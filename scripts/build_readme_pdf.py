"""Generate a professional, styled PDF of README.md using Playwright."""

import re
import sys
from pathlib import Path
import markdown
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
README_PATH = ROOT / "README.md"
OUTPUT_PATHS = [
    ROOT / "README.pdf",
    Path(r"C:\Users\Shaunak Rane\Desktop\PortiQ_Submission\README.pdf"),
    Path(r"C:\Users\Shaunak Rane\Desktop\PortiQ_README.pdf"),
]

def make_html(md_text: str) -> str:
    # Transform mermaid code blocks to <pre class="mermaid">
    md_transformed = re.sub(
        r"```mermaid\s*\n(.*?)\n```",
        r'<pre class="mermaid">\1</pre>',
        md_text,
        flags=re.DOTALL,
    )
    
    body = markdown.markdown(
        md_transformed,
        extensions=["tables", "fenced_code", "toc"],
    )
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PortiQ — Portfolio Analytics AI Agent</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'neutral',
      flowchart: {{ useMaxWidth: false, htmlLabels: true }}
    }});
  </script>
  <style>
    @page {{
      size: A4;
      margin: 18mm 16mm 18mm 16mm;
    }}
    
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      font-size: 10.5pt;
      line-height: 1.55;
      color: #1f2328;
      background: #ffffff;
      margin: 0;
      padding: 0;
    }}
    
    h1 {{
      font-size: 22pt;
      font-weight: 700;
      color: #0f172a;
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 8px;
      margin-top: 0;
      margin-bottom: 12px;
    }}
    
    h2 {{
      font-size: 15pt;
      font-weight: 650;
      color: #1e293b;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 6px;
      margin-top: 22px;
      margin-bottom: 10px;
      page-break-after: avoid;
    }}
    
    h3 {{
      font-size: 12.5pt;
      font-weight: 600;
      color: #334155;
      margin-top: 18px;
      margin-bottom: 8px;
      page-break-after: avoid;
    }}

    h4 {{
      font-size: 11pt;
      font-weight: 600;
      color: #475569;
      margin-top: 14px;
      margin-bottom: 6px;
      page-break-after: avoid;
    }}
    
    p {{
      margin-top: 0;
      margin-bottom: 10px;
    }}
    
    ul, ol {{
      margin-top: 0;
      margin-bottom: 12px;
      padding-left: 24px;
    }}
    
    li {{
      margin-bottom: 4px;
    }}
    
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 14px 0;
      font-size: 9.5pt;
      page-break-inside: avoid;
    }}
    
    th, td {{
      border: 1px solid #cbd5e1;
      padding: 7px 11px;
      text-align: left;
    }}
    
    th {{
      background: #f1f5f9;
      color: #0f172a;
      font-weight: 600;
    }}
    
    tr:nth-child(even) {{
      background: #f8fafc;
    }}
    
    code {{
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
      font-size: 9pt;
      background: #f1f5f9;
      color: #0f172a;
      padding: 2px 5px;
      border-radius: 4px;
      border: 1px solid #e2e8f0;
    }}
    
    pre {{
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
      font-size: 8.8pt;
      background: #0f172a;
      color: #f8fafc;
      padding: 12px 14px;
      border-radius: 6px;
      overflow-x: auto;
      margin: 12px 0;
      line-height: 1.45;
      page-break-inside: avoid;
    }}
    
    pre code {{
      background: transparent;
      color: inherit;
      padding: 0;
      border: none;
      font-size: inherit;
    }}
    
    pre.mermaid {{
      background: #ffffff;
      color: #1f2328;
      border: 1px solid #e2e8f0;
      padding: 16px;
      border-radius: 8px;
      display: flex;
      justify-content: center;
      margin: 16px 0;
      page-break-inside: avoid;
    }}
    
    pre.mermaid svg {{
      max-width: 100%;
      height: auto;
    }}
    
    hr {{
      border: none;
      border-top: 1px solid #e2e8f0;
      margin: 20px 0;
    }}
    
    a {{
      color: #0284c7;
      text-decoration: none;
    }}
    
    a:hover {{
      text-decoration: underline;
    }}
    
    blockquote {{
      margin: 12px 0;
      padding: 8px 14px;
      color: #475569;
      background: #f8fafc;
      border-left: 3px solid #0284c7;
      border-radius: 0 4px 4px 0;
    }}
  </style>
</head>
<body>
  {body}
</body>
</html>
"""
    return html


def build_pdf() -> None:
    if not README_PATH.exists():
        print(f"Error: {README_PATH} not found", file=sys.stderr)
        sys.exit(1)
        
    md_content = README_PATH.read_text(encoding="utf-8")
    html_content = make_html(md_content)
    
    print("Launching Chromium via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Load the HTML content and wait for network/mermaid rendering
        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(1500)  # Ensure Mermaid finishes layout
        
        footer_template = """
        <div style="font-family: -apple-system, sans-serif; font-size: 8pt; color: #94a3b8; width: 100%; display: flex; justify-content: space-between; padding: 0 16mm;">
          <span>PortiQ — Portfolio Analytics Agent</span>
          <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
        </div>
        """
        
        header_template = "<div></div>"
        
        for out_path in OUTPUT_PATHS:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            page.pdf(
                path=str(out_path),
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template=header_template,
                footer_template=footer_template,
                margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"}
            )
            print(f"Generated PDF: {out_path} ({out_path.stat().st_size:,} bytes)")
            
        browser.close()
    print("All PDFs generated successfully!")


if __name__ == "__main__":
    build_pdf()
