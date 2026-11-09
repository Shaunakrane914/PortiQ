"""Convert README.md into a beautifully formatted Microsoft Word (.docx) document."""

import re
import sys
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

ROOT = Path(__file__).resolve().parent.parent
README_PATH = ROOT / "README.md"
OUTPUT_PATHS = [
    ROOT / "README.docx",
    Path(r"C:\Users\Shaunak Rane\Desktop\PortiQ_Submission\README.docx"),
    Path(r"C:\Users\Shaunak Rane\Desktop\PortiQ_README.docx"),
]

COLOR_PRIMARY = RGBColor(15, 23, 42)      # Slate 900
COLOR_SECONDARY = RGBColor(30, 41, 59)   # Slate 800
COLOR_MUTED = RGBColor(71, 85, 105)      # Slate 600
COLOR_BLUE = RGBColor(2, 132, 199)       # Sky 600
COLOR_CODE = RGBColor(15, 23, 42)


def set_cell_background(cell, fill_hex: str) -> None:
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def add_formatted_text(paragraph, text: str) -> None:
    """Parse inline markdown (bold, italic, code, links) and append runs."""
    # Pattern to match: `code`, **bold**, *italic*, [text](url)
    pattern = re.compile(r'(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))')
    tokens = pattern.split(text)
    for token in tokens:
        if not token:
            continue
        if token.startswith("`") and token.endswith("`"):
            run = paragraph.add_run(token[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
            run.font.color.rgb = COLOR_CODE
        elif token.startswith("**") and token.endswith("**"):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        elif token.startswith("*") and token.endswith("*"):
            run = paragraph.add_run(token[1:-1])
            run.italic = True
        elif token.startswith("[") and "](" in token and token.endswith(")"):
            m = re.match(r'\[([^\]]+)\]\(([^)]+)\)', token)
            if m:
                label, url = m.groups()
                run = paragraph.add_run(label)
                run.font.color.rgb = COLOR_BLUE
                run.underline = True
            else:
                paragraph.add_run(token)
        else:
            paragraph.add_run(token)


def create_docx() -> None:
    if not README_PATH.exists():
        print(f"Error: {README_PATH} not found", file=sys.stderr)
        sys.exit(1)

    content = README_PATH.read_text(encoding="utf-8")
    lines = content.splitlines()

    doc = docx.Document()
    
    # Configure page geometry (A4, 1-inch margins)
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Configure Normal style
    style = doc.styles["Normal"]
    style.font.name = "Segoe UI"
    style.font.size = Pt(10.5)
    style.font.color.rgb = COLOR_SECONDARY
    style.paragraph_format.line_spacing = 1.2
    style.paragraph_format.space_after = Pt(6)

    i = 0
    in_code_block = False
    code_block_lines = []
    code_lang = ""

    while i < len(lines):
        line = lines[i]

        # Handle code blocks
        if line.startswith("```"):
            if in_code_block:
                in_code_block = False
                block_text = "\n".join(code_block_lines)
                
                # Render code block in a shaded container table
                tbl = doc.add_table(rows=1, cols=1)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = tbl.cell(0, 0)
                set_cell_background(cell, "0F172A")  # Dark slate
                set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
                cell.width = Inches(6.67)
                
                p = cell.paragraphs[0]
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.15
                run = p.add_run(block_text)
                run.font.name = "Consolas"
                run.font.size = Pt(9.0)
                run.font.color.rgb = RGBColor(241, 245, 249)  # Light slate
                
                doc.add_paragraph()  # Spacer
                code_block_lines = []
            else:
                in_code_block = True
                code_lang = line[3:].strip()
                code_block_lines = []
            i += 1
            continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Empty line
        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if stripped in {"---", "***", "___"}:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(8)
            run = p.add_run("―" * 55)
            run.font.color.rgb = RGBColor(226, 232, 240)
            i += 1
            continue

        # Headings
        if stripped.startswith("# ") and not stripped.startswith("## "):
            h = doc.add_heading(level=1)
            h.paragraph_format.space_before = Pt(0)
            h.paragraph_format.space_after = Pt(8)
            run = h.add_run(stripped[2:])
            run.font.name = "Segoe UI"
            run.font.size = Pt(22)
            run.font.color.rgb = COLOR_PRIMARY
            run.bold = True
            i += 1
            continue

        if stripped.startswith("## "):
            h = doc.add_heading(level=2)
            h.paragraph_format.space_before = Pt(16)
            h.paragraph_format.space_after = Pt(6)
            run = h.add_run(stripped[3:])
            run.font.name = "Segoe UI"
            run.font.size = Pt(15)
            run.font.color.rgb = COLOR_PRIMARY
            run.bold = True
            i += 1
            continue

        if stripped.startswith("### "):
            h = doc.add_heading(level=3)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(4)
            run = h.add_run(stripped[4:])
            run.font.name = "Segoe UI"
            run.font.size = Pt(12.5)
            run.font.color.rgb = COLOR_SECONDARY
            run.bold = True
            i += 1
            continue

        if stripped.startswith("#### "):
            h = doc.add_heading(level=4)
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(3)
            run = h.add_run(stripped[5:])
            run.font.name = "Segoe UI"
            run.font.size = Pt(11)
            run.font.color.rgb = COLOR_MUTED
            run.bold = True
            i += 1
            continue

        # Table detection
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            
            if len(table_lines) >= 2 and re.match(r"^\|(\s*:?-+:?\s*\|)+$", table_lines[1]):
                headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
                rows = []
                for tline in table_lines[2:]:
                    rows.append([c.strip() for c in tline.strip("|").split("|")])
                
                tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                tbl.style = "Table Grid"

                # Header row
                hdr_cells = tbl.rows[0].cells
                for col_idx, h_text in enumerate(headers):
                    cell = hdr_cells[col_idx]
                    set_cell_background(cell, "F1F5F9")
                    set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.space_before = Pt(0)
                    run = p.add_run(h_text)
                    run.bold = True
                    run.font.size = Pt(9.5)
                    run.font.color.rgb = COLOR_PRIMARY

                # Data rows
                for r_idx, row_data in enumerate(rows):
                    row_cells = tbl.rows[r_idx + 1].cells
                    fill_color = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
                    for col_idx in range(len(headers)):
                        if col_idx < len(row_data):
                            cell = row_cells[col_idx]
                            set_cell_background(cell, fill_color)
                            set_cell_margins(cell, top=70, bottom=70, left=120, right=120)
                            p = cell.paragraphs[0]
                            p.paragraph_format.space_after = Pt(0)
                            p.paragraph_format.space_before = Pt(0)
                            add_formatted_text(p, row_data[col_idx])
                            for r in p.runs:
                                r.font.size = Pt(9.0)

                doc.add_paragraph()  # Spacer after table
                continue

        # Bullet list
        if stripped.startswith("- ") or stripped.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_text(p, stripped[2:])
            i += 1
            continue

        # Numbered list
        m = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if m:
            num, item_text = m.groups()
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_text(p, item_text)
            i += 1
            continue

        # Regular paragraph
        p = doc.add_paragraph()
        add_formatted_text(p, stripped)
        i += 1

    # Save to all target paths
    for out_path in OUTPUT_PATHS:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(out_path))
        print(f"Generated DOCX: {out_path} ({out_path.stat().st_size:,} bytes)")

    print("All DOCX files generated successfully!")


if __name__ == "__main__":
    create_docx()
