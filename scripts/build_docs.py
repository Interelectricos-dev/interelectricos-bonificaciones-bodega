import os
import re
from PIL import Image
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

# --- Helper Formatting Functions ---

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return RGBColor(*(int(hex_str[i:i+2], 16) for i in (0, 2, 4)))

def set_cell_shading(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    for child in list(tcPr):
        if child.tag.endswith('shd'):
            tcPr.remove(child)
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex.lstrip("#")}" w:val="clear"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
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

def set_table_borders(table, color="CBD5E1", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    tblBorders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(tblBorders)

def set_callout_borders(cell, color="0284C7", sz="36"):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

def set_code_box_borders(cell, color="E2E8F0", sz="4"):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

def add_page_number_field(paragraph):
    fldSimple = parse_xml(
        f'<w:fldSimple {nsdecls("w")} w:instr="PAGE">'
        f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="17"/><w:color w:val="64748B"/></w:rPr><w:t>1</w:t></w:r>'
        f'</w:fldSimple>'
    )
    paragraph._p.append(fldSimple)

def add_formatted_runs(paragraph, text, base_font="Calibri", base_size=10.5, base_color="1F2937", is_bold=False, is_italic=False):
    # Clean markdown links [label](url) -> label
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Clean non-breaking spaces or double spaces
    text = text.replace('&nbsp;', ' ')
    
    # Parses inline markdown: **bold**, *italic*, `code`, and plain text
    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)', text)
    for token in tokens:
        if not token:
            continue
        run = paragraph.add_run()
        run.font.name = base_font
        run.font.size = Pt(base_size)
        run.font.color.rgb = hex_to_rgb(base_color)
        run.bold = is_bold
        run.italic = is_italic

        if token.startswith('**') and token.endswith('**') and len(token) >= 4:
            run.text = token[2:-2]
            run.bold = True
        elif token.startswith('*') and token.endswith('*') and len(token) >= 2:
            run.text = token[1:-1]
            run.italic = True
        elif token.startswith('`') and token.endswith('`') and len(token) >= 2:
            run.text = token[1:-1]
            run.font.name = 'Consolas'
            run.font.size = Pt(base_size * 0.9)
            run.font.color.rgb = hex_to_rgb("0F172A")
        else:
            run.text = token

# --- Document Builder Class ---

class MarkdownDocxBuilder:
    def __init__(self, doc_title, doc_subtitle, metadata_dict, base_dir="docs"):
        self.doc = docx.Document()
        self.doc_title = doc_title
        self.doc_subtitle = doc_subtitle
        self.metadata = metadata_dict
        self.base_dir = base_dir
        self.h1_count = 0
        self.setup_page_properties()
        self.setup_styles()

    def setup_page_properties(self):
        # Letter size, 1 inch margins
        for sec in self.doc.sections:
            sec.page_width = Inches(8.5)
            sec.page_height = Inches(11.0)
            sec.top_margin = Inches(1.0)
            sec.bottom_margin = Inches(1.0)
            sec.left_margin = Inches(1.0)
            sec.right_margin = Inches(1.0)
            sec.different_first_page_header_footer = True
        try:
            self.doc.settings.element.append(parse_xml(f'<w:updateFields {nsdecls("w")} w:val="true"/>'))
        except Exception:
            pass

    def setup_styles(self):
        styles = self.doc.styles

        # Normal
        if 'Normal' in styles:
            s_norm = styles['Normal']
            s_norm.font.name = 'Calibri'
            s_norm.font.size = Pt(10.5)
            s_norm.font.color.rgb = hex_to_rgb('1F2937')
            s_norm.paragraph_format.line_spacing = 1.15
            s_norm.paragraph_format.space_after = Pt(4)

        # Title
        if 'Title' in styles:
            s_title = styles['Title']
            s_title.font.name = 'Calibri'
            s_title.font.size = Pt(24.0)
            s_title.font.bold = True
            s_title.font.color.rgb = hex_to_rgb('1E293B')

        # Subtitle
        if 'Subtitle' in styles:
            s_sub = styles['Subtitle']
            s_sub.font.name = 'Calibri'
            s_sub.font.size = Pt(12.0)
            s_sub.font.italic = True
            s_sub.font.color.rgb = hex_to_rgb('475569')

        # Heading 1
        if 'Heading 1' in styles:
            s_h1 = styles['Heading 1']
            s_h1.font.name = 'Calibri'
            s_h1.font.size = Pt(15.0)
            s_h1.font.bold = True
            s_h1.font.color.rgb = hex_to_rgb('1E293B')
            s_h1.paragraph_format.space_before = Pt(16)
            s_h1.paragraph_format.space_after = Pt(6)
            s_h1.paragraph_format.keep_with_next = True

        # Heading 2
        if 'Heading 2' in styles:
            s_h2 = styles['Heading 2']
            s_h2.font.name = 'Calibri'
            s_h2.font.size = Pt(12.5)
            s_h2.font.bold = True
            s_h2.font.color.rgb = hex_to_rgb('334155')
            s_h2.paragraph_format.space_before = Pt(12)
            s_h2.paragraph_format.space_after = Pt(4)
            s_h2.paragraph_format.keep_with_next = True

        # Heading 3
        if 'Heading 3' in styles:
            s_h3 = styles['Heading 3']
            s_h3.font.name = 'Calibri'
            s_h3.font.size = Pt(11.5)
            s_h3.font.bold = True
            s_h3.font.color.rgb = hex_to_rgb('374151')
            s_h3.paragraph_format.space_before = Pt(10)
            s_h3.paragraph_format.space_after = Pt(3)
            s_h3.paragraph_format.keep_with_next = True

        # Heading 4
        if 'Heading 4' in styles:
            s_h4 = styles['Heading 4']
            s_h4.font.name = 'Calibri'
            s_h4.font.size = Pt(10.5)
            s_h4.font.bold = True
            s_h4.font.color.rgb = hex_to_rgb('475569')
            s_h4.paragraph_format.space_before = Pt(8)
            s_h4.paragraph_format.space_after = Pt(2)
            s_h4.paragraph_format.keep_with_next = True

        # List Bullet
        if 'List Bullet' in styles:
            s_bul = styles['List Bullet']
            s_bul.font.name = 'Calibri'
            s_bul.font.size = Pt(10.5)
            s_bul.font.color.rgb = hex_to_rgb('1F2937')
            s_bul.paragraph_format.space_after = Pt(2.5)
            s_bul.paragraph_format.line_spacing = 1.15

        # TOC Heading (excluded from TOC hierarchy by Word and WPS Office)
        if 'TOC Heading' in styles:
            s_toch = styles['TOC Heading']
            s_toch.font.name = 'Calibri'
            s_toch.font.size = Pt(15.0)
            s_toch.font.bold = True
            s_toch.font.color.rgb = hex_to_rgb('1E293B')
            s_toch.paragraph_format.space_before = Pt(8)
            s_toch.paragraph_format.space_after = Pt(14)
            s_toch.paragraph_format.keep_with_next = True

    def build_cover_page(self):
        # Section 0 is the cover
        sec = self.doc.sections[0]
        
        # Company banner
        p_comp = self.doc.add_paragraph()
        p_comp.paragraph_format.space_before = Pt(8)
        p_comp.paragraph_format.space_after = Pt(2)
        r_comp = p_comp.add_run("INTERELÉCTRICOS GROUP SAS")
        r_comp.font.name = "Calibri"
        r_comp.font.size = Pt(11.0)
        r_comp.font.color.rgb = hex_to_rgb("334155")
        r_comp.bold = True

        p_subcomp = self.doc.add_paragraph()
        p_subcomp.paragraph_format.space_before = Pt(0)
        p_subcomp.paragraph_format.space_after = Pt(24)
        r_subcomp = p_subcomp.add_run("Sistema de Control, Liquidación y Auditoría de Bonificaciones en Bodega")
        r_subcomp.font.name = "Calibri"
        r_subcomp.font.size = Pt(9.5)
        r_subcomp.font.color.rgb = hex_to_rgb("64748B")

        # Spacing before title
        p_space = self.doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(28)
        p_space.paragraph_format.space_after = Pt(0)

        # Title
        p_title = self.doc.add_paragraph(style='Title')
        p_title.paragraph_format.space_before = Pt(0)
        p_title.paragraph_format.space_after = Pt(8)
        r_title = p_title.add_run(self.doc_title.upper())
        r_title.font.name = "Calibri"
        r_title.font.size = Pt(24.0)
        r_title.font.color.rgb = hex_to_rgb("1E293B")
        r_title.bold = True

        # Subtitle
        p_sub = self.doc.add_paragraph(style='Subtitle')
        p_sub.paragraph_format.space_before = Pt(0)
        p_sub.paragraph_format.space_after = Pt(28)
        r_sub = p_sub.add_run(self.doc_subtitle)
        r_sub.font.name = "Calibri"
        r_sub.font.size = Pt(12.0)
        r_sub.font.color.rgb = hex_to_rgb("475569")
        r_sub.italic = True

        # Spacing before metadata box
        p_space2 = self.doc.add_paragraph()
        p_space2.paragraph_format.space_before = Pt(36)
        p_space2.paragraph_format.space_after = Pt(0)

        # Metadata table (3 rows x 2 cols)
        items = list(self.metadata.items())
        table = self.doc.add_table(rows=3, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table, color="E2E8F0", sz="4", val="single")
        col_widths = [Inches(3.25), Inches(3.25)]

        for row_idx in range(3):
            for col_idx in range(2):
                item_idx = row_idx * 2 + col_idx
                cell = table.cell(row_idx, col_idx)
                cell.width = col_widths[col_idx]
                set_cell_shading(cell, "F8FAFC")
                set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
                if item_idx < len(items):
                    k, v = items[item_idx]
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(0)
                    r_k = p.add_run(f"{k}: ")
                    r_k.font.name = "Calibri"
                    r_k.font.size = Pt(9.0)
                    r_k.font.color.rgb = hex_to_rgb("1E293B")
                    r_k.bold = True
                    r_v = p.add_run(v)
                    r_v.font.name = "Calibri"
                    r_v.font.size = Pt(9.0)
                    r_v.font.color.rgb = hex_to_rgb("475569")

        # Bottom confidentiality note
        p_bottom = self.doc.add_paragraph()
        p_bottom.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_bottom.paragraph_format.space_before = Pt(64)
        p_bottom.paragraph_format.space_after = Pt(0)
        r_bot = p_bottom.add_run("Documento Oficial de Arquitectura Técnica y Configuración  •  Todos los derechos reservados")
        r_bot.font.name = "Calibri"
        r_bot.font.size = Pt(8.5)
        r_bot.font.color.rgb = hex_to_rgb("94A3B8")

        # Note: Section break in setup_content_section_headers automatically starts page 2
        pass

    def setup_content_section_headers(self, short_title):
        # Create a new section so header/footer only appears after cover
        sec = self.doc.add_section()
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)
        sec.different_first_page_header_footer = False

        # Header
        header = sec.header
        p_hdr = header.paragraphs[0]
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_hdr.paragraph_format.space_after = Pt(4)
        r_hdr = p_hdr.add_run(f"Intereléctricos — Sistema de Bonificaciones Bodega | {short_title}")
        r_hdr.font.name = "Calibri"
        r_hdr.font.size = Pt(8.5)
        r_hdr.font.color.rgb = hex_to_rgb("64748B")
        
        # Border bottom on header
        pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="4" w:space="4" w:color="CBD5E1"/></w:pBdr>')
        p_hdr._p.get_or_add_pPr().append(pBdr)

        # Footer
        footer = sec.footer
        p_ftr = footer.paragraphs[0]
        p_ftr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_ftr.paragraph_format.space_before = Pt(4)
        r_ftr_title = p_ftr.add_run(f"{short_title}  •  Página ")
        r_ftr_title.font.name = "Calibri"
        r_ftr_title.font.size = Pt(8.5)
        r_ftr_title.font.color.rgb = hex_to_rgb("64748B")
        add_page_number_field(p_ftr)

        pBdr_ftr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:top w:val="single" w:sz="4" w:space="4" w:color="CBD5E1"/></w:pBdr>')
        p_ftr._p.get_or_add_pPr().append(pBdr_ftr)

    def add_table_of_contents(self):
        p_toc_title = self.doc.add_paragraph(style='TOC Heading')
        p_toc_title.paragraph_format.space_before = Pt(8)
        p_toc_title.paragraph_format.space_after = Pt(14)
        p_toc_title.paragraph_format.keep_with_next = True
        r = p_toc_title.add_run("TABLA DE CONTENIDO")
        r.font.name = "Calibri"
        r.font.size = Pt(15.0)
        r.font.bold = True
        r.font.color.rgb = hex_to_rgb("1E293B")

        # Dynamic Word / WPS Office TOC Field
        # \o "1-3" captures Headings 1-3, \h generates clickable hyperlinks for PDF export, \u applies outline levels
        p_fld = self.doc.add_paragraph()
        p_fld.paragraph_format.space_before = Pt(0)
        p_fld.paragraph_format.space_after = Pt(8)
        fld_xml = (
            f'<w:fldSimple {nsdecls("w")} w:instr="TOC \\o &quot;1-3&quot; \\h \\z \\u">'
            f'<w:r>'
            f'<w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:color w:val="64748B"/><w:i/></w:rPr>'
            f'<w:t>[Haga clic derecho y elija \'Actualizar campos\', o use Referencias &gt; Tabla de contenido en WPS Office para generar los hipervínculos]</w:t>'
            f'</w:r>'
            f'</w:fldSimple>'
        )
        p_fld._p.append(parse_xml(fld_xml))

        # Page break after TOC so Section 1 begins cleanly on page 3
        self.doc.add_page_break()

    def add_heading_1(self, text):
        p = self.doc.add_paragraph(style='Heading 1')
        if self.h1_count > 0:
            p.paragraph_format.page_break_before = True
        self.h1_count += 1
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(15.0)
        r.font.color.rgb = hex_to_rgb("1E293B")
        r.bold = True

    def add_heading_2(self, text):
        p = self.doc.add_paragraph(style='Heading 2')
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(12.5)
        r.font.color.rgb = hex_to_rgb("334155")
        r.bold = True

    def add_heading_3(self, text):
        p = self.doc.add_paragraph(style='Heading 3')
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(11.5)
        r.font.color.rgb = hex_to_rgb("374151")
        r.bold = True

    def add_heading_4(self, text):
        p = self.doc.add_paragraph(style='Heading 4')
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(10.5)
        r.font.color.rgb = hex_to_rgb("475569")
        r.bold = True

    def add_body_paragraph(self, text):
        p = self.doc.add_paragraph(style='Normal')
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.15
        add_formatted_runs(p, text, base_font="Calibri", base_size=10.5, base_color="1F2937")

    def add_bullet_item(self, text, indent_level=0):
        p = self.doc.add_paragraph(style='List Bullet')
        p.paragraph_format.left_indent = Inches(0.25 * (indent_level + 1))
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2.5)
        p.paragraph_format.line_spacing = 1.15
        add_formatted_runs(p, text, base_font="Calibri", base_size=10.5, base_color="1F2937")

    def add_code_block(self, code_text):
        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        row = table.rows[0]
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        cell = row.cells[0]
        cell.width = Inches(6.5)
        set_cell_shading(cell, "F8FAFC")
        set_code_box_borders(cell, color="E2E8F0", sz="4")
        set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
        
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.1
        lines = code_text.strip().split('\n')
        for i, line in enumerate(lines):
            r = p.add_run(line)
            r.font.name = "Consolas"
            r.font.size = Pt(9.0)
            r.font.color.rgb = hex_to_rgb("0F172A")
            if i < len(lines) - 1:
                p.add_run('\n')

        # Small spacing after table
        p_sp = self.doc.add_paragraph()
        p_sp.paragraph_format.space_before = Pt(0)
        p_sp.paragraph_format.space_after = Pt(4)

    def add_callout(self, callout_text):
        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        row = table.rows[0]
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        cell = row.cells[0]
        cell.width = Inches(6.5)
        set_cell_shading(cell, "F0F9FF")
        set_callout_borders(cell, color="0284C7", sz="36")
        set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
        
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.15
        add_formatted_runs(p, callout_text, base_font="Calibri", base_size=10.0, base_color="1E293B")

        p_sp = self.doc.add_paragraph()
        p_sp.paragraph_format.space_before = Pt(0)
        p_sp.paragraph_format.space_after = Pt(4)

    def resolve_image_path(self, rel_path):
        candidates = [
            os.path.normpath(os.path.join(self.base_dir, rel_path)),
            os.path.normpath(os.path.join(self.base_dir, "..", rel_path)),
            os.path.normpath(rel_path),
            os.path.normpath(os.path.join(os.getcwd(), rel_path)),
            os.path.normpath(os.path.join(os.getcwd(), "docs", rel_path))
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def add_table(self, headers, rows_data):
        num_rows = len(rows_data) + 1
        num_cols = len(headers)
        table = self.doc.add_table(rows=num_rows, cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table, color="CBD5E1", sz="4", val="single")

        # Proportional column widths totaling 6.5 inches
        base_width = Inches(6.5 / num_cols)

        # Header Row
        hdr_row = table.rows[0]
        trPr = hdr_row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

        for col_idx, h_text in enumerate(headers):
            cell = hdr_row.cells[col_idx]
            cell.width = base_width
            set_cell_shading(cell, "334155")
            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(h_text.strip())
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.color.rgb = hex_to_rgb("FFFFFF")
            r.bold = True

        # Data Rows
        for r_idx, r_data in enumerate(rows_data):
            row = table.rows[r_idx + 1]
            trPr = row._tr.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
            bg_color = "F8FAFC" if (r_idx % 2 == 1) else "FFFFFF"

            for c_idx in range(num_cols):
                cell = row.cells[c_idx]
                cell.width = base_width
                set_cell_shading(cell, bg_color)
                set_cell_margins(cell, top=90, bottom=90, left=120, right=120)
                val = r_data[c_idx].strip() if c_idx < len(r_data) else ""
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.1

                # Check if cell contains an image tag: <img src="..." ...>
                img_match = re.search(r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>', val)
                if img_match:
                    img_src = img_match.group(1)
                    full_path = self.resolve_image_path(img_src)
                    text_remaining = val[:img_match.start()] + val[img_match.end():]
                    text_remaining = text_remaining.replace('<br>', '\n').replace('<br/>', '\n').strip()
                    
                    if full_path:
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        r_pic = p.add_run()
                        try:
                            with Image.open(full_path) as img:
                                w_px, h_px = img.size
                            aspect = w_px / h_px
                            target_w = min(base_width * 0.9, Inches(2.6))
                            target_h = target_w / aspect
                            if target_h > Inches(3.6):
                                target_h = Inches(3.6)
                                target_w = target_h * aspect
                            r_pic.add_picture(full_path, width=target_w, height=target_h)
                        except Exception:
                            r_pic.add_picture(full_path, width=min(base_width * 0.9, Inches(2.2)))
                    if text_remaining:
                        p2 = cell.add_paragraph()
                        p2.paragraph_format.space_before = Pt(3)
                        p2.paragraph_format.space_after = Pt(0)
                        p2.paragraph_format.line_spacing = 1.1
                        add_formatted_runs(p2, text_remaining, base_font="Calibri", base_size=8.5, base_color="1F2937")
                else:
                    # Clean <br> into separate paragraphs
                    lines_in_val = val.replace('<br/>', '<br>').replace('<br />', '<br>').split('<br>')
                    for l_idx, l_text in enumerate(lines_in_val):
                        if l_idx > 0:
                            p = cell.add_paragraph()
                            p.paragraph_format.space_before = Pt(2)
                            p.paragraph_format.space_after = Pt(0)
                            p.paragraph_format.line_spacing = 1.1
                        add_formatted_runs(p, l_text.strip(), base_font="Calibri", base_size=9.0, base_color="1F2937")

        # Spacing after table
        p_sp = self.doc.add_paragraph()
        p_sp.paragraph_format.space_before = Pt(0)
        p_sp.paragraph_format.space_after = Pt(6)

    def add_image_from_path(self, rel_path, caption="", width_pts=None):
        full_path = self.resolve_image_path(rel_path)
        if not full_path:
            print(f"Warning: image path not found: {rel_path}")
            return

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_together = True
        if caption:
            p.paragraph_format.keep_with_next = True

        run = p.add_run()
        try:
            with Image.open(full_path) as img:
                w_px, h_px = img.size
            aspect = w_px / h_px

            if width_pts:
                target_w = Pt(width_pts)
            else:
                target_w = Inches(4.5) if aspect > 1.2 else Inches(2.3)

            target_h = target_w / aspect
            # Cap maximum height to 3.8 inches so mobile full screens fit comfortably on page with text
            if target_h > Inches(3.8):
                target_h = Inches(3.8)
                target_w = target_h * aspect

            # Cap maximum width to 5.8 inches
            if target_w > Inches(5.8):
                target_w = Inches(5.8)
                target_h = target_w / aspect

            run.add_picture(full_path, width=target_w, height=target_h)
        except Exception as e:
            run.add_picture(full_path, width=Pt(width_pts) if width_pts else Inches(4.5))

        if caption:
            p_cap = self.doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(1)
            p_cap.paragraph_format.space_after = Pt(6)
            p_cap.paragraph_format.keep_together = True
            r_cap = p_cap.add_run(caption)
            r_cap.font.name = "Calibri"
            r_cap.font.size = Pt(8.5)
            r_cap.font.color.rgb = hex_to_rgb("64748B")
            r_cap.italic = True

# --- Markdown Parser and Compiler ---

def parse_and_compile(md_filepath, docx_outpath, doc_title, doc_subtitle, metadata, short_title, is_formal_report=True):
    builder = MarkdownDocxBuilder(
        doc_title=doc_title,
        doc_subtitle=doc_subtitle,
        metadata_dict=metadata,
        base_dir=os.path.dirname(md_filepath)
    )

    with open(md_filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Strip HTML comments like <!-- ... -->
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    lines = content.split('\n')

    # Pre-scan headings for Table of Contents
    headings_list = []
    for line in lines:
        st = line.strip()
        if st.startswith('## '):
            headings_list.append((1, st[3:].strip()))
        elif st.startswith('### '):
            headings_list.append((2, st[4:].strip()))
        elif st.startswith('#### '):
            headings_list.append((3, st[5:].strip()))

    if is_formal_report:
        builder.build_cover_page()
        builder.setup_content_section_headers(short_title)
        builder.add_table_of_contents()
    else:
        # Simple doc: header/footer from beginning
        builder.setup_content_section_headers(short_title)
    i = 0
    in_code_block = False
    code_lang = ""
    code_lines = []

    in_table = False
    table_headers = []
    table_rows = []

    in_callout = False
    callout_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 1. Code Block Handling
        if stripped.startswith('```'):
            if in_code_block:
                builder.add_code_block('\n'.join(code_lines))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lang = stripped[3:].strip()
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # 2. Blockquote / Callout Handling
        if stripped.startswith('>'):
            callout_text = stripped[1:].strip()
            # If multiple callout lines, accumulate
            callout_lines.append(callout_text)
            # Peek next line
            if i + 1 < len(lines) and lines[i+1].strip().startswith('>'):
                i += 1
                continue
            else:
                builder.add_callout(' '.join(callout_lines))
                callout_lines = []
                i += 1
                continue

        # 3. Table Handling
        if '|' in stripped and ('|' in lines[i+1] if i + 1 < len(lines) else False):
            # Check if this is a markdown table
            if not in_table:
                # Potential table header
                cols = [c.strip() for c in stripped.split('|')[1:-1]]
                # Next line must be delimiter | :--- | :--- |
                if i + 1 < len(lines) and re.match(r'^[\|\s:\-]+$', lines[i+1].strip()):
                    table_headers = cols
                    table_rows = []
                    in_table = True
                    i += 2
                    continue

        if in_table:
            if '|' in stripped:
                cols = [c.strip() for c in stripped.split('|')[1:-1]]
                table_rows.append(cols)
                i += 1
                continue
            else:
                # Table ended
                builder.add_table(table_headers, table_rows)
                in_table = False
                table_headers = []
                table_rows = []
                # Don't increment i, parse current line

        # 4. Image tags: <img src="..." alt="..." width="..."> or ![alt](src)
        img_match = re.search(r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>', line)
        if img_match:
            img_src = img_match.group(1)
            # Check width
            w_match = re.search(r'width=["\']?(\d+)["\']?', line)
            w_pts = float(w_match.group(1)) if w_match else 280
            # Check alt
            alt_match = re.search(r'alt=["\']([^"\']+)["\']', line)
            caption = alt_match.group(1) if alt_match else ""
            builder.add_image_from_path(img_src, caption=caption, width_pts=w_pts)
            i += 1
            continue

        md_img = re.search(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        if md_img:
            caption = md_img.group(1)
            img_src = md_img.group(2)
            builder.add_image_from_path(img_src, caption=caption, width_pts=320)
            i += 1
            continue

        # 5. Headings
        if stripped.startswith('# '):
            # Skip doc title on body if it matches doc_title and has cover
            if not is_formal_report:
                builder.add_heading_1(stripped[2:].strip())
            i += 1
            continue
        elif stripped.startswith('## '):
            builder.add_heading_1(stripped[3:].strip())
            i += 1
            continue
        elif stripped.startswith('### '):
            builder.add_heading_2(stripped[4:].strip())
            i += 1
            continue
        elif stripped.startswith('#### '):
            builder.add_heading_3(stripped[5:].strip())
            i += 1
            continue
        elif stripped.startswith('##### '):
            builder.add_heading_4(stripped[6:].strip())
            i += 1
            continue

        # 6. Horizontal Rules
        if stripped in ('---', '***', '___'):
            i += 1
            continue

        # 7. Lists
        bullet_match = re.match(r'^(\s*)[*+-]\s+(.*)$', line)
        if bullet_match:
            indent = len(bullet_match.group(1)) // 2
            item_text = bullet_match.group(2).strip()
            builder.add_bullet_item(item_text, indent_level=indent)
            i += 1
            continue

        num_match = re.match(r'^(\s*)\d+\.\s+(.*)$', line)
        if num_match:
            indent = len(num_match.group(1)) // 2
            item_text = num_match.group(2).strip()
            builder.add_bullet_item(item_text, indent_level=indent)
            i += 1
            continue

        # 8. Ignore standalone HTML tags
        if re.match(r'^</?(p|div|span|center|a|br)[^>]*>$', stripped, flags=re.IGNORECASE):
            i += 1
            continue

        # 9. Regular Paragraphs
        if stripped:
            builder.add_body_paragraph(stripped)

        i += 1

    # If file ended inside table
    if in_table and table_headers:
        builder.add_table(table_headers, table_rows)

    builder.doc.save(docx_outpath)
    print(f"Successfully compiled: {docx_outpath}")

if __name__ == '__main__':
    # 1. Manual de Usuario Operativo
    parse_and_compile(
        md_filepath='docs/MANUAL_DE_USUARIO_OPERATIVO.md',
        docx_outpath='docs/MANUAL_DE_USUARIO_OPERATIVO.docx',
        doc_title='MANUAL DE USUARIO OPERATIVO',
        doc_subtitle='Módulo Móvil (AppSheet) — Guía Integral para Despachadores y Bodega',
        metadata={
            'Empresa': 'Intereléctricos Group SAS',
            'Proyecto': 'Sistema de Bonificaciones en Bodega',
            'Destinatarios': 'Despachadores, Auxiliares de Bodega y Supervisión',
            'Software': 'AppSheet PWA + Google Sheets Backend',
            'Autor': 'Mauricio Sierra — Aprendiz ADSO SENA',
            'Versión / Fecha': 'Versión 2.0 (Producción) | Octubre de 2026'
        },
        short_title='Manual de Usuario Operativo',
        is_formal_report=True
    )

    # 2. Informe Técnico y Manual de Configuración
    parse_and_compile(
        md_filepath='docs/INFORME_TECNICO_Y_MANUAL_DE_CONFIGURACION.md',
        docx_outpath='docs/INFORME_TECNICO_Y_MANUAL_DE_CONFIGURACION.docx',
        doc_title='INFORME TÉCNICO Y MANUAL DE CONFIGURACIÓN',
        doc_subtitle='Arquitectura de Datos, Fórmulas de Liquidación e Interfaz Móvil (AppSheet + Google Sheets)',
        metadata={
            'Empresa': 'Intereléctricos Group SAS',
            'Proyecto': 'Sistema de Bonificaciones en Bodega',
            'Destinatarios': 'Dirección de Operaciones, TI y Auditoría',
            'Software': 'AppSheet PWA + Google Sheets Backend',
            'Autor': 'Mauricio Sierra — Aprendiz ADSO SENA',
            'Versión / Fecha': 'Versión 2.0 (Producción) | Octubre de 2026'
        },
        short_title='Informe Técnico y Manual de Configuración',
        is_formal_report=True
    )

    # 3. Configuración Técnica de AppSheet
    parse_and_compile(
        md_filepath='schemas/appsheet_config.md',
        docx_outpath='docs/CONFIGURACION_TECNICA_APPSHEET.docx',
        doc_title='CONFIGURACIÓN TÉCNICA DE APPSHEET',
        doc_subtitle='Guía de Configuración Paso a Paso de Tablas, Columnas, Vistas y Reglas (V2.0)',
        metadata={
            'Empresa': 'Intereléctricos Group SAS',
            'Proyecto': 'Sistema de Bonificaciones en Bodega',
            'Destinatarios': 'Equipo de Sistemas y Desarrolladores AppSheet',
            'Software': 'Motor AppSheet Core Engine',
            'Autor': 'Mauricio Sierra — Aprendiz ADSO SENA',
            'Versión / Fecha': 'Versión 2.0 (Producción) | Octubre de 2026'
        },
        short_title='Configuración Técnica AppSheet',
        is_formal_report=True
    )

    # 4. Runbook de Soporte Técnico
    parse_and_compile(
        md_filepath='docs/RUNBOOK_SOPORTE_TECNICO.md',
        docx_outpath='docs/RUNBOOK_SOPORTE_TECNICO.docx',
        doc_title='RUNBOOK DE SOPORTE TÉCNICO',
        doc_subtitle='Diagnóstico de Incidencias, Mantenimiento Operativo y Contingencia (V2.0)',
        metadata={
            'Empresa': 'Intereléctricos Group SAS',
            'Proyecto': 'Sistema de Bonificaciones en Bodega',
            'Destinatarios': 'Equipo de Soporte Técnico, TI y Operaciones',
            'Software': 'AppSheet PWA + Google Sheets Backend',
            'Autor': 'Mauricio Sierra — Aprendiz ADSO SENA',
            'Versión / Fecha': 'Versión 2.0 (Producción) | Octubre de 2026'
        },
        short_title='Runbook Soporte Técnico',
        is_formal_report=True
    )
