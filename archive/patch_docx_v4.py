"""Append the v4 delta and the experiment log to the technical record."""
import os

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(HERE, "Track1_代码与改动说明.docx")

NAVY = RGBColor(0x0F, 0x25, 0x44)
BLUE = RGBColor(0x2F, 0x6F, 0xED)
GREY = RGBColor(0x6E, 0x80, 0x95)
BODY = RGBColor(0x33, 0x46, 0x5E)
CN, MONO = "Microsoft YaHei", "Consolas"


def set_run(run, size=10, bold=False, color=BODY, font=CN):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia"):
        rfonts.set(qn(attr), font if attr != "w:eastAsia" else CN)


def heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16 if level == 1 else 12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    set_run(p.add_run(text), 15 if level == 1 else 11.5, True, NAVY if level == 1 else BLUE)
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


def para(doc, text, size=10, color=BODY, after=6, mono=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.35
    set_run(p.add_run(text), size, False, color, MONO if mono else CN)


def table(doc, header, rows, widths, size=8.6):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    hdr = t.rows[0].cells
    for i, txt in enumerate(header):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        set_run(p.add_run(txt), size, True, RGBColor(0xFF, 0xFF, 0xFF))
        tcPr = hdr[i]._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "0F2544")
        tcPr.append(shd)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for ci, txt in enumerate(row):
            cells[ci].text = ""
            p = cells[ci].paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            set_run(p.add_run(str(txt)), size)
            if ri % 2 == 1:
                tcPr = cells[ci]._tc.get_or_add_tcPr()
                shd = OxmlElement("w:shd")
                shd.set(qn("w:val"), "clear")
                shd.set(qn("w:color"), "auto")
                shd.set(qn("w:fill"), "F7FAFE")
                tcPr.append(shd)
    for ci, w in enumerate(widths):
        for row in t.rows:
            row.cells[ci].width = Cm(w)
    for row in t.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    t.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


doc = Document(DOC)

heading(doc, "九、v4 增量：PCA 与夹爪", 1)
para(doc,
     "前面的记录止于 v3（12 页）。之后按 Track 1 的 brief 补了 PCA 位姿与平行夹爪，"
     "生成 v4（13 页）。本节只记增量，前面的内容保持原样，作为当时的状态存档。")

heading(doc, "9.1 结构变化", 2)
table(doc, ["项", "v3", "v4"],
      [["页数", "12", "13"],
       ["新增页", "第 11 页（量化对比）", "第 12 页（PCA + 夹爪）"],
       ["附录位置", "第 12 页", "第 13 页"],
       ["附录页码", "12", "13"]],
      [3.4, 6.0, 7.0])

heading(doc, "9.2 第 3 页的一处措辞", 2)
table(doc, ["原文", "改为", "原因"],
      [["…heading θ from minAreaRect; it is not a 6D pose…",
        "…heading θ from minAreaRect (or PCA, once a gripper is drawn — slide 12); …",
        "前 11 页的 IoU 表用的是 minAreaRect，第 12 页按 brief 换成 PCA，"
        "不点明会前后矛盾"]],
      [6.0, 6.4, 4.0])

heading(doc, "9.3 第 12 页的构成", 2)
table(doc, ["区块", "内容"],
      [["眉题", "POSER · PCA + PARALLEL-JAW GRIPPER"],
       ["标题", "Three masks, one pose: the heading holds to within a degree"],
       ["主图", "暗光绿软糖 × 三张掩码（颜色阈值 / 灰度+颜色 / YOLO），各画主轴与夹爪"],
       ["表格", "三种掩码来源在四个案例上的 PCA 朝向（度）"],
       ["右栏", "为什么用 PCA 而不是 minAreaRect：平均更稳、直接给出长短轴、"
                "输入输出统一、夹爪是最终检验"],
       ["底栏", "numpy 的 (row, column) 与 OpenCV 的 (x, y) 必须换轴"]],
      [3.0, 13.6])

heading(doc, "9.4 新增脚本", 2)
table(doc, ["脚本", "作用"],
      [["pca_gripper.py", "对真值掩码做 PCA，画长短轴与平行夹爪（brief 的核心交付）"],
       ["pca_compare.py", "同一套 PCA 跑在三种掩码来源上，输出三栏对比图"],
       ["dump_masks.py", "把三种方法的掩码并排画出来存图，替代断点调试"],
       ["conf_sweep.py", "扫描 YOLO 的置信度阈值，看零检出是“没看见”还是“不敢说”"]],
      [4.2, 12.4])

heading(doc, "附录 B · 实验日志", 1)
para(doc,
     "按要求留痕：这一节按时间顺序记下当天遇到的实际报错与处理。所有报错都是原文，没有改写。",
     size=9.5, color=GREY)

log = [
    ("12:11", "读参考 PDF", "本地无 pypdf / pdfminer，无法直接抽取文本",
     "自写 FlateDecode + TJ 解析脚本，抽出 37 页正文"),
    ("12:20", "下载参考 PDF", "Invoke-WebRequest: 基础连接已关闭；curl: schannel SEC_E_NO_CREDENTIALS",
     "改用 python urllib.request 下载成功"),
    ("12:44", "pip install opencv-python",
     "ValueError: check_hostname requires server_hostname",
     "系统代理 127.0.0.1:7890 触发旧版 urllib3 的 TLS-in-TLS 缺陷；设 NO_PROXY=* 并换清华源"),
    ("12:52", "装完导入失败", "PyCharm 里提示“没有名称为 cv2 的模块”",
     "pip 装进了 Python 3.8，而项目解释器是 3.14；改用 D:\\python\\python.exe -m pip"),
    ("13:00", "读图返回 None", "cv2.imread 读中文路径返回 None，下一行 .shape 报 AttributeError",
     "改用 np.fromfile + cv2.imdecode"),
    ("13:11", "安装 ultralytics", "pip 写临时目录被沙箱拒绝（Permission denied）",
     "在用户终端执行，或提升权限后重试"),
    ("16:33", "PyCharm 断点调试",
     "AttributeError: '_MainThread' object has no attribute '_handle'（pydevd_pep_669_tracing.py）",
     "PyCharm 2025.1 的调试器不兼容 Python 3.14 的 PEP 669；改用 Run + dump_masks.py 看中间结果"),
    ("17:50", "角度列出现 77.6° / 45.0°",
     "pose() 直接取 minAreaRect 的角度，没判断哪条是长边",
     "按 w < h 补 90°，并把长宽比 < 1.15 的角度判为无定义"),
    ("18:10", "YOLO 亮光两格 0.000",
     "怀疑是掩码没算对", "conf 扫描证明是置信度掉到 0.18；降到 0.15 可恢复 IoU 0.784"),
    ("19:45", "PCA 跨度异常", "同一块橡皮算出 L=636 / W=1286，明显超出画面",
     "PCA 用 ptp 求跨度，几个游离像素就能把轴拉远；先取最大连通域再算"),
]
table(doc, ["时间", "事件", "报错 / 现象", "处理"], log, [1.4, 3.4, 6.4, 5.2], size=8.2)

doc.save(DOC)
print("appended to", DOC)
