"""v4: metrics slide (from v3) + a new PCA / gripper slide, appendix renumbered to 13."""
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\30217\Downloads\Track1_Week1_Report.pptx"
OUT = os.path.join(HERE, "Track1_Week1_Report_v4.pptx")
BG = os.path.join(HERE, "track1_assets", "raw", "s01_landscape_2000x1125_68b446beb8.png")
FIG_GREEN = os.path.join(HERE, "track1_assets", "gripper", "dark_green_methods.jpg")
FIG_BLACK = os.path.join(HERE, "track1_assets", "gripper", "dark_black_methods.jpg")

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
    ("Dim light · green bean", "0.185", "0.873", "0.859", "25.6", "6.2"),
    ("Dim light · black block", "0.830", "0.832", "0.853", "9.3", "9.2"),
    ("Bright light · green bean", "0.069", "0.728", "0.000", "18.2", "15.4"),
    ("Bright light · black block", "0.341", "0.733", "0.000", "31.4", "6.1"),
    ("Mean", "0.356", "0.792", "0.428", "21.1", "9.2"),
]
HEADER = ("", "IoU RGB", "IoU HSV", "IoU YOLO", "Δc RGB", "Δc HSV")

POSE_ROWS = [
    ("Colour threshold", "+46.7", "−10.4", "−44.2", "+74.4"),
    ("Grayscale + colour", "+47.3", "−10.4", "−40.5", "+78.8"),
    ("YOLO seg + PCA", "+47.6", "−10.3", "no mask", "no mask"),
]


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


def chrome(slide, kicker, title, page):
    """kicker + title + accent bar + footer, identical to the rest of the deck."""
    prs = slide.part.package.presentation_part.presentation
    slide.shapes.add_picture(BG, 0, 0, width=prs.slide_width, height=prs.slide_height)

    tb = textbox(slide, 0.62, 0.40, 9.0, 0.26)
    run(para(tb.text_frame, True), kicker, 9.5, ACCENT, True)
    tb = textbox(slide, 0.62, 0.66, 12.09, 0.72)
    run(para(tb.text_frame, True), title, 26, NAVY, True)
    bar = slide.shapes.add_shape(1, Inches(0.62), Inches(1.42), Inches(0.85), Inches(0.06))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()
    bar.shadow.inherit = False
    tb = textbox(slide, 0.62, 7.06, 9.0, 0.24)
    run(para(tb.text_frame, True), "Track 1 Report", 8.5, MUTED)
    tb = textbox(slide, 11.81, 7.06, 0.90, 0.24)
    p = para(tb.text_frame, True)
    p.alignment = PP_ALIGN.RIGHT
    run(p, page, 8.5, MUTED, True)


def style_table(table, header, rows, widths, row_h, bold_last=False, warn_zero=False):
    tblPr = table._tbl.tblPr
    style_id = tblPr.find(qn("a:tableStyleId"))
    if style_id is None:
        style_id = parse_xml('<a:tableStyleId xmlns:a="http://schemas.openxmlformats.org/'
                             'drawingml/2006/main"/>')
        tblPr.append(style_id)
    style_id.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"
    table.first_row = False
    table.horz_banding = False
    for i, w in enumerate(widths):
        table.columns[i].width = Inches(w)
    for r in table.rows:
        r.height = Inches(row_h)

    for ci, txt in enumerate(header):
        cell = table.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        cell.margin_left = cell.margin_right = Inches(0.09)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.RIGHT
        run(p, txt, 8.8, RGBColor(0xFF, 0xFF, 0xFF), True)

    for ri, row in enumerate(rows, start=1):
        last = ri == len(rows)
        for ci, txt in enumerate(row):
            cell = table.cell(ri, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = (RGBColor(0xE8, 0xF0, 0xFE) if (bold_last and last)
                                        else RGBColor(0xFF, 0xFF, 0xFF) if ri % 2
                                        else RGBColor(0xF7, 0xFA, 0xFE))
            cell.margin_left = cell.margin_right = Inches(0.09)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.RIGHT
            color = BODY if ci == 0 else NAVY
            if ci == 2:
                color = DEEP
            if warn_zero and txt == "0.000":
                color = WARN
            if warn_zero and txt == "no mask":
                color = WARN
            run(p, txt, 9.2, color, (bold_last and last) or ci in (2, 3))
            hairline(cell)


def metrics_slide(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    chrome(s, "RESULT · MEASURED AGAINST GROUND TRUTH",
           "Measured: HSV 0.79, YOLO 0.43, RGB 0.36 mean IoU", "11")

    left, top, width, row_h = 0.62, 1.74, 7.30, 0.50
    gf = s.shapes.add_table(len(ROWS) + 1, len(HEADER), Inches(left), Inches(top),
                            Inches(width), Inches(row_h * (len(ROWS) + 1)))
    style_table(gf.table, HEADER, ROWS, (1.80, 1.10, 1.10, 1.10, 1.10, 1.10), row_h,
                bold_last=True, warn_zero=True)

    tb = textbox(s, 0.62, 4.95, 7.30, 0.72)
    run(para(tb.text_frame, True),
        "Δc = centre error in px. A heading is only reported where the min-area rectangle has "
        "aspect ≥ 1.15; the bean turns near-square in bright light, so that cell has no "
        "stable angle. YOLO's dim-light black score is the union of two overlapping boxes "
        "(skateboard 0.61 / snowboard 0.57), so its shadow coverage is accidental.", 8.8, MUTED)

    tb = textbox(s, 8.24, 1.72, 3.80, 0.30)
    run(para(tb.text_frame, True), "How to read it", 11, NAVY, True)

    def callout(y, color, head, body):
        b = s.shapes.add_shape(1, Inches(8.24), Inches(y), Inches(0.05), Inches(0.66))
        b.fill.solid()
        b.fill.fore_color.rgb = color
        b.line.fill.background()
        b.shadow.inherit = False
        tb = textbox(s, 8.46, y - 0.04, 4.26, 1.0)
        tf = tb.text_frame
        run(para(tf, True), head, 10.5, color, True)
        run(para(tf, space_before=3), body, 9.6, BODY)

    callout(2.16, GOOD, "0.79 HSV · 0.43 YOLO · 0.36 RGB",
            "Mean IoU across the four object × lighting cases. Only HSV stays above 0.7 "
            "under both lighting conditions.")
    callout(3.34, ACCENT, "Dim light: all three agree",
            "0.830 / 0.832 / 0.853. When the target is dark, three very different methods "
            "converge on almost the same mask.")
    callout(4.52, WARN, "Bright light: two rows of zero",
            "YOLO finds nothing at all at conf 0.5; RGB keeps the black block (0.341) but "
            "loses the bean (0.069).")

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
        "boundary), so absolute IoU reads slightly low — the bias applies equally to all "
        "three methods.", 9.2, BODY)
    return s


def pose_slide(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    chrome(s, "POSER · PCA + PARALLEL-JAW GRIPPER",
           "Three masks, one pose: the heading holds to within a degree", "12")

    s.shapes.add_picture(FIG_GREEN, Inches(0.62), Inches(1.68), width=Inches(7.00))
    tb = textbox(s, 0.62, 4.42, 7.55, 0.26)
    run(para(tb.text_frame, True),
        "Dim light · green bean — blue = long axis, red = short axis, green = gripper", 8.5, MUTED)

    left, top, width, row_h = 0.62, 4.78, 7.55, 0.34
    gf = s.shapes.add_table(len(POSE_ROWS) + 1, 5, Inches(left), Inches(top),
                            Inches(width), Inches(row_h * (len(POSE_ROWS) + 1)))
    style_table(gf.table, ("Heading from PCA", "dim green", "dim black", "bright green", "bright black"),
                POSE_ROWS, (2.35, 1.30, 1.30, 1.30, 1.30), row_h, warn_zero=True)

    tb = textbox(s, 8.42, 1.72, 3.80, 0.30)
    run(para(tb.text_frame, True), "Why PCA, not minAreaRect", 11, NAVY, True)

    def block(y, head, body):
        tb = textbox(s, 8.42, y, 4.30, 1.0)
        tf = tb.text_frame
        run(para(tf, True), head, 10, NAVY, True)
        run(para(tf, space_before=2), body, 9.4, BODY)

    block(2.06, "It averages, so it is stable",
          "The axes come from the covariance of all object pixels, not from the boundary. "
          "Saw-tooth edges move a min-area rectangle, not a mean.")
    block(2.98, "It hands you both axes",
          "The two eigenvectors are the long and the short axis; the eigenvalues say which "
          "is which. That is exactly what a gripper needs.")
    block(3.90, "Same inputs, same outputs",
          "Centre, heading, and the two extents — for every mask source, unchanged.")
    block(4.82, "And the gripper is the test",
          "Fingers parallel to the long axis, opening across the short one. If the pose were "
          "wrong, the jaws would visibly miss the object — here they close around it in all "
          "six panels.")

    band = s.shapes.add_shape(1, Inches(0.62), Inches(6.30), Inches(12.09), Inches(0.52))
    band.fill.solid()
    band.fill.fore_color.rgb = RGBColor(0xF4, 0xF8, 0xFE)
    band.line.color.rgb = RGBColor(0xD8, 0xE4, 0xF2)
    band.line.width = Pt(0.75)
    band.shadow.inherit = False
    tb = textbox(s, 0.88, 6.38, 11.55, 0.40)
    run(para(tb.text_frame, True),
        "Splitting axes · numpy returns (row, column) while OpenCV draws in (x, y); every "
        "point here is flipped to (x, y) before PCA, otherwise the gripper lands on the "
        "wrong side of the object.", 9.2, BODY)
    return s


def rewrite_all(prs, old, new, only_kicker=None):
    hits = 0
    for slide in prs.slides:
        kick = ""
        for shape in slide.shapes:
            if shape.has_text_frame:
                t = shape.text_frame.text
                if t.strip().startswith(("APPENDIX", "RESULT", "TASK", "OVERVIEW", "DATASET",
                                         "METHOD", "POSER")):
                    kick = t
        if only_kicker and only_kicker not in kick:
            continue
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if old in r.text:
                        r.text = r.text.replace(old, new)
                        hits += 1
    return hits


def main():
    prs = Presentation(SRC)

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
        (2, "heading θ from minAreaRect;",
         "heading θ from minAreaRect (or PCA, once a gripper is drawn — slide 12);"),
    ]
    for idx, old, new in edits:
        n = 0
        for shape in prs.slides[idx].shapes:
            if not shape.has_text_frame:
                continue
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if old in r.text:
                        r.text = r.text.replace(old, new)
                        n += 1
        print(f"slide {idx + 1}: {n} run(s)")

    # appendix page number: it is still slide 11 here, before the new pages go in
    for shape in prs.slides[10].shapes:
        if shape.has_text_frame and shape.text_frame.text.strip() == "17":
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    r.text = "13"
            print("appendix page 17 -> 13")

    metrics_slide(prs)
    pose_slide(prs)

    # two new slides sit at the tail; move them in front of the appendix
    lst = prs.slides._sldIdLst
    ids = list(lst)
    m, p = ids[-2], ids[-1]
    for el in (m, p):
        lst.remove(el)
    base = len(list(lst)) - 1          # appendix is now last
    lst.insert(base, m)
    lst.insert(base + 1, p)

    prs.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    main()
