"""Tailor the portfolio to the 轻食研发工程师（门店方向） role.

Usage: python3 -I build.py STAGE1.pdf OUT.pdf FONTDIR PHOTODIR
STAGE1.pdf = output of edit_p9.py (page 9 already revised).
Steps: (1) page 1/2 line tweaks, (2) insert two new pages after page 9,
(3) renumber footers of the pages that moved.
"""
import sys, os, re
import pymupdf as fz
from fontTools.ttLib import TTFont
from fontTools import subset

SRC, DST, FONTDIR, PHOTODIR = sys.argv[1:5]
WORK = os.path.dirname(os.path.abspath(DST))
H = 540.0
GREY = (.384314, .4, .415686)       # 0x62666a
INK = (.141176, .141176, .14902)    # 0x242426
BODY = (.270588, .282353, .298039)  # 0x45484c
RED = (.701961, .14902, .215686)
CARD_FILL = (.984314, .980392, .976471)
CARD_LINE = (.882353, .886275, .886275)
BAR_FILL = (.964706, .960784, .956863)
RULE = (.866667, .87451, .878431)
IMG_LINE = (.882353, .882353, .882353)
SYM = set('·≥≤')

# ------------------------------------------------------------------ content
P1_TAGS = '轻食沙拉  ·  烘焙研发  ·  中式产品  ·  饮品乳制品  ·  酱料研发  ·  门店落地'
P1_GOAL = '求职意向：轻食/食品研发工程师 / 产品研发主管（门店 · OEM/ODM方向）'
P2_CATS = '轻食沙拉 · 烘焙 · 中式食品 · 饮品乳制品 · 酱料与基础组件'

PAGE_A = dict(
    title='门店端产品研发与落地',
    sub='从概念到门店推广的全流程跟进',
    meta='胚 · 陈永春 · 一亩草原  |  门店运营  +  预制产品  +  SOP标准化  +  试销跟进  +  合规与保质期',
    flow_label='落地流程',
    flow=['概念定位', '配方试制', '成本核算 · SOP', '门店小试', '门店试销 · 驻店跟进', '区域/全国门店推广', '数据复盘 · 菜单迭代'],
    cards=[
        ('门店出品导向的配方与SOP', [
            '从店员、店长转岗研发，配方按门店设备条件、人员',
            '操作水平与出餐效率落地；开发20+款预制产品，',
            '门店出品时间由约5分钟缩短至30–60秒。']),
        ('门店小试、试销与驻店跟进', [
            '参与6家新门店项目落地，现场协同设备适配、出品',
            '流程、陈列与器具选型；预制产品经5轮打样后上线；',
            '赴10+个城市做门店调研，20+款新品基于调研开发。']),
        ('成本控制与供应链协同', [
            '配方成本核算与研发记录标准化；对接包装及物料',
            '供应商，完成50+款产品包装方案，包装成本平均',
            '降低20%；OEM/ODM工厂按资质、产能、品控筛选。']),
        ('合规、品控与保质期', [
            '对接清真认证、SC资质与品控评估；酱料以Brix/pH',
            '终点判定、≥85℃热灌装、批次留样控制；按未开封/',
            '开封后分别设定保质期与冷链/温控储运条件。']),
    ])

PAGE_B = dict(
    title='轻食 / 沙拉 / 酱汁',
    sub='三明治 · 沙拉碗 · 塔可 · 烤串 · 轻食酱汁｜门店端轻食产品',
    items=[('01_sandwich.jpg', '牛油果三文鱼三明治'), ('02_bowl.jpg', '鲜虾牛油果藜麦碗'), ('03_salad.jpg', '缤纷果蔬沙拉盒'),
           ('04_skewer.jpg', '菠萝彩椒鸡肉串'), ('05_taco.jpg', '鲜虾芒果塔可'), ('06_sauce.jpg', '轻食酱汁与抹酱')])

# ------------------------------------------------------------------ fonts
def make_subset(src, text, out):
    f = TTFont(src)
    cmap = f.getBestCmap()
    missing = [c for c in set(text) if ord(c) not in cmap and not c.isspace()]
    assert not missing, (src, missing)
    opts = subset.Options(); opts.layout_features = []; opts.name_IDs = ['*']
    opts.notdef_outline = True; opts.hinting = False
    ss = subset.Subsetter(opts)
    ss.populate(unicodes=[ord(c) for c in set(text)] + [32])
    ss.subset(f); f.save(out)
    return TTFont(out)

def width(ft, s, size):
    cm = ft.getBestCmap(); hm = ft['hmtx']; upm = ft['head'].unitsPerEm
    return sum(hm[cm[ord(c)]][0] for c in s) / upm * size

all_reg = P1_TAGS + P1_GOAL + P2_CATS + PAGE_A['meta'] + ''.join(PAGE_A['flow']) + PAGE_B['sub'] + \
    ''.join(l for _, ls in PAGE_A['cards'] for l in ls)
all_bold = PAGE_A['title'] + PAGE_A['sub'] + PAGE_A['flow_label'] + ''.join(h for h, _ in PAGE_A['cards']) + \
    PAGE_B['title'] + ''.join(n for _, n in PAGE_B['items']) + '0123456789→'
all_reg = ''.join(c for c in all_reg if c not in SYM)
REG = os.path.join(WORK, 'new_reg.ttf'); BLD = os.path.join(WORK, 'new_bold.ttf'); SYMF = os.path.join(WORK, 'new_sym.ttf')
freg = make_subset(os.path.join(FONTDIR, 'NotoSansSC-Regular.ttf'), all_reg, REG)
fbld = make_subset(os.path.join(FONTDIR, 'NotoSansSC-Bold.ttf'), all_bold, BLD)
fsym = make_subset(os.path.join(FONTDIR, 'DejaVuSans.ttf'), ''.join(SYM), SYMF)

doc = fz.open(SRC)

def fonts_on(page):
    page.insert_font(fontname='NR', fontfile=REG)
    page.insert_font(fontname='NB', fontfile=BLD)
    page.insert_font(fontname='SY', fontfile=SYMF)

def text_w(s, size, bold=False):
    if bold: return width(fbld, s, size)
    return sum(width(fsym if c in SYM else freg, c, size) for c in s)

def put(page, x, y_top, s, size, color, bold=False):
    """Draw s with baseline at PDF y (from top) = y_top; mixes DejaVu for · ≥ ≤."""
    if bold:
        page.insert_text((x, y_top), s, fontname='NB', fontsize=size, color=color); return
    run = ''; sym = None
    for ch in s + '\0':
        is_sym = ch in SYM
        if ch == '\0' or (run and is_sym != sym):
            page.insert_text((x, y_top), run, fontname='SY' if sym else 'NR', fontsize=size, color=color)
            x += text_w(run, size); run = ''
        if ch != '\0': run += ch; sym = is_sym

def replace_line(page, old_text, new_text, size, color, max_right):
    hits = page.search_for(old_text)
    assert len(hits) == 1, (old_text, hits)
    r = hits[0]
    # baseline from the span origin
    origin = None
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for sp in l['spans']:
                if sp['text'].strip() == old_text.strip() or old_text.strip() in sp['text']:
                    origin = sp['origin']
    assert origin, old_text
    page.add_redact_annot(r + (-1, -1, 1, 1))
    page.apply_redactions(images=fz.PDF_REDACT_IMAGE_NONE, graphics=fz.PDF_REDACT_LINE_ART_NONE)
    fonts_on(page)  # redaction rebuilds the page resources
    w = text_w(new_text, size)
    assert origin[0] + w <= max_right, (new_text, origin[0] + w)
    put(page, origin[0], origin[1], new_text, size, color)

# ------------------------------------------------------------------ 1) page 1 / page 2 lines
p = doc[0]; fonts_on(p)
replace_line(p, '烘焙研发  ·  中式产品  ·  饮品乳制品  ·  酱料研发  ·  清真食品  ·  产品落地', P1_TAGS, 14.2, GREY, 585)
replace_line(p, '求职意向：食品研发工程师 / 烘焙研发 / 产品研发主管（OEM/ODM方向）', P1_GOAL, 13.2, GREY, 585)
p = doc[1]; fonts_on(p)
replace_line(p, '烘焙 · 中式食品 · 饮品乳制品 · 酱料与基础组件', P2_CATS, 14.0, INK, 700)

# ------------------------------------------------------------------ common chrome
def chrome(page, title, number):
    sh = page.new_shape()
    sh.draw_rect(fz.Rect(64, 46, 94, 49)); sh.finish(fill=RED, color=None, width=0)
    sh.draw_line(fz.Point(64, 497), fz.Point(896, 497)); sh.finish(color=RULE, width=0.75)
    sh.commit()
    put(page, 64, 86.0, title, 25, INK, bold=True)
    put(page, 874, 516.0, '%02d' % number, 11, GREY, bold=True)

# ------------------------------------------------------------------ 2a) new page A: 门店端研发与落地
pa = doc.new_page(pno=9, width=960, height=540); fonts_on(pa)
chrome(pa, PAGE_A['title'], 10)
put(pa, 64, 120.5, PAGE_A['sub'], 17, INK, bold=True)
put(pa, 64, 148.5, PAGE_A['meta'], 12.6, GREY)
# flow bar (same geometry as page 9: y 160..186)
sh = pa.new_shape(); sh.draw_rect(fz.Rect(64, 160, 896, 186), radius=(4 / 832, 4 / 26)); sh.finish(fill=BAR_FILL, color=None, width=0); sh.commit()
put(pa, 76, 177.5, PAGE_A['flow_label'], 11.5, RED, bold=True)
x = 136.0; gap = 6.0; arrow_w = width(fbld, '→', 11.2)
for i, it in enumerate(PAGE_A['flow']):
    put(pa, x, 177.4, it, 11.2, INK); x += text_w(it, 11.2) + gap
    if i < len(PAGE_A['flow']) - 1:
        put(pa, x, 177.4, '→', 11.2, RED, bold=True); x += arrow_w + gap
assert x - gap <= 892, x
# cards 2x2 (page-4 geometry shifted down 22pt for the flow bar)
boxes = [fz.Rect(64, 199, 468, 342), fz.Rect(492, 199, 896, 342), fz.Rect(64, 352, 468, 495 - 8), fz.Rect(492, 352, 896, 495 - 8)]
sh = pa.new_shape()
for b in boxes:
    sh.draw_rect(b, radius=(6 / b.width, 6 / b.height)); sh.finish(fill=CARD_FILL, color=CARD_LINE, width=1)
    sh.draw_rect(fz.Rect(b.x0 + 18, b.y0 + 15, b.x0 + 21.5, b.y0 + 33)); sh.finish(fill=RED, color=None, width=0)
sh.commit()
for b, (head, lines) in zip(boxes, PAGE_A['cards']):
    put(pa, b.x0 + 31, b.y0 + 29.5, head, 17, INK, bold=True)
    for k, ln in enumerate(lines):
        w = text_w(ln, 15); assert b.x0 + 18 + w <= b.x1 - 14, (ln, w)
        put(pa, b.x0 + 18, b.y0 + 62 + k * 23, ln, 15, INK)

# ------------------------------------------------------------------ 2b) new page B: 轻食 gallery
pb = doc.new_page(pno=10, width=960, height=540); fonts_on(pb)
chrome(pb, PAGE_B['title'], 11)
put(pb, 64, 110.0, PAGE_B['sub'], 12, GREY)
cells = [fz.Rect(64 + c * 285.3333, 121 + r * 190, 64 + c * 285.3333 + 261.3333, 121 + r * 190 + 153) for r in range(2) for c in range(3)]
sh = pb.new_shape()
for cell, (fn, name) in zip(cells, PAGE_B['items']):
    pb.insert_image(cell, filename=os.path.join(PHOTODIR, fn), keep_proportion=True)
    sh.draw_rect(cell); sh.finish(color=IMG_LINE, width=0.6)
    w = text_w(name, 13, bold=True)
    put(pb, cell.x0 + (cell.width - w) / 2, cell.y1 + 17.5, name, 13, INK, bold=True)
sh.commit()

# ------------------------------------------------------------------ 3) renumber footers of moved pages (old 10..17 -> 12..19)
for i in range(11, len(doc)):
    page = doc[i]; old = '%02d' % (i - 1); new = '%02d' % (i + 1)
    hits = [r for r in page.search_for(old, clip=fz.Rect(850, 500, 900, 525))]
    assert len(hits) == 1, (i + 1, old, hits)
    page.add_redact_annot(hits[0] + (-1, -1, 1, 1))
    page.apply_redactions(images=fz.PDF_REDACT_IMAGE_NONE, graphics=fz.PDF_REDACT_LINE_ART_NONE)
    fonts_on(page)
    put(page, 874, 516.0, new, 11, GREY, bold=True)

doc.set_metadata({**doc.metadata, 'subject': '食品产品研发求职资料（轻食/门店方向）'})
doc.save(DST, garbage=3, deflate=True)
print('pages', len(doc), 'saved', DST)
