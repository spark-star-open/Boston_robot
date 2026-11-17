"""Build the Word record: the code that produced the numbers, plus the deck edits."""
import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Track1_代码与改动说明.docx")

NAVY = RGBColor(0x0F, 0x25, 0x44)
BLUE = RGBColor(0x2F, 0x6F, 0xED)
GREY = RGBColor(0x6E, 0x80, 0x95)
BODY = RGBColor(0x33, 0x46, 0x5E)
CODE_BG = "F5F7FA"
HEAD_BG = "0F2544"
ALT_BG = "F7FAFE"

CN = "Microsoft YaHei"
MONO = "Consolas"


# ---------------------------------------------------------------- helpers
def set_run(run, size=10.5, bold=False, color=BODY, font=CN, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), font)
    rfonts.set(qn("w:hAnsi"), font)
    rfonts.set(qn("w:eastAsia"), CN)


def shade(element, fill):
    pr = element.get_or_add_tcPr() if hasattr(element, "get_or_add_tcPr") else None
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    if pr is not None:
        pr.append(shd)
    return shd


def shade_paragraph(paragraph, fill=CODE_BG):
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def para(doc, text="", size=10.5, bold=False, color=BODY, before=0, after=4,
         align=None, line=1.35, font=CN):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line
    if align is not None:
        p.alignment = align
    if text:
        set_run(p.add_run(text), size, bold, color, font)
    return p


def heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16 if level == 1 else 12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    size = 15 if level == 1 else 11.5
    color = NAVY if level == 1 else BLUE
    set_run(p.add_run(text), size, True, color)
    if level == 1:
        pPr = p._p.get_or_add_pPr()
        bdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "8")
        bottom.set(qn("w:space"), "4")
        bottom.set(qn("w:color"), "D8E4F2")
        bdr.append(bottom)
        pPr.append(bdr)
    return p


def code_block(doc, source, size=8.0):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.left_indent = Cm(0.25)
    shade_paragraph(p)
    lines = source.replace("\t", "    ").rstrip("\n").split("\n")
    for i, line in enumerate(lines):
        r = p.add_run(line if line else " ")
        r.font.size = Pt(size)
        r.font.name = MONO
        rpr = r._element.get_or_add_rPr()
        rfonts = OxmlElement("w:rFonts")
        rfonts.set(qn("w:ascii"), MONO)
        rfonts.set(qn("w:hAnsi"), MONO)
        rfonts.set(qn("w:eastAsia"), CN)
        rpr.append(rfonts)
        if i < len(lines) - 1:
            r.add_break()
    return p


def table(doc, header, rows, widths=None, size=9.2, align_right=(), bold_last=False):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    hdr = t.rows[0].cells
    for i, txt in enumerate(header):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        set_run(p.add_run(txt), size, True, RGBColor(0xFF, 0xFF, 0xFF))
        shade_cell(hdr[i], HEAD_BG)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for ci, txt in enumerate(row):
            cells[ci].text = ""
            p = cells[ci].paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            if ci in align_right:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            bold = bold_last and ri == len(rows) - 1
            color = NAVY if bold else BODY
            set_run(p.add_run(str(txt)), size, bold, color)
            if ri % 2 == 1:
                shade_cell(cells[ci], ALT_BG)
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
    hdrPr = t.rows[0]._tr.get_or_add_trPr()
    hdrPr.append(OxmlElement("w:tblHeader"))

    if widths:
        for row in t.rows:
            for ci, w in enumerate(widths):
                row.cells[ci].width = Cm(w)
        grid = t._tbl.find(qn("w:tblGrid"))
        if grid is not None:
            for ci, gc in enumerate(grid.findall(qn("w:gridCol"))):
                if ci < len(widths):
                    gc.set(qn("w:w"), str(int(widths[ci] * 567)))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def add_page_number_footer(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("Track 1 · 代码与改动说明   ·   "), 8.5, False, GREY)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "17")
    rpr.append(sz)
    r.append(rpr)
    t = OxmlElement("w:t"); t.text = "1"
    r.append(t)
    fld.append(r)
    p._p.append(fld)


# ---------------------------------------------------------------- content
def section_overview(doc):
    heading(doc, "一、这份文档是什么", 1)
    para(doc,
         "记录 2026-11-12 这一天对 Track 1 周报做的全部技术工作：我为验证与补全数据写了哪些脚本、"
         "改动了 PPT 的哪几处、每一处改动的依据是什么。所有数字都可以用文末的步骤原样复现。")

    table(doc,
          ["项目", "内容"],
          [["源文件", "Downloads\\Track1_Week1_Report.pptx（11 页，未改动）"],
           ["交付文件", "Track1_Week1_Report_v3.pptx（12 页）"],
           ["核心结论", "HSV 平均 IoU 0.792，YOLO 0.428，RGB 0.356；YOLO 的失败是二值的"],
           ["验证方式", "用 PPT 第 5、6 页印出的参数重跑两条基线，再用同一张真值打分"],
           ["真值来源", "GrabCut 半自动标注（人工拖框 + 自动细化），4 个目标"],
           ["代码量", "7 个脚本，约 820 行（第 7 个 build_v3.py 放在附录）"]],
          widths=[3.4, 13.2])

    heading(doc, "二、环境与依赖", 1)
    table(doc,
          ["解释器", "用途", "关键包"],
          [["D:\\python\\python.exe（3.14.8）", "图像处理、指标计算、YOLO 推理",
            "numpy 2.5.3 / opencv-python 5.0.0.93 / ultralytics 8.4.211 / torch 2.14.1 / torchvision 0.29.2"],
           ["DSH 内置 Python（3.x）", "读写 PPTX、生成 Word",
            "python-pptx 1.0.2 / lxml / Pillow"]],
          widths=[4.6, 4.6, 7.4], size=8.8)
    para(doc,
         "注意：python-pptx 只装在 DSH 内置运行时里，D:\\python 里没有。若要自己重建 PPT，"
         "需先执行 pip install python-pptx，之后所有脚本可统一用 D:\\python\\python.exe 运行。",
         size=9.5, color=GREY)

    heading(doc, "三、脚本清单", 1)
    table(doc,
          ["脚本", "行数", "作用", "产出"],
          [["extract_media.py", "35", "拆 PPTX 内嵌图，按页号+尺寸+哈希命名", "track1_assets/raw/ 共 11 张"],
           ["repro_rgb_hsv.py", "108", "按第 5、6 页参数重跑 BGR 与 HSV 流水线", "repro/*_mask.png、components.json"],
           ["label_gt.py", "135", "拖框 + GrabCut 生成真值掩码", "gt/*.png、boxes.json"],
           ["metrics.py", "130", "算 IoU、中心误差、角度误差", "终端表格"],
           ["yolo_masks.py", "95", "下载权重并跑 YOLOv8n-seg", "yolo/ 掩码与叠加图"],
           ["yolo_assign.py", "73", "把检测框归到绿/黑目标", "repro/*_yolo_*.png"]],
          widths=[3.6, 1.4, 7.4, 4.6], size=8.8, align_right=(1,))


def section_code(doc):
    heading(doc, "四、代码全文", 1)
    para(doc, "以下为实际运行过的源码，未做删改。文件均位于工作目录下。", size=9.5, color=GREY)

    items = [
        ("1. extract_media.py", "从 PPTX 里取出原始图片。关键点：Shape.image.blob 拿到的是嵌入的原始字节，"
                                "不是被裁剪或缩放的版本，所以两张手机原图能恢复到 1024×1460 与 1444×1024。",
         "extract_media.py"),
        ("2. repro_rgb_hsv.py", "按第 5 页的 BGR_RANGES 与第 6 页的 HSV_RANGES 重跑，流程与 PPT 完全一致："
                                "inRange → 5×5 开 → 5×5 闭 → RETR_EXTERNAL → 面积≥300 → minAreaRect。"
                                "顺带处理了 Windows 上 cv2.imread 读不了中文路径的问题。",
         "repro_rgb_hsv.py"),
        ("3. label_gt.py", "交互式标注：鼠标拖一个粗框，GrabCut 迭代 5 次细化，只保留最大连通域，回车存成 PNG。"
                           "支持 python label_gt.py dark_green 只重标单个目标。",
         "label_gt.py"),
        ("4. metrics.py", "对每个「图像 × 目标 × 方法」算三个数：掩码 IoU、质心距离（px）、长边朝向差（°）。"
                          "朝向按 minAreaRect 的长边取值；长宽比小于 1.15 时判为近方形，角度记为 n/a。",
         "metrics.py"),
        ("5. yolo_masks.py", "下载 yolov8n-seg.pt（先直连，失败自动切到本地 7890 代理），以 conf=0.5 推理两张图，"
                             "用 masks.xy 的原始图坐标画掩码，避开 letterbox 还原的坑。",
         "yolo_masks.py"),
        ("6. yolo_assign.py", "一个图里可能有多框（暗光下黑块被同时认成 skateboard 和 snowboard），"
                              "按与真值的重叠面积把每个框归给绿或黑，再取并集。没有检出的目标写全零掩码——这就是 0.000 的来源。",
         "yolo_assign.py"),
    ]
    for title, note, fname in items:
        heading(doc, title, 2)
        para(doc, note, size=9.5)
        src = open(os.path.join(HERE, fname), encoding="utf-8-sig").read()
        code_block(doc, src)


def section_deck_edits(doc):
    heading(doc, "五、PPT 改了什么", 1)
    para(doc, "全篇共 11 页，改动范围是：新增 1 页、改写 6 句、修 1 个页码。其余内容、图片、版式、"
              "演讲者备注均未触碰。", size=10)

    heading(doc, "5.1 结构变化", 2)
    table(doc,
          ["项", "改动前", "改动后"],
          [["页数", "11", "12"],
           ["新增页位置", "—", "第 11 页（在 YOLO 结果页之后、附录之前）"],
           ["附录位置", "第 11 页", "第 12 页"],
           ["附录页码", "17（串号）", "12"],
           ["其余页脚", "02–10", "02–10（不变）"]],
          widths=[3.6, 5.0, 8.4], size=9.0)

    heading(doc, "5.2 六处文字改动", 2)
    table(doc,
          ["页", "原文", "改为", "依据"],
          [["02",
            "HSV clearly beats RGB in this scene",
            "HSV averages 0.79 IoU against 0.36 for RGB in this scene",
            "把定性主张换成实测均值"],
           ["08", "…(4,622 px)", "…(4,191 px)", "复现值"],
           ["08",
            "41,463 / 951 / 330 px, angles −8.9° / −55.5° / −79.3° — mutually contradictory",
            "20,104 / 1,332 / 691 px, headings up to 75° apart — mutually contradictory",
            "面积用复现值；三个负角是旧版 OpenCV 角度约定的产物，改为不受约定影响的「相差 75°」"],
           ["08",
            "2,630 px, about 1/7 of the HSV result",
            "1,831 px, about 1/11 of the HSV result (IoU 0.069)",
            "复现值，并补一个 IoU"],
           ["09", "(20,988 / 19,385 px)", "(20,987 / 19,410 px)", "复现值"],
           ["09",
            "…turns near-square and the angle degenerates to −90.0°",
            "…the aspect ratio falls to 1.17, so the heading is no longer defined",
            "长宽比是量出来的；−90° 是旧角度约定的产物"]] ,
          widths=[1.2, 6.0, 6.0, 4.4], size=8.4)

    heading(doc, "5.3 新增的第 11 页", 2)
    table(doc,
          ["区块", "内容"],
          [["眉题", "RESULT · MEASURED AGAINST GROUND TRUTH"],
           ["标题", "Measured: HSV 0.79, YOLO 0.43, RGB 0.36 mean IoU"],
           ["表格", "5 行数据 + 1 行均值；列：IoU RGB / IoU HSV / IoU YOLO / Δc RGB / Δc HSV"],
           ["表下注", "Δc 定义；角度仅在长宽比 ≥1.15 时报告；YOLO 暗光黑块得分是两框并集"],
           ["右侧三条", "均值对比 / 暗光三家打平 / 亮光两行 0.000"],
           ["底部说明", "一次重跑同一套参数；真值为 GrabCut 半自动标注，±5–10% 边界误差"]],
          widths=[3.2, 13.4], size=9.0)
    para(doc,
         "版式沿用原 deck：同一张背景图、Microsoft YaHei、标题 26pt / 眉题 9.5pt、"
         "主蓝 2F6FED、深藏青 0F2544、卡片边 D8E4F2、好绿 1F9D55、警示琥珀 B26A12。",
         size=9.5, color=GREY)

    heading(doc, "5.4 刻意没改的地方", 2)
    for txt in [
        "封面、第 3/4/5/6/7 页（总览、数据集、三个方法页）——写的是方法与参数，与重跑用的完全一致。",
        "第 9 页「the box swallows the cast shadow and drags the angle to −12.4° / −13.5°, a few degrees off the true heading」"
        "——我们的真值也把阴影包了进去，测不出黑块的真实朝向，改了等于用一个不可靠的数替换另一个。",
        "第 10 页 YOLO 结果页——版面已排满，且该页三个检出（0.77 / 0.61 / 0.57）复现结果一字不差，本来就没写错。",
        "所有图片、演讲者备注、版式与动画。",
    ]:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(4)
        set_run(p.add_run(txt), 9.8)


def section_numbers(doc):
    heading(doc, "六、实测数据", 1)
    table(doc,
          ["图像 · 目标", "IoU RGB", "IoU HSV", "IoU YOLO", "Δc RGB", "Δc HSV"],
          [["暗光 · 绿软糖", "0.185", "0.873", "0.859", "25.6", "6.2"],
           ["暗光 · 黑块", "0.830", "0.832", "0.853", "9.3", "9.2"],
           ["亮光 · 绿软糖", "0.069", "0.728", "0.000", "18.2", "15.4"],
           ["亮光 · 黑块", "0.341", "0.733", "0.000", "31.4", "6.1"],
           ["均值", "0.356", "0.792", "0.428", "21.1", "9.2"]],
          widths=[4.4, 2.6, 2.6, 2.8, 2.2, 2.2], size=9.4, align_right=(1, 2, 3, 4, 5), bold_last=True)

    heading(doc, "读数", 2)
    for txt in [
        "HSV 在四种情形里都稳在 0.72 以上，是唯一两种光照都不掉的方法。",
        "暗光下三种方法几乎重合（0.830 / 0.832 / 0.853）：目标本身就暗时，「BGR<60」「V<70」和「模型认出来」殊途同归。",
        "YOLO 的失败是二值的：亮光下 conf=0.5 一个检出都没有，直接交白卷，而不是给一个偏差大的答案。",
        "YOLO 暗光黑块的 0.853 略高于 HSV 0.832，是两个重叠框（skateboard 0.61 / snowboard 0.57）取并集后多盖了阴影，属于偶然得分。",
        "RGB 亮光黑块只有 0.341、绿软糖 0.069，且中心偏 18–31 px，是渐变式失效。",
    ]:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(4)
        set_run(p.add_run(txt), 9.8)


def section_repro(doc):
    heading(doc, "七、复现步骤", 1)
    steps = [
        ("拆图", "python extract_media.py  →  track1_assets/raw/ 出现 11 张图"),
        ("重跑基线", "python repro_rgb_hsv.py  →  repro/ 出现 12 张掩码与 components.json"),
        ("标真值", "python label_gt.py  →  拖 4 个框，gt/ 出现 4 张 PNG"),
        ("算指标", "python metrics.py  →  终端打印六列表格"),
        ("跑 YOLO", "python yolo_masks.py  →  下载权重并推理，yolo/ 出现叠加图"),
        ("归框", "python yolo_assign.py  →  repro/ 补上 yolo 掩码"),
        ("看三方法", "python metrics.py --methods rgb,hsv,yolo  →  得到终版表格"),
        ("重建 PPT", "python build_v3.py（需 python-pptx）→  Track1_Week1_Report_v3.pptx"),
    ]
    for i, (name, cmd) in enumerate(steps, 1):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        set_run(p.add_run(f"{i}. {name}　"), 9.8, True, NAVY)
        set_run(p.add_run(cmd), 9.2, False, BODY, MONO)


def section_issues(doc):
    heading(doc, "八、已知问题与待办", 1)
    table(doc,
          ["问题", "现状", "建议"],
          [["RGB 参数与第 8 页原数字对不上",
            "第 5 页印的 BGR 范围复现不出 41,463 等数值，说明当时手调过阈值但代码块没同步",
            "已统一用复现值；答辩时若被对比旧版，需说明这一点"],
           ["真值包含投影",
            "黑块的真值比两个方法的掩码都大 12k 像素，测不出「真实朝向」",
            "重标一版只含物体本体的真值，才能验证第 9 页那句「偏 12°」"],
           ["YOLO 暗光得分偏高",
            "两个重叠框取并集，多盖了阴影",
            "已在页脚注明；若要更严，可先做 NMS 去重再算"],
           ["第 10 页缺实测数字",
            "该页仍用「两个检出 / 零检出」的定性说法",
            "版面已满，需删掉收束句才能加一行 0.86 / 0.00"]],
          widths=[4.6, 7.2, 4.8], size=8.6)


def section_appendix(doc):
    heading(doc, "附录 A · build_v3.py", 1)
    para(doc,
         "这份脚本就是「第五节」里那些改动的执行代码：新建第 11 页、写入表格与三条读法、"
         "把新页插到附录之前，然后用字符串替换的方式改掉六处文字与一个页码。"
         "之所以没有直接在 PowerPoint 里手改，是因为手改无法复核——脚本跑两遍结果一致，"
         "而且下次要换数字时只改表格数据即可。", 9.8)
    src = open(os.path.join(HERE, "build_v3.py"), encoding="utf-8-sig").read()
    code_block(doc, src)


def main():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.1)
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(1.9)

    style = doc.styles["Normal"]
    style.font.name = CN
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), CN)

    add_page_number_footer(sec)

    # title block
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    set_run(p.add_run("TRACK 1 · WEEK 1"), 10, True, BLUE)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    set_run(p.add_run("代码与改动说明"), 26, True, NAVY)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    set_run(p.add_run("从 11 页到 12 页：补一页证据，修六处数字"), 12.5, False, RGBColor(0x33, 0x46, 0x5E))

    table(doc, ["字段", "值"],
          [["日期", "2026-11-12"],
           ["作者", "Track 1 · Team report"],
           ["文档用途", "交付记录：脚本、指标、PPT 改动逐条对照"]],
          widths=[3.4, 13.2], size=9.0)

    section_overview(doc)
    section_code(doc)
    section_deck_edits(doc)
    section_numbers(doc)
    section_repro(doc)
    section_issues(doc)
    section_appendix(doc)

    doc.core_properties.title = "Track 1 周报 · 代码与改动说明"
    doc.core_properties.author = "Track 1"
    doc.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    main()
