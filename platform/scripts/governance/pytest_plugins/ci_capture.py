"""Write the real post-deselection collection for the CI containment audit."""
import json
import os
from pathlib import Path


def pytest_collection_finish(session):
    Path(os.environ['KY_COLLECTION_OUT']).write_text(json.dumps([item.nodeid for item in session.items]))
