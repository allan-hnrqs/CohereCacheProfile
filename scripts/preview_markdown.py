from __future__ import annotations

import argparse
import tempfile
import webbrowser
from pathlib import Path


def render_markdown(text: str) -> str:
    try:
        from markdown_it import MarkdownIt

        return MarkdownIt("commonmark", {"html": True}).enable("table").render(text)
    except ImportError:
        try:
            import mistune

            return mistune.html(text)
        except ImportError as exc:
            raise SystemExit(
                "No Markdown renderer found. Install `markdown-it-py` or `mistune`."
            ) from exc


def build_document(title: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #ffffff;
      --fg: #1f2328;
      --muted: #59636e;
      --border: #d0d7de;
      --code-bg: #f6f8fa;
      --table-stripe: #f6f8fa;
      --link: #0969da;
    }}

    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #0d1117;
        --fg: #e6edf3;
        --muted: #8b949e;
        --border: #30363d;
        --code-bg: #161b22;
        --table-stripe: #161b22;
        --link: #58a6ff;
      }}
    }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--fg);
      font: 16px/1.6 Georgia, "Times New Roman", serif;
    }}

    main {{
      max-width: 860px;
      margin: 0 auto;
      padding: 40px 24px 64px;
    }}

    h1, h2, h3, h4, h5, h6 {{
      margin: 1.5em 0 0.45em;
      line-height: 1.25;
      font-family: "Segoe UI", system-ui, sans-serif;
    }}

    p, ul, ol, table, pre, blockquote {{
      margin: 0 0 1em;
    }}

    a {{
      color: var(--link);
      text-decoration: none;
    }}

    a:hover {{
      text-decoration: underline;
    }}

    code {{
      background: var(--code-bg);
      padding: 0.15em 0.35em;
      border-radius: 6px;
      font-family: Consolas, "Courier New", monospace;
      font-size: 0.92em;
    }}

    pre {{
      background: var(--code-bg);
      padding: 16px;
      border-radius: 10px;
      overflow-x: auto;
    }}

    pre code {{
      padding: 0;
      background: transparent;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.96rem;
    }}

    th, td {{
      border: 1px solid var(--border);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
    }}

    tbody tr:nth-child(even) {{
      background: var(--table-stripe);
    }}

    blockquote {{
      border-left: 4px solid var(--border);
      margin-left: 0;
      padding-left: 16px;
      color: var(--muted);
    }}

    img {{
      max-width: 100%;
      height: auto;
    }}
  </style>
</head>
<body>
  <main>
{body_html}
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a Markdown file to standalone HTML for local preview."
    )
    parser.add_argument("markdown_file", help="Path to the Markdown file to preview")
    parser.add_argument(
        "--output",
        help="Optional output HTML path. Defaults to the system temp directory.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the rendered file in your default browser.",
    )
    args = parser.parse_args()

    source = Path(args.markdown_file).resolve()
    if not source.exists():
        raise SystemExit(f"Markdown file not found: {source}")

    body_html = render_markdown(source.read_text(encoding="utf-8"))
    if args.output:
        output = Path(args.output).resolve()
    else:
        output = Path(tempfile.gettempdir()) / f"{source.stem}.preview.html"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_document(source.name, body_html), encoding="utf-8")

    print(output)
    if args.open:
        webbrowser.open(output.as_uri())


if __name__ == "__main__":
    main()
