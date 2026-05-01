"""Build gcp-setup-walkthrough.pdf from gcp-setup-walkthrough.md.

Run with:
    uv run --with markdown --with weasyprint python docs/build_walkthrough_pdf.py

Uses an ephemeral virtualenv so the project's runtime dependencies are
untouched.
"""

from pathlib import Path

import markdown
from weasyprint import CSS, HTML

HERE = Path(__file__).parent
SRC = HERE / "gcp-setup-walkthrough.md"
OUT = HERE / "gcp-setup-walkthrough.pdf"

CSS_STYLES = """
@page {
  size: Letter;
  margin: 0.75in 0.8in;
  @bottom-right {
    content: counter(page) " / " counter(pages);
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    font-size: 9pt;
    color: #888;
  }
  @bottom-left {
    content: "Treepolitics GCP Setup — Walkthrough";
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    font-size: 9pt;
    color: #888;
  }
}

html { font-size: 11pt; }

body {
  font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
  color: #1f2937;
  line-height: 1.5;
}

h1 {
  font-size: 22pt;
  color: #0f172a;
  border-bottom: 3px solid #2563eb;
  padding-bottom: 0.3em;
  margin-top: 0;
}

h2 {
  font-size: 15pt;
  color: #0f172a;
  margin-top: 1.6em;
  padding: 0.35em 0.6em;
  background: #eff6ff;
  border-left: 4px solid #2563eb;
  page-break-after: avoid;
}

h3 {
  font-size: 12pt;
  color: #1e3a8a;
  margin-top: 1.3em;
  page-break-after: avoid;
}

p { margin: 0.55em 0; }

ul, ol { margin: 0.5em 0 0.8em 0; padding-left: 1.5em; }
li { margin: 0.25em 0; }
li > ul, li > ol { margin: 0.2em 0; }

code {
  font-family: "SF Mono", Menlo, Consolas, monospace;
  background: #f1f5f9;
  padding: 0.08em 0.35em;
  border-radius: 3px;
  font-size: 0.92em;
  color: #0f172a;
}

strong { color: #0f172a; }

hr {
  border: none;
  border-top: 1px dashed #cbd5e1;
  margin: 1.5em 0;
  page-break-after: always;
}

/* Role tags: [WILL] and [AMR] */
.role-will, .role-amr, .role-both {
  display: inline-block;
  font-family: "SF Mono", Menlo, Consolas, monospace;
  font-size: 0.82em;
  font-weight: 700;
  padding: 0.05em 0.45em;
  border-radius: 3px;
  margin-right: 0.15em;
  vertical-align: baseline;
}
.role-will { background: #dcfce7; color: #14532d; border: 1px solid #86efac; }
.role-amr  { background: #dbeafe; color: #1e3a8a; border: 1px solid #93c5fd; }
.role-both { background: #fef3c7; color: #78350f; border: 1px solid #fcd34d; }

/* Markdown checkboxes */
ul.task-list { list-style: none; padding-left: 1.2em; }
ul.task-list li { position: relative; padding-left: 0.3em; }
li input[type="checkbox"] {
  appearance: none;
  -webkit-appearance: none;
  width: 0.95em;
  height: 0.95em;
  border: 1.5px solid #64748b;
  border-radius: 2px;
  margin-right: 0.4em;
  vertical-align: -0.15em;
}

blockquote {
  border-left: 4px solid #f59e0b;
  background: #fffbeb;
  padding: 0.6em 1em;
  margin: 1em 0;
  color: #78350f;
}

/* Keep headings and their first paragraph together where possible */
h2 + p, h2 + ul, h3 + p, h3 + ul { page-break-before: avoid; }
"""


def transform_role_tags(html: str) -> str:
    """Wrap [WILL] / [AMR] / [BOTH] markers in styled spans."""
    replacements = {
        "[WILL]": '<span class="role-will">WILL</span>',
        "[AMR]": '<span class="role-amr">AMR</span>',
        "[BOTH]": '<span class="role-both">BOTH</span>',
    }
    for marker, span in replacements.items():
        html = html.replace(marker, span)
    return html


def main() -> None:
    md_source = SRC.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        md_source,
        extensions=["extra", "sane_lists", "toc"],
    )
    # markdown's default doesn't render GFM-style checkboxes, but we can
    # transform "[ ]" at the start of list items into input elements.
    html_body = html_body.replace("[ ] ", '<input type="checkbox" disabled> ')
    html_body = transform_role_tags(html_body)

    full_html = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Treepolitics GCP Setup — Walkthrough</title></head>
<body>
{html_body}
</body>
</html>"""

    HTML(string=full_html).write_pdf(
        target=str(OUT),
        stylesheets=[CSS(string=CSS_STYLES)],
    )
    print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
