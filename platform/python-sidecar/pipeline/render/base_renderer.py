"""
BaseRenderer — Jinja2 environment + no-narration linter + anchor helpers.
"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from datetime import datetime, timezone
from typing import Optional
import re

# No-narration forbidden verb list (from INF8 / M4 decision)
FORBIDDEN_VERBS = [
    r'\bindicates?\b', r'\bsuggests?\b', r'\bimplies?\b',
    r'\bmeans?\s+that\b', r'\bdenotes?\b', r'\bshows?\b',
    r'\brepresents?\b', r'\bsignifies?\b', r'\bsymbolizes?\b',
]
FORBIDDEN_PATTERN = re.compile('|'.join(FORBIDDEN_VERBS), re.IGNORECASE)


class NarrationViolation(Exception):
    """Raised when rendered output contains forbidden narration verbs."""
    pass


def lint_narration(text: str, section: str = 'unknown') -> None:
    """Scan text for forbidden narrative verbs. Raises NarrationViolation if found."""
    matches = FORBIDDEN_PATTERN.findall(text)
    if matches:
        raise NarrationViolation(
            f"No-narration violation in section '{section}': found {set(matches)}"
        )


def anchor_id(section_title: str) -> str:
    """Convert section title to GitHub-flavored markdown anchor ID."""
    # e.g. "§ Planetary Positions" → "planetary-positions"
    slug = re.sub(r'[^a-z0-9\s-]', '', section_title.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug


def frontmatter(
    chart_id: str,
    ayanamsha_id: str,
    engine_version: str,
    build_id: str,
    rendered_at: Optional[datetime] = None,
) -> str:
    """Generate YAML frontmatter block for FORENSIC.md."""
    ts = (rendered_at or datetime.now(timezone.utc)).isoformat()
    return f"""---
chart_id: {chart_id}
ayanamsha_id: {ayanamsha_id}
engine_version: {engine_version}
build_id: {build_id}
rendered_at: {ts}
document_type: forensic_render
no_narration: true
b10_compliant: true
---

"""


class ForensicRenderer:
    """
    Renders FORENSIC.md from chart_output dict.
    Sections rendered by sub-renderers registered in SECTION_REGISTRY.
    All output passes through narration linter before emit.
    """

    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path(__file__).parent / 'templates'
        self.template_dir.mkdir(exist_ok=True)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            undefined=StrictUndefined,
            autoescape=False,
        )
        self.sections: list[tuple[str, callable]] = []

    def register_section(self, title: str, renderer_fn: callable) -> None:
        """Register a section renderer. renderer_fn(chart_output) -> str."""
        self.sections.append((title, renderer_fn))

    def render(
        self,
        chart_output: dict,
        chart_id: str,
        ayanamsha_id: str,
        engine_version: str = 'pyjhora/1.0.0',
        build_id: str = 'unknown',
    ) -> str:
        """Render full FORENSIC.md. Returns complete markdown string."""
        parts = [frontmatter(chart_id, ayanamsha_id, engine_version, build_id)]

        # Title
        parts.append(f"# FORENSIC Chart — {ayanamsha_id.replace('_', ' ').title()} Ayanamsha\n\n")

        # Table of contents placeholder
        parts.append("## Table of Contents\n\n")
        for title, _ in self.sections:
            aid = anchor_id(title)
            parts.append(f"- [{title}](#{aid})\n")
        parts.append("\n---\n\n")

        # Render each section
        for title, renderer_fn in self.sections:
            try:
                section_text = renderer_fn(chart_output)
                lint_narration(section_text, title)  # enforce no-narration

                aid = anchor_id(title)
                parts.append(f'## {title} {{#{aid}}}\n\n')
                parts.append(section_text)
                parts.append("\n\n---\n\n")
            except NarrationViolation:
                raise
            except Exception as e:
                # Section render failure → placeholder (build continues)
                parts.append(f"## {title}\n\n_[Render error: {type(e).__name__}: {e}]_\n\n---\n\n")

        return ''.join(parts)
