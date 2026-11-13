"""Project alias compatibility without importing provider SDKs or writer modules."""
import ast
import builtins
import io
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from pipeline.cloud_project import read_google_cloud_project


class Environment(dict):
    def __init__(self, values=()):
        super().__init__(values)
        self.reads = []

    def get(self, key, default=None):
        self.reads.append((key, default))
        return super().get(key, default)


class Clients:
    def __init__(self, failure=None):
        self.calls = []
        self.imports = []
        self.published = []
        self.failure = failure
        self.client = SimpleNamespace(
            topic_path=lambda project, topic: (project, topic),
            publish=self.publish,
        )
        self.genai = SimpleNamespace(Client=self.create)
        self.types = SimpleNamespace(HttpOptions=lambda **kwargs: kwargs)
        self.pubsub = SimpleNamespace(PublisherClient=self.create)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.failure is not None:
            raise self.failure
        return self.client

    def publish(self, *args, **kwargs):
        self.published.append((args, kwargs))
        return SimpleNamespace(add_done_callback=lambda callback: None)

    def importer(self, name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'google':
            self.imports.append(name)
            return SimpleNamespace(genai=self.genai)
        if name == 'google.genai':
            self.imports.append(name)
            return SimpleNamespace(types=self.types)
        if name == 'google.cloud':
            self.imports.append(name)
            return SimpleNamespace(pubsub_v1=self.pubsub)
        if name.startswith('google'):
            raise AssertionError('unexpected_provider_import')
        return builtins.__import__(name, globals, locals, fromlist, level)


def load_reader(sidecar, relative, env, clients, reader=None):
    path = Path(sidecar) / relative
    tree = ast.parse(path.read_bytes(), filename=str(path))
    scope = {
        '__name__': 'inert_reader',
        '__builtins__': dict(vars(builtins), __import__=clients.importer, print=lambda *args, **kwargs: None),
        'os': SimpleNamespace(environ=env, getpid=lambda: 123),
        'sys': SimpleNamespace(stdout=io.StringIO(), stderr=io.StringIO()),
        'json': json,
        'logging': SimpleNamespace(getLogger=lambda name: SimpleNamespace(
            info=lambda *args, **kwargs: None,
            warning=lambda *args, **kwargs: None,
            error=lambda *args, **kwargs: None,
        )),
        'socket': SimpleNamespace(gethostname=lambda: 'synthetic-host'),
        'uuid': SimpleNamespace(uuid4=lambda: 'synthetic-event'),
        'threading': threading,
        'logger': SimpleNamespace(info=lambda *args, **kwargs: None),
        '_genai_client': None,
        '_genai_client_lock': threading.Lock(),
        'read_google_cloud_project': reader,
    }
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    if relative.endswith('events.py'):
        nodes = [n for n in tree.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
    else:
        wanted = {'GCP_PROJECT', 'VERTEX_LOCATION', 'EMBED_MODEL', 'EMBED_HTTP_TIMEOUT_MS'}
        nodes = []
        for node in tree.body:
            targets = [n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)]
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and set(targets) & wanted:
                nodes.append(node)
            elif isinstance(node, ast.FunctionDef) and node.name == '_get_genai_client':
                nodes.append(node)
    selected = ast.fix_missing_locations(ast.Module(body=[future, *nodes], type_ignores=[]))
    exec(compile(selected, str(path), 'exec'), scope)
    return scope


SIDECAR = Path(__file__).resolve().parents[1]
WRITERS = [
    "pipeline/orchestrator/writers/bg_texts.py",
    "pipeline/orchestrator/writers/bo_samskara.py",
]


@pytest.mark.parametrize("values,default,expected", [
    ({}, None, None),
    ({}, "caller-default", "caller-default"),
    ({"GCP_PROJECT": "legacy"}, "caller-default", "legacy"),
    ({"GCP_PROJECT": ""}, "caller-default", ""),
    ({"GCP_PROJECT": " "}, "caller-default", " "),
    ({"GOOGLE_CLOUD_PROJECT": "canonical"}, "caller-default", "canonical"),
    ({"GOOGLE_CLOUD_PROJECT": ""}, "caller-default", ""),
    ({"GOOGLE_CLOUD_PROJECT": " "}, "caller-default", " "),
    ({"GCP_PROJECT": "legacy", "GOOGLE_CLOUD_PROJECT": "canonical"}, None, "legacy"),
    ({"GCP_PROJECT": "", "GOOGLE_CLOUD_PROJECT": "canonical"}, None, ""),
    ({"GCP_PROJECT": None, "GOOGLE_CLOUD_PROJECT": "canonical"}, None, "canonical"),
    ({"GCP_PROJECT": None, "GOOGLE_CLOUD_PROJECT": ""}, None, ""),
    ({"GCP_PROJECT": None}, "caller-default", "caller-default"),
    ({"GCP_PROJECT": "None"}, None, "None"),
])
def test_alias_precedence_and_caller_default(values, default, expected):
    env = Environment(values)
    assert read_google_cloud_project(env, default) == expected
    expected_keys = ["GCP_PROJECT"]
    if values.get("GCP_PROJECT") is None:
        expected_keys.append("GOOGLE_CLOUD_PROJECT")
    assert [key for key, _ in env.reads] == expected_keys


@pytest.mark.parametrize("path", WRITERS)
@pytest.mark.parametrize("values,expected", [
    ({}, "madhav-astrology"),
    ({"GOOGLE_CLOUD_PROJECT": "canonical"}, "canonical"),
    ({"GCP_PROJECT": "legacy", "GOOGLE_CLOUD_PROJECT": "canonical"}, "legacy"),
    ({"GCP_PROJECT": "", "GOOGLE_CLOUD_PROJECT": "canonical"}, ""),
])
def test_writer_binding_is_captured_before_lazy_single_client(path, values, expected):
    env = Environment(values)
    clients = Clients()
    scope = load_reader(SIDECAR, path, env, clients, read_google_cloud_project)
    assert clients.calls == clients.imports == []
    assert scope["GCP_PROJECT"] == expected
    env["GCP_PROJECT"] = "rebound-after-module-load"
    first = scope["_get_genai_client"]()
    second = scope["_get_genai_client"]()
    assert first is second
    assert len(clients.calls) == 1
    assert clients.calls[0]["project"] == expected
    assert clients.calls[0]["vertexai"] is True


@pytest.mark.parametrize("path", WRITERS)
def test_writer_client_failure_preserves_exception_and_uncached_state(path):
    error = RuntimeError("synthetic-client-failure")
    clients = Clients(failure=error)
    scope = load_reader(SIDECAR, path, Environment(), clients, read_google_cloud_project)
    with pytest.raises(RuntimeError) as caught:
        scope["_get_genai_client"]()
    assert caught.value is error
    assert scope["_genai_client"] is None
    assert len(clients.calls) == 1


@pytest.mark.parametrize("path", WRITERS)
def test_writer_provider_import_failure_preserves_exception(path):
    error = ModuleNotFoundError("synthetic-sdk-unavailable")
    clients = Clients()
    original_import = clients.importer

    def unavailable(name, *args, **kwargs):
        if name.startswith("google"):
            raise error
        return original_import(name, *args, **kwargs)

    clients.importer = unavailable
    scope = load_reader(SIDECAR, path, Environment(), clients, read_google_cloud_project)
    with pytest.raises(ModuleNotFoundError) as caught:
        scope["_get_genai_client"]()
    assert caught.value is error
    assert clients.calls == []


@pytest.mark.parametrize("values,expected_clients", [
    ({"GOOGLE_CLOUD_PROJECT": "canonical"}, 0),
    ({"GOOGLE_CLOUD_PROJECT": "canonical", "PUBSUB_DISABLED": "1", "PUBSUB_TOPIC": "synthetic"}, 0),
    ({"GOOGLE_CLOUD_PROJECT": "canonical", "PUBSUB_DISABLED": "0", "PUBSUB_TOPIC": "synthetic"}, 0),
    ({"GOOGLE_CLOUD_PROJECT": "canonical", "PUBSUB_DISABLED": "false", "PUBSUB_TOPIC": "synthetic"}, 0),
    ({"GOOGLE_CLOUD_PROJECT": "canonical", "PUBSUB_DISABLED": ""}, 0),
    ({"GOOGLE_CLOUD_PROJECT": "canonical", "PUBSUB_TOPIC": "synthetic"}, 1),
    ({"GOOGLE_CLOUD_PROJECT": "canonical", "PUBSUB_DISABLED": "", "PUBSUB_TOPIC": "synthetic"}, 1),
])
def test_original_pubsub_activation_and_topic_guards(values, expected_clients):
    env = Environment(values)
    clients = Clients()
    scope = load_reader(SIDECAR, "pipeline/orchestrator/events.py", env, clients, read_google_cloud_project)
    assert clients.calls == clients.imports == []
    scope["emit_event"]({"type": "synthetic-project-check"})
    assert len(clients.calls) == len(clients.published) == expected_clients
    if expected_clients == 0:
        assert clients.imports == []
        assert all(key not in {"GCP_PROJECT", "GOOGLE_CLOUD_PROJECT"} for key, _ in env.reads)
    else:
        assert clients.published[0][0][0][0] == "canonical"


@pytest.mark.parametrize("values,expected", [
    ({"GCP_PROJECT": "later-legacy", "GOOGLE_CLOUD_PROJECT": "canonical"}, "later-legacy"),
    ({"GCP_PROJECT": "", "GOOGLE_CLOUD_PROJECT": "canonical"}, ""),
    ({"GOOGLE_CLOUD_PROJECT": "later-canonical"}, "later-canonical"),
    ({}, "madhav-astrology"),
])
def test_pubsub_project_is_read_at_the_original_publish_point(values, expected):
    env = Environment({"GCP_PROJECT": "before-load"})
    clients = Clients()
    scope = load_reader(SIDECAR, "pipeline/orchestrator/events.py", env, clients, read_google_cloud_project)
    assert clients.calls == clients.imports == []
    assert env.reads == []
    env.clear()
    env.update(values, PUBSUB_TOPIC="synthetic")
    scope["emit_event"]({"type": "synthetic-project-check"})
    assert clients.published[0][0][0] == (expected, "synthetic")


def test_pubsub_client_failure_remains_nonfatal():
    clients = Clients(failure=RuntimeError("synthetic-client-failure"))
    scope = load_reader(SIDECAR, "pipeline/orchestrator/events.py",
                        Environment({"GOOGLE_CLOUD_PROJECT": "canonical", "PUBSUB_TOPIC": "synthetic"}),
                        clients, read_google_cloud_project)
    assert scope["emit_event"]({"type": "synthetic-project-check"}) is None
    assert len(clients.calls) == 1
    assert clients.published == []


def test_existing_image_copies_include_the_pure_pipeline_helper():
    sidecar = (SIDECAR / "Dockerfile").read_text()
    pipeline = (SIDECAR / "Dockerfile.pipeline").read_text()
    assert any(line.startswith("COPY python-sidecar/ ") for line in sidecar.splitlines())
    assert any(line.startswith("COPY platform/python-sidecar/pipeline/ ") for line in pipeline.splitlines())
