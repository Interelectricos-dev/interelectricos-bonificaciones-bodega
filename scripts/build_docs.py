import os
import re
import math
from PIL import Image, ImageDraw, ImageFont
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

def add_image_border(run, color_hex="D9D9D9", width_emu=12700):
    """Applies a 1pt (12700 EMUs) solid border around any picture inside the given run."""
    color_clean = color_hex.lstrip('#')
    for spPr in run._r.xpath('.//pic:spPr'):
        ln = parse_xml(
            f'<a:ln xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" w="{width_emu}">'
            f'<a:solidFill><a:srgbClr val="{color_clean}"/></a:solidFill>'
            f'</a:ln>'
        )
        spPr.append(ln)

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

def set_run_shading(run, color_hex="F1F5F9"):
    """Applies a subtle background highlight/shading behind a text run (code tags)."""
    rPr = run._r.get_or_add_rPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex.lstrip("#")}" w:val="clear"/>')
    rPr.append(shd)

def add_formatted_runs(paragraph, text, base_font="Calibri", base_size=10.5, base_color="1F2937", is_bold=False, is_italic=False):
    # Clean markdown links [label](url) -> label
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Clean non-breaking spaces or double spaces
    text = text.replace('&nbsp;', ' ')
    
    # Parses inline markdown: **bold**, *italic*, `code`, and plain text with nested code support
    tokens = re.split(r'(`[^`]+`|\*\*[^*]+?\*\*|\*[^*]+?\*)', text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith('**') and tok.endswith('**') and len(tok) >= 4:
            inner = tok[2:-2]
            sub_toks = re.split(r'(`[^`]+`)', inner)
            for st in sub_toks:
                if not st:
                    continue
                if st.startswith('`') and st.endswith('`') and len(st) >= 2:
                    r = paragraph.add_run(st[1:-1])
                    r.font.name = 'Consolas'
                    r.font.size = Pt(base_size * 0.9)
                    r.font.color.rgb = hex_to_rgb("0F172A")
                    r.bold = True
                    r.italic = is_italic
                    set_run_shading(r, "F1F5F9")
                else:
                    r = paragraph.add_run(st.replace('`', ''))
                    r.font.name = base_font
                    r.font.size = Pt(base_size)
                    r.font.color.rgb = hex_to_rgb(base_color)
                    r.bold = True
                    r.italic = is_italic
        elif tok.startswith('*') and tok.endswith('*') and len(tok) >= 2:
            inner = tok[1:-1]
            sub_toks = re.split(r'(`[^`]+`)', inner)
            for st in sub_toks:
                if not st:
                    continue
                if st.startswith('`') and st.endswith('`') and len(st) >= 2:
                    r = paragraph.add_run(st[1:-1])
                    r.font.name = 'Consolas'
                    r.font.size = Pt(base_size * 0.9)
                    r.font.color.rgb = hex_to_rgb("0F172A")
                    r.bold = is_bold
                    r.italic = True
                    set_run_shading(r, "F1F5F9")
                else:
                    r = paragraph.add_run(st.replace('`', ''))
                    r.font.name = base_font
                    r.font.size = Pt(base_size)
                    r.font.color.rgb = hex_to_rgb(base_color)
                    r.bold = is_bold
                    r.italic = True
        elif tok.startswith('`') and tok.endswith('`') and len(tok) >= 2:
            r = paragraph.add_run(tok[1:-1])
            r.font.name = 'Consolas'
            r.font.size = Pt(base_size * 0.9)
            r.font.color.rgb = hex_to_rgb("0F172A")
            r.bold = is_bold
            r.italic = is_italic
            set_run_shading(r, "F1F5F9")
        else:
            r = paragraph.add_run(tok.replace('`', ''))
            r.font.name = base_font
            r.font.size = Pt(base_size)
            r.font.color.rgb = hex_to_rgb(base_color)
            r.bold = is_bold
            r.italic = is_italic

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
            s_h1.paragraph_format.space_before = Pt(0)
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

        # Remover numPr de cualquier estilo de párrafo para evitar doble viñeta o numeraciones no deseadas en Word
        from docx.enum.style import WD_STYLE_TYPE
        for s in styles:
            if s.type == WD_STYLE_TYPE.PARAGRAPH and s._element.pPr is not None:
                np = s._element.pPr.find(qn('w:numPr'))
                if np is not None:
                    s._element.pPr.remove(np)

        # Custom Styles semánticos para Viñetas y Listas sin numPr nativo
        if 'Viñeta' not in styles:
            s_bul = styles.add_style('Viñeta', WD_STYLE_TYPE.PARAGRAPH)
            s_bul.base_style = styles['Normal']
            s_bul.font.name = 'Calibri'
            s_bul.font.size = Pt(10.5)
            s_bul.font.color.rgb = hex_to_rgb('1F2937')
            s_bul.paragraph_format.line_spacing = 1.15

        if 'Subviñeta' not in styles:
            s_bul2 = styles.add_style('Subviñeta', WD_STYLE_TYPE.PARAGRAPH)
            s_bul2.base_style = styles['Normal']
            s_bul2.font.name = 'Calibri'
            s_bul2.font.size = Pt(10.5)
            s_bul2.font.color.rgb = hex_to_rgb('1F2937')
            s_bul2.paragraph_format.line_spacing = 1.15

        if 'Subviñeta 2' not in styles:
            s_bul3 = styles.add_style('Subviñeta 2', WD_STYLE_TYPE.PARAGRAPH)
            s_bul3.base_style = styles['Normal']
            s_bul3.font.name = 'Calibri'
            s_bul3.font.size = Pt(10.5)
            s_bul3.font.color.rgb = hex_to_rgb('1F2937')
            s_bul3.paragraph_format.line_spacing = 1.15

        if 'Lista Numerada' not in styles:
            s_num = styles.add_style('Lista Numerada', WD_STYLE_TYPE.PARAGRAPH)
            s_num.base_style = styles['Normal']
            s_num.font.name = 'Calibri'
            s_num.font.size = Pt(10.5)
            s_num.font.color.rgb = hex_to_rgb('1F2937')
            s_num.paragraph_format.line_spacing = 1.2

        if 'Lista Numerada 2' not in styles:
            s_num2 = styles.add_style('Lista Numerada 2', WD_STYLE_TYPE.PARAGRAPH)
            s_num2.base_style = styles['Normal']
            s_num2.font.name = 'Calibri'
            s_num2.font.size = Pt(10.5)
            s_num2.font.color.rgb = hex_to_rgb('1F2937')
            s_num2.paragraph_format.line_spacing = 1.2

        # Caption
        if 'Caption' in styles:
            s_cap = styles['Caption']
            s_cap.font.name = 'Calibri'
            s_cap.font.size = Pt(8.5)
            s_cap.font.italic = True
            s_cap.font.color.rgb = hex_to_rgb('64748B')
            s_cap.paragraph_format.space_before = Pt(1)
            s_cap.paragraph_format.space_after = Pt(6)

        # Custom Styles semánticos para Código, Checklist y Callout
        if 'Code Block' not in styles:
            s_code = styles.add_style('Code Block', WD_STYLE_TYPE.PARAGRAPH)
            s_code.base_style = styles['Normal']
            s_code.font.name = 'Consolas'
            s_code.font.size = Pt(9.0)
            s_code.font.color.rgb = hex_to_rgb('0F172A')
            s_code.paragraph_format.line_spacing = 1.15
            s_code.paragraph_format.space_before = Pt(0)
            s_code.paragraph_format.space_after = Pt(0)

        if 'Checklist' not in styles:
            s_chk = styles.add_style('Checklist', WD_STYLE_TYPE.PARAGRAPH)
            s_chk.base_style = styles['Normal']
            s_chk.font.name = 'Calibri'
            s_chk.font.size = Pt(10.5)
            s_chk.font.color.rgb = hex_to_rgb('1F2937')

        if 'Callout Text' not in styles:
            s_call = styles.add_style('Callout Text', WD_STYLE_TYPE.PARAGRAPH)
            s_call.base_style = styles['Normal']
            s_call.font.name = 'Calibri'
            s_call.font.size = Pt(10.0)
            s_call.font.color.rgb = hex_to_rgb('1E293B')

        # TOC Heading (excluded from TOC hierarchy by Word and WPS Office)
        if 'TOC Heading' in styles:
            s_toch = styles['TOC Heading']
            s_toch.font.name = 'Calibri'
            s_toch.font.size = Pt(15.0)
            s_toch.font.bold = True
            s_toch.font.color.rgb = hex_to_rgb('1E293B')
            s_toch.paragraph_format.space_before = Pt(0)
            s_toch.paragraph_format.space_after = Pt(14)
            s_toch.paragraph_format.keep_with_next = True

    def build_cover_page(self):
        # Section 0 is the cover
        sec = self.doc.sections[0]
        
        # Company banner
        p_comp = self.doc.add_paragraph()
        p_comp.paragraph_format.space_before = Pt(8)
        p_comp.paragraph_format.space_after = Pt(2)
        r_comp = p_comp.add_run("INTERELECTRICOS GROUP SAS")
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
        r_hdr = p_hdr.add_run(f"Interelectricos — Sistema de Bonificaciones Bodega | {short_title}")
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
        r_ftr_title = p_ftr.add_run("Página ")
        r_ftr_title.font.name = "Calibri"
        r_ftr_title.font.size = Pt(8.5)
        r_ftr_title.font.color.rgb = hex_to_rgb("64748B")
        add_page_number_field(p_ftr)

        pBdr_ftr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:top w:val="single" w:sz="4" w:space="4" w:color="CBD5E1"/></w:pBdr>')
        p_ftr._p.get_or_add_pPr().append(pBdr_ftr)

    def add_table_of_contents(self):
        p_toc_title = self.doc.add_paragraph(style='TOC Heading')
        p_toc_title.paragraph_format.space_before = Pt(0)
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
        self.doc.add_page_break()

    def add_heading_1(self, text):
        p = self.doc.add_paragraph(style='Heading 1')
        if self.h1_count > 0:
            p.paragraph_format.page_break_before = True
        self.h1_count += 1
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.keep_with_next = True
        add_formatted_runs(p, text, base_font="Calibri", base_size=15.0, base_color="1E293B", is_bold=True)

    def add_heading_2(self, text):
        p = self.doc.add_paragraph(style='Heading 2')
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        add_formatted_runs(p, text, base_font="Calibri", base_size=12.5, base_color="334155", is_bold=True)

    def add_heading_3(self, text):
        p = self.doc.add_paragraph(style='Heading 3')
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        add_formatted_runs(p, text, base_font="Calibri", base_size=11.5, base_color="374151", is_bold=True)

    def add_heading_4(self, text):
        p = self.doc.add_paragraph(style='Heading 4')
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        add_formatted_runs(p, text, base_font="Calibri", base_size=10.5, base_color="475569", is_bold=True)

    def add_body_paragraph(self, text):
        p = self.doc.add_paragraph(style='Normal')
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.15
        add_formatted_runs(p, text, base_font="Calibri", base_size=10.5, base_color="1F2937")

    def add_bullet_item(self, text, indent_level=0, has_sub_bullets=False):
        style_name = 'Viñeta' if indent_level == 0 else ('Subviñeta' if indent_level == 1 else 'Subviñeta 2')
        p = self.doc.add_paragraph(style=style_name)
        if indent_level == 0:
            p.paragraph_format.left_indent = Inches(0.28)
            p.paragraph_format.first_line_indent = Inches(-0.18)
            p.paragraph_format.space_before = Pt(5)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.keep_with_next = has_sub_bullets
            bullet_char = "•  "
            bullet_color = "1E293B"
        else:
            p.paragraph_format.left_indent = Inches(0.54 if indent_level == 1 else 0.76)
            p.paragraph_format.first_line_indent = Inches(-0.18)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(1.5)
            p.paragraph_format.keep_with_next = has_sub_bullets
            bullet_char = "◦  " if indent_level == 1 else "▪  "
            bullet_color = "475569"
        p.paragraph_format.line_spacing = 1.15
        r_bul = p.add_run(bullet_char)
        r_bul.font.name = "Calibri"
        r_bul.font.size = Pt(10.5)
        r_bul.font.color.rgb = hex_to_rgb(bullet_color)
        r_bul.bold = (indent_level == 0)
        add_formatted_runs(p, text, base_font="Calibri", base_size=10.5, base_color="1F2937")

    def add_checklist_item(self, text, is_checked=False, indent_level=0):
        p = self.doc.add_paragraph(style='Checklist')
        p.paragraph_format.left_indent = Inches(0.28 if indent_level == 0 else 0.54)
        p.paragraph_format.first_line_indent = Inches(-0.18)
        p.paragraph_format.space_before = Pt(4 if indent_level == 0 else 0)
        p.paragraph_format.space_after = Pt(1 if indent_level == 0 else 1.5)
        if indent_level == 0:
            p.paragraph_format.keep_with_next = True
        p.paragraph_format.line_spacing = 1.15
        box_char = "☑  " if is_checked else "☐  "
        r_box = p.add_run(box_char)
        r_box.font.name = "Segoe UI Symbol"
        r_box.font.size = Pt(11.0)
        r_box.font.color.rgb = hex_to_rgb("0284C7" if is_checked else "64748B")
        r_box.bold = True
        add_formatted_runs(p, text, base_font="Calibri", base_size=10.5, base_color="1F2937")

    def add_numbered_item(self, num_prefix, text, indent_level=0):
        style_name = 'Lista Numerada' if indent_level == 0 else 'Lista Numerada 2'
        p = self.doc.add_paragraph(style=style_name)
        p.paragraph_format.left_indent = Inches(0.28 if indent_level == 0 else 0.54)
        p.paragraph_format.first_line_indent = Inches(-0.22)
        p.paragraph_format.space_before = Pt(6) if indent_level == 0 else Pt(0)
        p.paragraph_format.space_after = Pt(3) if indent_level == 0 else Pt(1.5)
        p.paragraph_format.line_spacing = 1.2
        r_num = p.add_run(f"{num_prefix} ")
        r_num.font.name = "Calibri"
        r_num.font.size = Pt(10.5)
        r_num.font.color.rgb = hex_to_rgb("1E293B")
        r_num.bold = True
        add_formatted_runs(p, text, base_font="Calibri", base_size=10.5, base_color="1F2937")

    def add_code_block(self, code_text):
        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        row = table.rows[0]
        # No se aplica cantSplit para permitir que callouts extensos fluyan naturalmente entre paginas
        cell = row.cells[0]
        cell.width = Inches(6.5)
        set_cell_shading(cell, "F8FAFC")
        set_code_box_borders(cell, color="E2E8F0", sz="4")
        set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
        
        p = cell.paragraphs[0]
        p.style = 'Code Block'
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.15
        lines = code_text.strip().split('\n')
        for i, line in enumerate(lines):
            r = p.add_run(line)
            r.font.name = "Consolas"
            r.font.size = Pt(9.0)
            r.font.color.rgb = hex_to_rgb("0F172A")
            if i < len(lines) - 1:
                p.add_run('\n')

    def add_callout(self, callout_lines):
        if isinstance(callout_lines, str):
            callout_lines = [callout_lines]

        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        row = table.rows[0]
        # No se aplica cantSplit para permitir que callouts extensos fluyan naturalmente entre paginas
        cell = row.cells[0]
        cell.width = Inches(6.5)
        set_cell_shading(cell, "F0F9FF")
        set_callout_borders(cell, color="0284C7", sz="36")
        set_cell_margins(cell, top=120, bottom=120, left=180, right=180)

        first_p_used = False
        in_callout_code = False

        def get_next_p():
            nonlocal first_p_used
            if not first_p_used:
                first_p_used = True
                return cell.paragraphs[0]
            return cell.add_paragraph()

        for raw_line in callout_lines:
            st = raw_line.strip()
            if st.startswith('```'):
                in_callout_code = not in_callout_code
                continue

            if in_callout_code:
                p = get_next_p()
                p.style = 'Code Block'
                p.paragraph_format.left_indent = Inches(0.32)
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.15
                r = p.add_run(raw_line)
                r.font.name = "Consolas"
                r.font.size = Pt(8.5)
                r.font.color.rgb = hex_to_rgb("0F172A")
                continue

            if not st:
                if first_p_used and cell.paragraphs:
                    cell.paragraphs[-1].paragraph_format.space_after = Pt(5)
                continue

            bul_m = re.match(r'^(\s*)[*+-]\s+(.*)$', raw_line)
            num_m = re.match(r'^(\s*)(\d+\.)\s+(.*)$', raw_line)

            if bul_m:
                spaces = len(bul_m.group(1))
                lvl = 0 if spaces < 2 else 1
                txt = bul_m.group(2).strip()
                p = get_next_p()
                p.style = 'Viñeta' if lvl == 0 else 'Subviñeta'
                p.paragraph_format.left_indent = Inches(0.20 if lvl == 0 else 0.40)
                p.paragraph_format.first_line_indent = Inches(-0.15)
                p.paragraph_format.space_before = Pt(3.5 if lvl == 0 else 0)
                p.paragraph_format.space_after = Pt(1 if lvl == 0 else 1.5)
                if lvl == 0:
                    p.paragraph_format.keep_with_next = True
                p.paragraph_format.line_spacing = 1.15
                r_b = p.add_run("•  " if lvl == 0 else "◦  ")
                r_b.font.name = "Calibri"
                r_b.font.size = Pt(10.0)
                r_b.font.color.rgb = hex_to_rgb("1E293B" if lvl == 0 else "475569")
                r_b.bold = (lvl == 0)
                add_formatted_runs(p, txt, base_font="Calibri", base_size=10.0, base_color="1E293B")
            elif num_m:
                spaces = len(num_m.group(1))
                lvl = 0 if spaces < 2 else 1
                num_str = num_m.group(2)
                txt = num_m.group(3).strip()
                p = get_next_p()
                p.style = 'Lista Numerada' if lvl == 0 else 'Lista Numerada 2'
                p.paragraph_format.left_indent = Inches(0.22 if lvl == 0 else 0.42)
                p.paragraph_format.first_line_indent = Inches(-0.18)
                p.paragraph_format.space_before = Pt(3.5 if lvl == 0 else 0)
                p.paragraph_format.space_after = Pt(1 if lvl == 0 else 1.5)
                if lvl == 0:
                    p.paragraph_format.keep_with_next = True
                p.paragraph_format.line_spacing = 1.15
                r_n = p.add_run(f"{num_str} ")
                r_n.font.name = "Calibri"
                r_n.font.size = Pt(10.0)
                r_n.font.color.rgb = hex_to_rgb("1E293B")
                r_n.bold = True
                add_formatted_runs(p, txt, base_font="Calibri", base_size=10.0, base_color="1E293B")
            else:
                p = get_next_p()
                p.style = 'Callout Text'
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.line_spacing = 1.15
                add_formatted_runs(p, st, base_font="Calibri", base_size=10.0, base_color="1E293B")

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

    def _populate_gallery_cell(self, cell, val, base_width):
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0

        img_match = re.search(r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>', val)
        if img_match:
            img_src = img_match.group(1)
            full_path = self.resolve_image_path(img_src)
            alt_match = re.search(r'alt=["\']([^"\']+)["\']', img_match.group(0))
            caption_from_alt = alt_match.group(1) if alt_match else ""

            text_remaining = val[:img_match.start()] + val[img_match.end():]
            text_remaining = text_remaining.replace('<br>', '\n').replace('<br/>', '\n').strip()

            caption = text_remaining or caption_from_alt

            if full_path:
                r_pic = p.add_run()
                try:
                    with Image.open(full_path) as img:
                        w_px, h_px = img.size
                    aspect = w_px / h_px
                    target_w = min(base_width * 0.96, Inches(3.12))
                    target_h = target_w / aspect
                    max_h = Inches(3.50) if base_width < Inches(2.5) else Inches(4.2)
                    if target_h > max_h:
                        target_h = max_h
                        target_w = target_h * aspect
                    r_pic.add_picture(full_path, width=target_w, height=target_h)
                except Exception as e:
                    print(f"Error cargando imagen de galeria {full_path}: {e}")
                    r_pic.add_picture(full_path, width=min(base_width * 0.95, Inches(2.8)))
                add_image_border(r_pic, "D9D9D9")

            if caption:
                p_cap = cell.add_paragraph(style='Caption')
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_before = Pt(2)
                p_cap.paragraph_format.space_after = Pt(2)
                p_cap.paragraph_format.line_spacing = 1.05
                clean_cap = caption.strip('*_ ')
                add_formatted_runs(p_cap, clean_cap, base_font="Calibri", base_size=8.5, base_color="64748B", is_italic=True)
        else:
            add_formatted_runs(p, val, base_font="Calibri", base_size=9.5, base_color="1E293B", is_bold=True)

    def add_table(self, headers, rows_data):
        num_cols = len(headers)

        # Detectar si es una tabla de galeria de imagenes (modales o celular en 2 o 3 columnas)
        all_cells = headers + [c for r in rows_data for c in r]
        has_imgs = any('<img' in c for c in all_cells)
        is_gallery = has_imgs and (any('<img' in h for h in headers) or all(('<img' in c or not c) for r in rows_data for c in r))

        if is_gallery:
            all_table_rows = [headers] if any('<img' in h for h in headers) else []
            all_table_rows.extend(rows_data)
            header_is_text = not any('<img' in h for h in headers)

            table = self.doc.add_table(rows=len(all_table_rows) + (1 if header_is_text else 0), cols=num_cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            set_table_borders(table, val="none")

            base_width = Inches(6.5 / num_cols)
            cur_r_idx = 0

            if header_is_text:
                hdr_row = table.rows[0]
                cur_r_idx = 1
                for col_idx, h_text in enumerate(headers):
                    cell = hdr_row.cells[col_idx]
                    cell.width = base_width
                    set_cell_shading(cell, "FFFFFF")
                    set_cell_margins(cell, top=40, bottom=40, left=40, right=40)
                    p = cell.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(2)
                    add_formatted_runs(p, h_text.strip(), base_font="Calibri", base_size=9.5, base_color="1E293B", is_bold=True)

            for r_idx, r_data in enumerate(all_table_rows):
                row = table.rows[cur_r_idx + r_idx]
                trPr = row._tr.get_or_add_trPr()
                trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
                for c_idx in range(num_cols):
                    cell = row.cells[c_idx]
                    cell.width = base_width
                    set_cell_shading(cell, "FFFFFF")
                    set_cell_margins(cell, top=40, bottom=60, left=40, right=40)
                    val = r_data[c_idx].strip() if c_idx < len(r_data) else ""
                    self._populate_gallery_cell(cell, val, base_width)

            return

        num_rows = len(rows_data) + 1
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
            add_formatted_runs(p, h_text.strip(), base_font="Calibri", base_size=9.5, base_color="FFFFFF", is_bold=True)

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
                        add_image_border(r_pic, "D9D9D9")
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
        add_image_border(run, "D9D9D9")

        if caption:
            p_cap = self.doc.add_paragraph(style='Caption')
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
    in_manual_toc = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip manual markdown Table of Contents section when formal report already has native Word TOC
        if is_formal_report and stripped.startswith('## '):
            h1_title_lower = stripped[3:].strip().lower()
            if h1_title_lower in ('tabla de contenidos', 'tabla de contenido', 'índice', 'indice'):
                in_manual_toc = True
                i += 1
                continue
            else:
                in_manual_toc = False

        if in_manual_toc:
            i += 1
            continue

        # Skip duplicate header metadata lines before the first Heading 1 when formal cover page exists
        if is_formal_report and builder.h1_count == 0 and re.match(
            r'^\*\*(Proyecto|Empresa|Fecha|Autor|Entorno Tecnol[oó]gico|Destinatarios|Versi[oó]n|Estado):\*\*',
            stripped
        ):
            i += 1
            continue

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
            callout_line = re.sub(r'^>\s?', '', stripped)
            # Accumulate lines preserving structure inside the callout
            callout_lines.append(callout_line)
            # Peek next line
            if i + 1 < len(lines) and lines[i+1].strip().startswith('>'):
                i += 1
                continue
            else:
                builder.add_callout(callout_lines)
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
        checklist_match = re.match(r'^(\s*)[*+-]\s+\[([ xX])\]\s+(.*)$', line)
        if checklist_match:
            raw_spaces = len(checklist_match.group(1))
            indent = 0 if raw_spaces < 2 else (1 if raw_spaces < 5 else 2)
            is_checked = checklist_match.group(2).lower() == 'x'
            item_text = checklist_match.group(3).strip()
            builder.add_checklist_item(item_text, is_checked=is_checked, indent_level=indent)
            i += 1
            continue

        bullet_match = re.match(r'^(\s*)[*+-]\s+(.*)$', line)
        if bullet_match:
            raw_spaces = len(bullet_match.group(1))
            indent = 0 if raw_spaces < 2 else (1 if raw_spaces < 5 else 2)
            item_text = bullet_match.group(2).strip()

            # Detectar si esta viñeta tiene sub-viñetas o bloque de fórmula directamente subordinado
            has_sub = False
            for next_idx in range(i + 1, min(i + 6, len(lines))):
                next_st = lines[next_idx].strip()
                if not next_st:
                    continue
                next_bul = re.match(r'^(\s*)[*+-]\s+(.*)$', lines[next_idx])
                if next_bul:
                    next_spaces = len(next_bul.group(1))
                    next_indent = 0 if next_spaces < 2 else (1 if next_spaces < 5 else 2)
                    if next_indent > indent:
                        has_sub = True
                    break
                elif next_st.startswith('```'):
                    has_sub = True
                    break
                else:
                    break

            builder.add_bullet_item(item_text, indent_level=indent, has_sub_bullets=has_sub)
            i += 1
            continue

        num_match = re.match(r'^(\s*)(\d+\.)\s+(.*)$', line)
        if num_match:
            raw_spaces = len(num_match.group(1))
            indent = 0 if raw_spaces < 2 else 1
            num_prefix = num_match.group(2)
            item_text = num_match.group(3).strip()
            builder.add_numbered_item(num_prefix, item_text, indent_level=indent)
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

def generate_architecture_diagram_png(out_path='docs/images/arquitectura_flujo_v2.png'):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    W, H = 1800, 1260
    img = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    def get_font(bold=False, size=22):
        path = "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    f_title = get_font(True, 29)
    f_layer = get_font(True, 20)
    f_box_title = get_font(True, 20)
    f_box_sub = get_font(False, 17)
    f_lbl = get_font(True, 15)

    # Title banner
    draw.rounded_rectangle([40, 20, W-40, 80], radius=12, fill="#1E293B")
    draw.text((W//2, 50), "ARQUITECTURA GENERAL Y FLUJO DE INFORMACIÓN (VERSIÓN 2.1)", fill="#FFFFFF", font=f_title, anchor="mm")

    # Layer backgrounds
    draw.rounded_rectangle([40, 100, W-40, 360], radius=16, fill="#F8FAFC", outline="#CBD5E1", width=2)
    draw.rounded_rectangle([40, 445, W-40, 675], radius=16, fill="#F0F9FF", outline="#BAE6FD", width=2)
    draw.rounded_rectangle([40, 760, W-40, 1225], radius=16, fill="#F0FDF4", outline="#BBF7D0", width=2)

    # Layer Top Bars (full width header strips inside each layer)
    draw.rounded_rectangle([40, 100, W-40, 142], radius=16, fill="#0284C7")
    draw.rectangle([40, 125, W-40, 142], fill="#0284C7")
    draw.text((W//2, 121), "1. CAPA DE CAPTURA Y CONSULTA (APPSHEET MÓVIL / PWA + WHATSAPP BODEGA)", fill="#FFFFFF", font=f_layer, anchor="mm")

    draw.rounded_rectangle([40, 445, W-40, 487], radius=16, fill="#0369A1")
    draw.rectangle([40, 470, W-40, 487], fill="#0369A1")
    draw.text((W//2, 466), "2. CAPA DE ORQUESTACIÓN Y PROCESAMIENTO EN LA NUBE (APPSHEET ENGINE + VERCEL IA)", fill="#FFFFFF", font=f_layer, anchor="mm")

    draw.rounded_rectangle([40, 760, W-40, 802], radius=16, fill="#15803D")
    draw.rectangle([40, 785, W-40, 802], fill="#15803D")
    draw.text((W//2, 781), "3. CAPA DE ALMACENAMIENTO Y MOTOR MATRICIAL EN MEMORIA (GOOGLE SHEETS)", fill="#FFFFFF", font=f_layer, anchor="mm")

    def draw_box(x1, y1, x2, y2, title, lines, bg="#FFFFFF", border="#334155", header_bg=None):
        draw.rounded_rectangle([x1+3, y1+4, x2+3, y2+4], radius=12, fill="#E2E8F0")
        draw.rounded_rectangle([x1, y1, x2, y2], radius=12, fill=bg, outline=border, width=3)
        cx = (x1 + x2) // 2
        if header_bg:
            draw.rounded_rectangle([x1, y1, x2, y1+40], radius=12, fill=header_bg, outline=border, width=3)
            draw.rectangle([x1+2, y1+26, x2-2, y1+40], fill=header_bg)
            draw.text((cx, y1+21), title, fill="#FFFFFF", font=f_box_title, anchor="mm")
            ty = y1 + 62
        else:
            draw.text((cx, y1+26), title, fill="#0F172A", font=f_box_title, anchor="mm")
            ty = y1 + 56
        for line in lines:
            draw.text((cx, ty), line, fill="#334155", font=f_box_sub, anchor="mm")
            ty += 24

    def draw_arrow(x1, y1, x2, y2, color="#334155", label="", lx=None, ly=None, dashed=False):
        if dashed:
            dist = math.hypot(x2-x1, y2-y1)
            steps = max(1, int(dist // 10))
            for s in range(0, steps, 2):
                px1 = x1 + (x2-x1)*s/steps
                py1 = y1 + (y2-y1)*s/steps
                px2 = x1 + (x2-x1)*min(s+1, steps)/steps
                py2 = y1 + (y2-y1)*min(s+1, steps)/steps
                draw.line([(px1, py1), (px2, py2)], fill=color, width=3)
        else:
            draw.line([(x1, y1), (x2, y2)], fill=color, width=4)
        angle = math.atan2(y2-y1, x2-x1)
        ah = 12
        p1 = (x2 - ah*math.cos(angle - math.pi/6), y2 - ah*math.sin(angle - math.pi/6))
        p2 = (x2 - ah*math.cos(angle + math.pi/6), y2 - ah*math.sin(angle + math.pi/6))
        draw.polygon([(x2, y2), p1, p2], fill=color)
        if label:
            tx = lx if lx is not None else (x1+x2)//2
            ty = ly if ly is not None else (y1+y2)//2
            bbox = draw.textbbox((tx, ty), label, font=f_lbl, anchor="mm")
            draw.rounded_rectangle([bbox[0]-8, bbox[1]-4, bbox[2]+8, bbox[3]+4], radius=5, fill="#FFFFFF", outline=color, width=2)
            draw.text((tx, ty), label, fill=color, font=f_lbl, anchor="mm")

    # Boxes Layer 1
    draw_box(70, 162, 460, 338, "Vista NUEVO REGISTRO", ["Formulario táctil AppSheet", "Botonera Tipo (IC, DP, IR)", "Teclado numérico directo"], border="#0284C7", header_bg="#0284C7")
    draw_box(495, 162, 885, 338, "Vista HISTORIAL HOY", ["Auditoría diaria en vivo", "Columna virtual Hora y Factura", "Edición bloqueada a los 15 min"], border="#0284C7", header_bg="#0284C7")
    draw_box(920, 162, 1310, 338, "Vista LIQUIDACION", ["Drill-Down: Año > Mes > Quincena", "Ordenado por Pts_Esfuerzo", "Resaltado de bonos (> $0)"], border="#0284C7", header_bg="#0284C7")
    draw_box(1345, 162, 1730, 338, "WhatsApp Bodega (Voz/Texto)", ["Notas de voz (.ogg) o texto", "Despacho individual o por bloque", "Confirmación instantánea"], border="#0D9488", header_bg="#0D9488")

    # Boxes Layer 2
    draw_box(120, 505, 1020, 655, "AppSheet Core Engine (Sincronización Bidireccional)", ["• Validación de campos obligatorios, reglas de negocio y seguridad (15 min)", "• Cálculo de columnas virtuales (Factura, Hora, ID_Liquidacion) y Format Rules"], border="#0369A1", header_bg="#0369A1")
    draw_box(1090, 505, 1720, 655, "Bot Serverless Vercel + Green API + Gemini 3.5 Flash", ["• Filtro de privacidad Fail-Closed (CHAT_ID_PRUEBA)", "• Extracción multimodal JSON sin alucinación y cruce de EMPLEADOS"], border="#0F766E", header_bg="#0F766E")

    # Boxes Layer 3
    draw_box(80, 822, 560, 975, "Tabla REGISTRO_DIARIO", ["7 Columnas físicas atómicas", "(ID, Fecha_Hora, Empleado, Tipo, N°,", "Puntos_Esfuerzo, Puntos_Error)"], border="#15803D", header_bg="#15803D")
    draw_box(640, 822, 1140, 975, "Tabla EMPLEADOS", ["Catálogo maestro de personal", "(ID_Empleado, Nombre_Completo, Activo)", "Validación de operarios activos"], border="#15803D", header_bg="#15803D")
    draw_box(1200, 822, 1720, 975, "Tabla CONFIGURACION", ["Parámetros salariales y Ley 1393", "Meta Base (300 pts), Bono Calidad ($100.000)", "Tramos de $50k a $200k (Tope neto $300.000)"], border="#15803D", header_bg="#15803D")

    draw_box(120, 1045, 1040, 1200, "Motor Matricial BASE_HISTORICA (En Memoria RAM)", ["Fórmula única en A1: LET + MAP + LAMBDA + QUERY", "Agrupa por Año, Mes, Quincena (Q1/Q2) e ID_Empleado y liquida Bonos (G1:J1)"], border="#1E293B", header_bg="#1E293B")
    draw_box(1140, 1045, 1720, 1200, "Dashboard LIQUIDACION_MES", ["Tablero ejecutivo para Gerencia y Nómina", "Filtro dinámico por Año, Mes y Quincena"], border="#334155", header_bg="#334155")

    # Arrows Layer 1 <-> Layer 2 (placed in the clean corridor y=360..445)
    draw_arrow(265, 338, 300, 505, "#0284C7", "Inserta despacho", lx=280, ly=402)
    draw_arrow(690, 505, 690, 338, "#0284C7", "Sincroniza hoy", lx=690, ly=402)
    draw_arrow(920, 505, 1080, 338, "#0284C7", "Renderiza liquidación", lx=1010, ly=402)
    draw_arrow(1535, 338, 1480, 505, "#0F766E", "Webhook audio/texto", lx=1510, ly=402)

    # Arrows Layer 2 <-> Layer 3 (placed in the clean corridor y=675..760)
    draw_arrow(260, 655, 260, 822, "#15803D", "Escribe fila", lx=260, ly=718)
    draw_arrow(600, 1045, 600, 655, "#0369A1", "Alimenta vista jerárquica", lx=600, ly=718)
    draw_arrow(1250, 655, 460, 822, "#0F766E", "Batch append (bloque/unidad)", lx=960, ly=718)
    draw_arrow(1440, 655, 980, 822, "#0F766E", "Valida empleado activo", lx=1310, ly=718, dashed=True)

    # Arrows inside Layer 3 (placed in the clean corridor y=975..1045)
    draw_arrow(320, 975, 380, 1045, "#1E293B", "Lectura vectorial", lx=350, ly=1010, dashed=True)
    draw_arrow(890, 975, 760, 1045, "#1E293B", "Cruza nombres", lx=825, ly=1010, dashed=True)
    draw_arrow(1460, 975, 960, 1045, "#1E293B", "Meta y tramos", lx=1210, ly=1010, dashed=True)
    draw_arrow(1040, 1122, 1140, 1122, "#334155", "QUERY")

    img.save(out_path, "PNG", optimize=True)
    print(f"Successfully generated architecture diagram: {out_path}")

if __name__ == '__main__':
    generate_architecture_diagram_png()
    # 1. Manual de Usuario Operativo
    parse_and_compile(
        md_filepath='docs/MANUAL_DE_USUARIO_OPERATIVO.md',
        docx_outpath='docs/MANUAL_DE_USUARIO_OPERATIVO.docx',
        doc_title='MANUAL DE USUARIO OPERATIVO',
        doc_subtitle='Módulo Móvil (AppSheet) y Bot de WhatsApp con IA — Guía Integral para Bodega',
        metadata={
            'Empresa': 'Interelectricos Group SAS',
            'Proyecto': 'Sistema de Bonificaciones en Bodega',
            'Destinatarios': 'Despachadores, Auxiliares de Bodega y Supervisión',
            'Software': 'AppSheet PWA + Bot WhatsApp IA + Google Sheets',
            'Autor': 'Mauricio Sierra — Aprendiz ADSO SENA',
            'Versión / Fecha': 'Versión 2.1 (Producción) | Octubre de 2026'
        },
        short_title='Manual de Usuario Operativo',
        is_formal_report=True
    )

    # 2. Informe Técnico y Manual de Configuración
    parse_and_compile(
        md_filepath='docs/INFORME_TECNICO_Y_MANUAL_DE_CONFIGURACION.md',
        docx_outpath='docs/INFORME_TECNICO_Y_MANUAL_DE_CONFIGURACION.docx',
        doc_title='INFORME TÉCNICO Y MANUAL DE CONFIGURACIÓN',
        doc_subtitle='Arquitectura de Datos, Fórmulas de Liquidación, AppSheet y Bot Serverless IA',
        metadata={
            'Empresa': 'Interelectricos Group SAS',
            'Proyecto': 'Sistema de Bonificaciones en Bodega',
            'Destinatarios': 'Dirección de Operaciones, TI y Auditoría',
            'Software': 'AppSheet PWA + Bot Vercel/Gemini + Google Sheets',
            'Autor': 'Mauricio Sierra — Aprendiz ADSO SENA',
            'Versión / Fecha': 'Versión 2.1 (Producción) | Octubre de 2026'
        },
        short_title='Informe Técnico y Manual de Configuración',
        is_formal_report=True
    )

    # 3. Configuración Técnica de AppSheet
    parse_and_compile(
        md_filepath='schemas/appsheet_config.md',
        docx_outpath='docs/CONFIGURACION_TECNICA_APPSHEET.docx',
        doc_title='CONFIGURACIÓN TÉCNICA DE APPSHEET',
        doc_subtitle='Guía de Configuración Paso a Paso de Tablas, Columnas, Vistas y Reglas (V2.1)',
        metadata={
            'Empresa': 'Interelectricos Group SAS',
            'Proyecto': 'Sistema de Bonificaciones en Bodega',
            'Destinatarios': 'Equipo de Sistemas y Desarrolladores AppSheet',
            'Software': 'Motor AppSheet Core Engine',
            'Autor': 'Mauricio Sierra — Aprendiz ADSO SENA',
            'Versión / Fecha': 'Versión 2.1 (Producción) | Octubre de 2026'
        },
        short_title='Configuración Técnica AppSheet',
        is_formal_report=True
    )

    # 4. Runbook de Soporte Técnico
    parse_and_compile(
        md_filepath='docs/RUNBOOK_SOPORTE_TECNICO.md',
        docx_outpath='docs/RUNBOOK_SOPORTE_TECNICO.docx',
        doc_title='RUNBOOK DE SOPORTE TÉCNICO',
        doc_subtitle='Diagnóstico de Incidencias, Mantenimiento Operativo y Contingencia (V2.1)',
        metadata={
            'Empresa': 'Interelectricos Group SAS',
            'Proyecto': 'Sistema de Bonificaciones en Bodega',
            'Destinatarios': 'Equipo de Soporte Técnico, TI y Operaciones',
            'Software': 'AppSheet PWA + Bot Vercel/Gemini + Google Sheets',
            'Autor': 'Mauricio Sierra — Aprendiz ADSO SENA',
            'Versión / Fecha': 'Versión 2.1 (Producción) | Octubre de 2026'
        },
        short_title='Runbook Soporte Técnico',
        is_formal_report=True
    )
