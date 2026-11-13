"""Insert the v5 (multi-object) delta into the record, just before appendix B."""
import os

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(HERE, "Track1_代码与改动说明.docx")

NAVY = RGBColor(0x0F, 0x25, 0x44)
BLUE = RGBColor(0x2F, 0x6F, 0xED)
BODY = RGBColor(0x33, 0x46, 0x5E)
CN = "Microsoft YaHei"


def styled(p, text, size, bold, color):
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = CN
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia"):
        rfonts.set(qn(attr), CN)


doc = Document(DOC)
anchor = next((p for p in doc.paragraphs if p.text.strip().startswith("附录 B")), None)
if anchor is None:
    raise SystemExit("appendix B not found")

items = [
    ("9.5 v5 增量：多物体一次遍历", 11.5, True, BLUE, 12),
    ("页数 13 → 14。新增第 13 页 PIPELINE · ONE PASS, MANY OBJECTS，附录挪到第 14 页。", 9.8, False, BODY, 4),
    ("新脚本 multi_object.py：把绿色（按色相）与深色（按亮度）合成一张掩码，一次 findContours "
     "得到 3 个轮廓，按面积过滤掉 1 个（28 px 的噪点），剩下两个各跑一次 PCA 并画自己的夹爪；"
     "编号按外接框左边界排序，保证两次运行顺序一致。", 9.8, False, BODY, 4),
    ("结果：绿软糖 20,287 px、中心 (520, 335)、朝向 +46.9°；黑橡皮 57,546 px、中心 (675, 1095)、"
     "朝向 −10.4°。两个位姿与第 12 页单物体版本一致（+46.7° / −10.4°），说明“先遍历、再逐个算”"
     "不改变结果。", 9.8, False, BODY, 4),
    ("这条对应 brief 里“用 cv2.findContours 处理多个物体”那一条。截图见 track1_assets/multi/。",
     9.8, False, BODY, 10),
]

for text, size, bold, color, space_before in items:
    p = anchor.insert_paragraph_before()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.3
    styled(p, text, size, bold, color)

doc.save(DOC)
print("inserted v5 delta before appendix B")
