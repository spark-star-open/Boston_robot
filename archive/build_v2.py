"""Insert a measured-results slide and reconcile the numbers in slides 08-09."""
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\30217\Downloads\Track1_Week1_Report.pptx"
OUT = os.path.join(HERE, "Track1_Week1_Report_v2.pptx")
BG = os.path.join(HERE, "track1_assets", "raw", "s01_landscape_2000x1125_68b446beb8.png")

NAVY = RGBColor(0x0F, 0x25, 0x44)
BODY = RGBColor(0x33, 0x46, 0x5E)
MUTED = RGBColor(0x6E, 0x80, 0x95)
ACCENT = RGBColor(0x2F, 0x6F, 0xED)
GOOD = RGBColor(0x1F, 0x9D, 0x55)
WARN = RGBColor(0xB2, 0x6A, 0x12)
DEEP = RGBColor(0x15, 0x7A, 0x43)
BORDER = "D8E4F2"
FONT = "Microsoft YaHei"

ROWS = [
    ("Dim light · green bean", "0.185", "0.873", "25.6", "6.2"),
    ("Dim light · black block", "0.830", "0.832", "9.3", "9.2"),
    ("Bright light · green bean", "0.069", "0.728", "18.2", "15.4"),
    ("Bright light · black block", "0.341", "0.733", "31.4", "6.1"),
    ("Mean", "0.356", "0.792", "21.1", "9.2"),
]
HEADER = ("", "IoU RGB", "IoU HSV", "Δc RGB", "Δc HSV")


def textbox(slide, x, y, w, h):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    return tb


def para(tf, first=False, space_before=0):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.space_before = Pt(space_before)
    return p


def run(p, text, size, color, bold=False):
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.name = FONT
    r.font.color.rgb = color
    return r


def hairline(cell, color=BORDER):
    tcPr = cell._tc.get_or_add_tcPr()
    ln = parse_xml(
        '<a:lnB xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'w="9525" cap="flat" cmpd="sng" algn="ctr">'
        '<a:solidFill><a:srgbClr val="' + color + '"/></a:solidFill>'
        '<a:prstDash val="solid"/></a:lnB>')
    tcPr.insert(0, ln)


def main():
    prs = Presentation(SRC)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.shapes.add_picture(BG, 0, 0, width=prs.slide_width, height=prs.slide_height)

    tb = textbox(s, 0.62, 0.40, 9.0, 0.26)
    run(para(tb.text_frame, True), "RESULT · MEASURED AGAINST GROUND TRUTH", 9.5, ACCENT, True)

    tb = textbox(s, 0.62, 0.66, 12.09, 0.72)
    run(para(tb.text_frame, True), "Same pipeline, measured: 0.79 vs 0.36 mean IoU", 26, NAVY, True)

    bar = s.shapes.add_shape(1, Inches(0.62), Inches(1.42), Inches(0.85), Inches(0.06))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()
    bar.shadow.inherit = False

    tb = textbox(s, 0.62, 7.06, 9.0, 0.24)
    run(para(tb.text_frame, True), "Track 1 Report", 8.5, MUTED)
    tb = textbox(s, 11.81, 7.06, 0.90, 0.24)
    p = para(tb.text_frame, True)
    p.alignment = PP_ALIGN.RIGHT
    run(p, "11", 8.5, MUTED, True)

    # ---------------- table ----------------
    left, top, width = 0.62, 1.74, 7.30
    row_h = 0.50
    gf = s.shapes.add_table(len(ROWS) + 1, 5, Inches(left), Inches(top),
                            Inches(width), Inches(row_h * (len(ROWS) + 1)))
    table = gf.table
    tblPr = table._tbl.tblPr
    style_id = tblPr.find(qn("a:tableStyleId"))
    if style_id is None:
        style_id = parse_xml('<a:tableStyleId xmlns:a="http://schemas.openxmlformats.org/'
                             'drawingml/2006/main"/>')
        tblPr.append(style_id)
    style_id.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"
    table.first_row = False
    table.horz_banding = False

    for i, w in enumerate((2.05, 1.32, 1.32, 1.30, 1.31)):
        table.columns[i].width = Inches(w)
    for r in table.rows:
        r.height = Inches(row_h)

    for ci, txt in enumerate(HEADER):
        cell = table.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        cell.margin_left = Inches(0.10)
        cell.margin_right = Inches(0.10)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.RIGHT
        run(p, txt, 9, RGBColor(0xFF, 0xFF, 0xFF), True)

    for ri, row in enumerate(ROWS, start=1):
        is_mean = row[0] == "Mean"
        for ci, txt in enumerate(row):
            cell = table.cell(ri, ci)
            cell.fill.solid()
            if is_mean:
                cell.fill.fore_color.rgb = RGBColor(0xE8, 0xF0, 0xFE)
            else:
                cell.fill.fore_color.rgb = (RGBColor(0xFF, 0xFF, 0xFF) if ri % 2
                                            else RGBColor(0xF7, 0xFA, 0xFE))
            cell.margin_left = Inches(0.10)
            cell.margin_right = Inches(0.10)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.RIGHT
            color = BODY if ci == 0 else NAVY
            if ci == 2:
                color = DEEP
            run(p, txt, 9.5, color, is_mean or ci == 2)
            hairline(cell)

    tb = textbox(s, 0.62, 4.95, 7.30, 0.72)
    tf = tb.text_frame
    run(para(tf, True),
        "Δc = centre error in px. A heading is only reported where the min-area rectangle has "
        "aspect ≥ 1.15; the bean turns near-square in bright light, so that cell has no "
        "stable angle.", 8.8, MUTED)

    # ---------------- callouts ----------------
    tb = textbox(s, 8.24, 1.72, 3.80, 0.30)
    run(para(tb.text_frame, True), "How to read it", 11, NAVY, True)

    def callout(y, color, head, body):
        b = s.shapes.add_shape(1, Inches(8.24), Inches(y), Inches(0.05), Inches(0.92))
        b.fill.solid()
        b.fill.fore_color.rgb = color
        b.line.fill.background()
        b.shadow.inherit = False
        tb = textbox(s, 8.46, y - 0.04, 4.26, 1.0)
        tf = tb.text_frame
        run(para(tf, True), head, 10.5, color, True)
        run(para(tf, space_before=3), body, 9.6, BODY)

    callout(2.16, GOOD, "0.79 vs 0.36 mean IoU",
            "RGB only keeps up where the target is dark. On the green bean it collapses to "
            "0.185 in dim light and 0.069 in bright light.")
    callout(3.34, ACCENT, "Dim light is a dead heat",
            "Black block: 0.830 RGB vs 0.832 HSV. In dim light \u201cBGR < 60\u201d and "
            "\u201cV < 70\u201d are effectively the same test.")
    callout(4.52, WARN, "Bright light is where it breaks",
            "Black block 0.341 with the centre 31 px off, and three fragments whose headings "
            "disagree by up to 75°.")

    # ---------------- method band ----------------
    band = s.shapes.add_shape(1, Inches(0.62), Inches(5.92), Inches(12.09), Inches(0.62))
    band.fill.solid()
    band.fill.fore_color.rgb = RGBColor(0xF4, 0xF8, 0xFE)
    band.line.color.rgb = RGBColor(0xD8, 0xE4, 0xF2)
    band.line.width = Pt(0.75)
    band.shadow.inherit = False
    tb = textbox(s, 0.88, 6.02, 11.55, 0.44)
    run(para(tb.text_frame, True),
        "Method note · one re-run of the pipeline printed on slides 05–06, on the same two "
        "photos; ground truth is semi-automatic (GrabCut from a hand-drawn box, ±5–10 % "
        "boundary), so absolute IoU reads slightly low — the bias applies equally to both "
        "methods.", 9.2, BODY)

    # ---------------- move before the appendix ----------------
    sldIdLst = prs.slides._sldIdLst
    ids = list(sldIdLst)
    sldIdLst.remove(ids[-1])
    sldIdLst.insert(len(ids) - 2, ids[-1])

    # ---------------- reconcile text ----------------
    def rewrite(idx, old, new):
        hits = 0
        for shape in prs.slides[idx].shapes:
            if not shape.has_text_frame:
                continue
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if old in r.text:
                        r.text = r.text.replace(old, new)
                        hits += 1
        return hits

    edits = [
        (1, "HSV clearly beats RGB in this scene",
            "HSV averages 0.79 IoU against 0.36 for RGB in this scene"),
        (7, "4,622 px", "4,191 px"),
        (7, "41,463 / 951 / 330 px, angles −8.9° / −55.5° / −79.3° — mutually contradictory.",
            "20,104 / 1,332 / 691 px, headings up to 75° apart — mutually contradictory."),
        (7, "2,630 px, about 1/7 of the HSV result.",
            "1,831 px, about 1/11 of the HSV result (IoU 0.069)."),
        (8, "(20,988 / 19,385 px)", "(20,987 / 19,410 px)"),
        (8, "in bright light it turns near-square and the angle degenerates to −90.0°.",
            "in bright light the aspect ratio falls to 1.17, so the heading is no longer defined."),
        (11, "17", "12"),
    ]
    for idx, old, new in edits:
        print(f"slide {idx + 1}: {rewrite(idx, old, new)} run(s) <- {old[:46]!r}")

    prs.save(OUT)
    print("\nsaved:", OUT)


if __name__ == "__main__":
    main()
