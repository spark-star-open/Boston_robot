"""Build the beginner tutorial as a Word document with one figure per step."""
import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "track1_assets", "learn")
OUT = os.path.join(HERE, "Track1_流水线入门教程.docx")

NAVY = RGBColor(0x0F, 0x25, 0x44)
BLUE = RGBColor(0x2F, 0x6F, 0xED)
GREY = RGBColor(0x6E, 0x80, 0x95)
BODY = RGBColor(0x33, 0x46, 0x5E)
WARN = RGBColor(0xB2, 0x6A, 0x12)

CN = "Microsoft YaHei"
MONO = "Consolas"


def set_run(run, size=10.5, bold=False, color=BODY, font=CN):
    run.font.size = Pt(size)
    run.font.bold = bold
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


def para(doc, text="", size=10.5, bold=False, color=BODY, before=0, after=6,
         align=None, line=1.5, font=CN):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line
    if align is not None:
        p.alignment = align
    if text:
        set_run(p.add_run(text), size, bold, color, font)
    return p


def heading(doc, text, level=1, kicker=None):
    if kicker:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        set_run(p.add_run(kicker), 9, True, BLUE)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2 if kicker else 16)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = True
    set_run(p.add_run(text), 16 if level == 1 else 12, True, NAVY if level == 1 else BLUE)
    return p


def figure(doc, name, caption, width_cm):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(os.path.join(FIG, name), width=Cm(width_cm))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(10)
    set_run(c.add_run(caption), 8.8, False, GREY)


def code(doc, source, size=8.6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.left_indent = Cm(0.3)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "F5F7FA")
    pPr.append(shd)
    lines = source.strip("\n").split("\n")
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


def pitfall(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Cm(0.2)
    set_run(p.add_run("容易踩的坑　"), 9.5, True, WARN)
    set_run(p.add_run(text), 9.5, False, BODY)


def add_footer(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("Track 1 入门 · 从一张照片到一个位姿   ·   "), 8.5, False, GREY)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "17")
    rpr.append(sz)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    p._p.append(fld)


def main():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin = Cm(2.1)
    sec.bottom_margin = Cm(2.0)
    add_footer(sec)

    style = doc.styles["Normal"]
    style.font.name = CN
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), CN)

    # ---------------- cover ----------------
    para(doc, "TRACK 1 · 初学者读本", 10, True, BLUE, before=10, after=2)
    para(doc, "从一张照片到一个位姿", 28, True, NAVY, after=4, line=1.15)
    para(doc, "这套流水线其实只有五步，每一步都对应一个能单独运行的函数。",
         12.5, False, RGBColor(0x33, 0x46, 0x5E), after=14, line=1.4)
    para(doc,
         "写给同组同学：如果你看不懂 task1_rgb.py 里那一长串 cv2 调用，先读这一份。"
         "它不讲怎么改代码，只讲每个函数在干什么、为什么需要它、它会在哪儿出错。",
         10.5, False, GREY, after=6)
    para(doc, "全篇只用了一张照片、一个绿色软糖、一条流水线。读完大约 15 分钟。",
         10.5, False, GREY, after=10)

    para(doc, "读完你会知道", 10, True, NAVY, before=8, after=4)
    for t in ["一张彩色照片在 Python 里到底是什么；",
              "「绿色」怎么被翻译成一组数字，又怎么变成一张黑白图；",
              "黑白图怎么变成一个中心点和一个角度；",
              "以及——怎么判断这个结果到底准不准。"]:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(3)
        set_run(p.add_run(t), 10)

    para(doc, "配套文件：learn_pipeline.py（可运行的示例）、"
              "track1_assets/learn/（本文所有插图）、Track1_Week1_Report_v3.pptx（这些代码的出处）。",
         9, False, GREY, before=14)
    doc.add_page_break()

    # ---------------- 0 ----------------
    heading(doc, "零、先看全景", 1)
    para(doc,
         "代码从头到尾只在做一件事：把「一张彩色照片」变成「一个中心点加一个角度」。"
         "中间拆成五步，每一步的产物都能单独存成一张图看。")
    code(doc,
         "彩色照片  →  掩码（黑白）  →  干净掩码  →  轮廓（一串点）  →  位姿（中心 + 角度）\n"
         "  cv2          inRange        open/close     findContours      minAreaRect\n"
         "  读图         颜色变白       去噪/补洞       找边界            外接矩形")
    para(doc,
         "把 learn_pipeline.py 跑一遍，它会打印每一步的数字，并在 track1_assets/learn/ 里存下 5 张图。"
         "下面每一节都对应其中一张。")

    # ---------------- 1 ----------------
    heading(doc, "一、图像就是一张数字表格", 1, "第 1 台阶")
    figure(doc, "fig1_array.jpg",
           "图 1 · 左：整张照片。右：同一个位置放大 20 倍，能看到一个一个像素方块。", 13.6)
    para(doc, "一张 1024×1460 的彩色照片，在 Python 里就是个表格：1460 行、1024 列、每格 3 个数字，每个数字 0–255。")
    code(doc,
         "img = cv2.imread(path)\n"
         "img.shape        # (1460, 1024, 3)   高、宽、通道\n"
         "img[0, 0]        # [166 185 190]     一个像素的三个通道值")
    para(doc,
         "所以「处理图像」不是什么玄学，就是对这个表格做加减乘除：把某些格子的值改成 0，"
         "或者找出表格里满足某个条件的连续区域。")
    pitfall(doc,
            "shape 的顺序是高在前、宽在后；通道顺序是 B、G、R 不是 RGB，所以 (0,255,0) 是纯绿。"
            "另外 dtype 是 uint8，只能装 0–255，255 再加 1 会变回 0，不要直接拿像素做加减。")

    # ---------------- 2 ----------------
    heading(doc, "二、阈值：把「绿色」翻译成数字", 1, "第 2 台阶")
    figure(doc, "fig2_mask.jpg",
           "图 2 · 左：原图。右：只保留色相 40–70 的像素，绿色软糖变成白斑，其余全黑。", 12.6)
    para(doc,
         "人眼说「那是绿色的」，计算机只认数字。于是我们把颜色写成一个区间，逐像素判断在不在里面——"
         "在就涂白（255），不在就涂黑（0）。这张黑白图叫掩码（mask）。")
    code(doc,
         "hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)\n"
         "mask = cv2.inRange(hsv,\n"
         "                   np.array([40, 40, 40]),     # H, S, V 的下限\n"
         "                   np.array([70, 255, 255]))   # H, S, V 的上限")
    para(doc,
         "为什么要先转到 HSV：在 HSV 里 H 管「什么颜色」、V 管「多亮」。开灯关灯主要改 V，"
         "H 几乎不动，所以一套阈值能同时应付两种光照。而 BGR 三个通道都掺了亮度，灯一亮三个数一起漂，"
         "阈值就废了——这正是当初 RGB 版本在亮光下崩掉的原因。")
    pitfall(doc,
            "inRange 的上下限可以互换位置（OpenCV 会自动取小值做大值），但别指望它帮你判断合理范围。"
            "阈值调太严 → 白斑只剩一小块；调太松 → 背景也被吃进来。")

    # ---------------- 3 ----------------
    heading(doc, "三、形态学：修毛刺和空洞", 1, "第 3 台阶")
    figure(doc, "fig3_morph.jpg",
           "图 3 · 示意图（不是这张照片，为了看清效果而人工加了噪点）：A 原始 → B 开运算去掉零散白点 → C 闭运算补掉内部黑洞。", 16.0)
    para(doc,
         "阈值切出来的白斑边缘往往不干净：外圈有零散白点，里面有小黑洞。形态学就是拿一个小方块"
         "（kernel）在图上滑，按「邻居够不够白」来决定这一格留不留。")
    code(doc,
         "kernel = np.ones((5, 5), np.uint8)   # 看周围 5×5 的范围\n"
         "mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)   # 先腐蚀再膨胀：去小白点\n"
         "mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)   # 先膨胀再腐蚀：补小黑洞")
    para(doc,
         "这张照片本身很干净，跑出来的数字是 20,989 → 20,986 → 20,987，几乎没变化。"
         "但换成黑色橡皮那组，开闭运算的影响就明显得多——暗色物体的掩码边界永远更脏。")
    pitfall(doc,
            "kernel 越大效果越猛。21×21 会把豆子边缘啃掉一圈，形状变圆、面积变小，"
            "外接矩形的角度也跟着变——这是「过度处理」的典型症状。")

    # ---------------- 4 ----------------
    heading(doc, "四、轮廓：沿边界走一圈", 1, "第 4 台阶")
    figure(doc, "fig4_contours.jpg",
           "图 4 · findContours 沿着白斑的边界取了一串点，再把这些点连起来画回原图。", 7.6)
    para(doc,
         "光有白斑还不够，我们要的是「物体的边界在哪」。findContours 就是沿白色区域的边界走一圈，"
         "把走过的点全记下来，返回一个列表，每个元素是一串 (x, y)。")
    code(doc,
         "contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,\n"
         "                               cv2.CHAIN_APPROX_SIMPLE)\n"
         "\n"
         "for c in contours:\n"
         "    if cv2.contourArea(c) < 300:     # 面积太小，多半是噪声\n"
         "        continue")
    para(doc,
         "RETR_EXTERNAL 表示只要最外层轮廓，不管里面有没有洞；CHAIN_APPROX_SIMPLE 会把同一条直线上的点"
         "压成一个点，省内存。这一步跑完，这颗豆子的轮廓是 239 个点、面积 20,738。")
    pitfall(doc,
            "面积过滤是一刀切，也是双刃剑。亮光下黑橡皮被切成三块，每块都超过 300，"
            "于是三块都被当成物体，给出三个互相矛盾的位姿——你 PPT 第 8 页那个现象就是这么来的。")

    # ---------------- 5 ----------------
    heading(doc, "五、位姿：从一个白斑到一个点加一个角度", 1, "第 5 台阶")
    figure(doc, "fig5_pose.jpg",
           "图 5 · minAreaRect 给出的最小外接矩形（黄框），它的中心红点就是 (u, v)，"
           "旋转角就是 −45.0°。", 7.6)
    para(doc,
         "找一圈轮廓之后，问题变成「这个形状怎么用几个数描述」。minAreaRect 的做法是："
         "找一个能刚好包住这个白斑、并且面积最小的矩形。这个矩形转了多少度，就是物体的朝向。")
    code(doc,
         "(cx, cy), (w, h), angle = cv2.minAreaRect(contour)\n"
         "box = cv2.boxPoints(((cx, cy), (w, h), angle))   # 把矩形还原成 4 个顶点，方便画\n"
         "\n"
         "# 这颗豆子的结果\n"
         "# 中心 (519.0, 334.5)   尺寸 128.0×219.9   角度 -45.0")
    para(doc,
         "注意这里说的「位姿」很朴素：一个平面上的点 (u, v) 加一个朝向角 θ。没有深度，"
         "也就没有 6D 位姿——机器人要抓它，还差一步深度估计。")
    pitfall(doc,
            "angle 是「某一条边」的角度，OpenCV 不告诉你是长边还是短边，所以 −45° 和 +45° "
            "可能描述同一个豆子。要统一，先看 w 和 h：谁大，就以谁为准。")

    # ---------------- 6 ----------------
    heading(doc, "六、IoU：怎么知道测得准不准", 1, "第 6 台阶")
    figure(doc, "fig6_iou.jpg",
           "图 6 · 两个掩码叠在一起：深色是重合部分，全部浅色是并集。IoU 就是前者除以后者。", 9.0)
    para(doc,
         "有了两个掩码（一个是你算的，一个是手标的真值），怎么量化「像不像」？答案是 IoU："
         "重合的像素数除以合起来的像素数。完全重合是 1.0，完全不沾是 0.0。")
    code(doc,
         "iou = np.logical_and(gt, pred).sum() / np.logical_or(gt, pred).sum()")
    para(doc,
         "它最好用的地方是没有单位：不管图多大、物体多大，结果都是 0–1 之间的小数，"
         "可以直接横向比。PPT 第 11 页那张表，每一格就是这么算出来的。")
    pitfall(doc,
            "分子分母都别忘了：IoU 用的是「交集 / 并集」，不是「交集 / 真值」。"
            "用错分母算出来的叫 recall，数值会虚高。")

    # ---------------- 7 ----------------
    heading(doc, "七、GrabCut：为什么标真值还要人帮忙", 1, "进阶")
    para(doc,
         "要算 IoU，得先有一个「标准答案」。全自动抠图不靠谱，纯手工涂又太慢，"
         "于是 GrabCut 走中间路线：你给一个粗框，它自己猜框里哪些是物体、哪些是背景。")
    code(doc,
         "mask = np.zeros(img.shape[:2], np.uint8)\n"
         "bgd, fgd = np.zeros((1,65), np.float64), np.zeros((1,65), np.float64)\n"
         "cv2.grabCut(img, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)")
    para(doc,
         "最后那个 5 是迭代次数。rect 是你拖的框——框大一点没关系，它自己会往里收。"
         "但它也会犯错：暗光下那颗豆子的框拖松了，它把左边一块背景也吃进去，"
         "长宽比从 1.7 变成 1.0，角度直接失效。所以标完要看一眼叠加图，别闭眼交。")

    # ---------------- 8 ----------------
    heading(doc, "八、YOLO：一行推理，为什么还会「找不到」", 1, "进阶")
    para(doc,
         "前面所有方法都要你手调阈值；YOLO 是训好的神经网络，喂图进去直接吐框、类别和掩码，"
         "不用调任何参数。")
    code(doc,
         "model = YOLO(\"yolov8n-seg.pt\")\n"
         "res   = model(img, conf=0.5)[0]\n"
         "for box in res.boxes:\n"
         "    print(model.names[int(box.cls)], float(box.conf))")
    para(doc,
         "conf=0.5 是个闸门：模型给每个候选打一个 0–1 的置信度，低于 0.5 直接丢掉。"
         "亮光下它给出的置信度全都不到 0.5，于是返回空列表——表里那两个 0.000 就是这么来的。"
         "它不是算错了，是不敢说。")
    para(doc,
         "至于把软糖认成 frisbee：它只学过 COCO 的 80 类，软糖不在里面，它只能从学过的类别里挑一个最像的。"
         "这就是「类别体系不覆盖」与「模型认错」的区别，写报告时这个区别很重要。")

    # ---------------- 9 ----------------
    heading(doc, "九、怎么读别人写的脚本", 1)
    para(doc, "别从头一行行读。按这个顺序跳，五分钟能摸清一份陌生脚本：")
    for i, t in enumerate([
        "看 import：用 cv2 还是 torch，就知道是传统方法还是神经网络。",
        "看顶部常量：BGR_RANGES、MIN_AREA 这类大写变量，是全部「可调旋钮」。",
        "看函数名：components()、grabcut()、pose()，名字就是目录。",
        "最后看 if __name__ == \"__main__\":，真正的执行顺序在那儿。",
    ], 1):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.left_indent = Cm(0.6)
        set_run(p.add_run(f"{i}. "), 10, True, NAVY)
        set_run(p.add_run(t), 10)

    # ---------------- 10 ----------------
    heading(doc, "十、三个动手练习", 1)
    para(doc, "改 learn_pipeline.py 里的数字，重跑，看输出怎么变。每个两分钟。")
    for t in [
        "把绿色下限 [40, 40, 40] 里的第二个 40 改成 120（提高饱和度要求）——"
        "白斑会明显缩小甚至消失，这是「阈值调太严」。",
        "把 MIN_AREA = 300 改成 20000——连豆子都被过滤掉，输出一片空白，这是「面积阈值调太大」。",
        "把 kernel 从 (5,5) 改成 (21,21)——豆子被啃掉一圈、形状变圆，这是「形态学太猛」。",
    ]:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(6)
        set_run(p.add_run(t), 10)

    # ---------------- 11 ----------------
    heading(doc, "十一、术语速查", 1)
    terms = [
        ("掩码 mask", "黑白图，白的地方是物体，黑的地方是背景。"),
        ("阈值 threshold", "把连续的数值切成「要」和「不要」的那个数。"),
        ("形态学 morphology", "按邻域规则增删像素，用来去噪和补洞。"),
        ("轮廓 contour", "白色区域的边界，是一串 (x, y) 点。"),
        ("位姿 pose", "这里指平面位姿：中心 (u, v) 加朝向角 θ，不含深度。"),
        ("真值 ground truth", "人工标注的正确答案，用来衡量算法准不准。"),
        ("IoU", "两个掩码的交集除以并集，0–1 之间，越大越准。"),
        ("conf 置信度", "模型对「这里有东西」的把握，低于阈值就被丢弃。"),
    ]
    for name, desc in terms:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.left_indent = Cm(0.6)
        set_run(p.add_run(name + "　"), 10, True, NAVY)
        set_run(p.add_run(desc), 10)

    # ---------------- appendix ----------------
    heading(doc, "附录 · learn_pipeline.py 全文", 1)
    para(doc, "这份脚本把上面五步拆开跑了一遍，每步都存图、都打印数字。建议边读边跑。", 9.5, color=GREY)
    code(doc, open(os.path.join(HERE, "learn_pipeline.py"), encoding="utf-8-sig").read(), 7.9)

    doc.core_properties.title = "Track 1 流水线入门"
    doc.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    main()
