"""Rebuild the whole portfolio with one design system.
Usage: python3 -I deck.py OUT.pdf FONTDIR IMGDIR(orig extracted) RGBADIR(logos) LIGHTDIR(轻食 photos) CACHE
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck_engine import *

OUT, FONTDIR, IMG, RGBA, LIGHTDIR, CACHE = sys.argv[1:7]
TOTAL = 19
D = Deck(FONTDIR, CACHE)
I = lambda n: os.path.join(IMG, n)          # original product photos (pNN_xNNN.jpeg)
L = lambda n: os.path.join(RGBA, n)         # logos / badge / portrait (png with alpha)
P = lambda n: os.path.join(LIGHTDIR, n)        # 轻食 photos

# ====================================================================== chrome
def header(label, title, meta=None, meta2=None, logo=None):
    D.text(M, 58, label, 9.5, 'm', RED, tracking=1.6)
    D.text(M, 90, title, 26, 'b', INK)
    y = 114
    if meta:
        D.text(M, y, meta, 12.5, 'r', MUTED); y += 18
    if meta2:
        D.text(M, y - 1, meta2, 12, 'r', MUTED)
    if logo:
        D.image_fit((760, 46, 896, 96), L(logo), align='right')

def footer(n):
    D.line(M, 500, W - M, 500, LINE, 0.6)
    D.text(M, 518, '惠志杨 · 食品产品研发作品集 2026', 9, 'r', MUTED)
    D.text(W - M, 518, '%02d / %d' % (n, TOTAL), 9.5, 'm', MUTED, align='right')

def tick(x, y, h=16):
    D.rect((x, y, x + 3, y + h), fill=RED)

def stat(x, y, value, label):
    m = re.match(r'^([0-9A-Za-z+%–\-.→]+)(.*)$', value)
    num, unit = m.group(1), m.group(2)
    w = D.text(x, y, num, 28, 'x', INK)
    if unit: D.text(x + w + 2, y, unit, 15, 'b', INK)
    D.text(x, y + 19, label, 11, 'r', MUTED)

def stat_strip(y, stats):
    cw = CW / len(stats)
    for k, (v, lab) in enumerate(stats):
        x = M + k * cw
        if k: D.line(x - 18, y - 24, x - 18, y + 24, LINE, 0.6)
        stat(x, y, v, lab)

def card(r, head, body, body_size=12.5, leading=19.5, max_lines=3, fill=SURFACE):
    r = fz.Rect(r)
    D.rect(r, fill=fill, radius=6)
    tick(r.x0 + 18, r.y0 + 19)
    D.text(r.x0 + 30, r.y0 + 32, head, 14.5, 'b', INK)
    D.paragraph(r.x0 + 18, r.y0 + 57, body, body_size, 'r', BODY, maxw=r.width - 36, leading=leading, max_lines=max_lines)

def cards_2x2(top, bottom, items, **kw):
    h = (bottom - top - 12) / 2; w = (CW - 16) / 2
    for i, (head, body) in enumerate(items):
        x = M + (i % 2) * (w + 16); y = top + (i // 2) * (h + 12)
        card((x, y, x + w, y + h), head, body, **kw)

# gallery: 4 x 2 grid, cell 196 x 146
GW, GH, GX, GY = 196.0, 146.0, 16.0, 36.0
def cell_rect(col, row, cols=1, rows=1):
    x = M + col * (GW + GX); y = 134 + row * (GH + GY)
    return fz.Rect(x, y, x + cols * GW + (cols - 1) * GX, y + rows * GH + (rows - 1) * GY)

def photo(r, path, name, note=None, fx=0.5, fy=0.5, region=None, halal=False, tag=None):
    r = fz.Rect(r)
    D.image(r, path, fx=fx, fy=fy, region=region)
    w = D.text(r.x0, r.y1 + 16, name, 12, 'm', INK)
    if note: D.text(r.x0 + w + 4, r.y1 + 16, note, 10.5, 'r', MUTED)
    if halal: D.image_fit((r.x1 - 34, r.y0 + 8, r.x1 - 8, r.y0 + 34), L('badge_halal.png'))
    if tag:
        tw = D.width(tag, 9, 'm') + 14
        D.rect((r.x0 + 8, r.y0 + 8, r.x0 + 8 + tw, r.y0 + 26), fill=RED, radius=3)
        D.text(r.x0 + 15, r.y0 + 20.5, tag, 9, 'm', WHITE)

def note_card(r, brand, head, body):
    r = fz.Rect(r)
    D.rect(r, fill=SURFACE, radius=6)
    D.text(r.x0 + 18, r.y0 + 26, brand, 10, 'm', RED, tracking=0.6)
    D.text(r.x0 + 18, r.y0 + 48, head, 13.5, 'b', INK)
    D.paragraph(r.x0 + 18, r.y0 + 71, body, 11.5, 'r', BODY, maxw=r.width - 36, leading=17, max_lines=4)

def gallery(label, title, meta, items, note=None, note_pos=(2, 1)):
    """items: list of dicts(path,name,note?,fx,fy,region,halal,tag); 6 photos + note card, or 8 photos."""
    D.new_page(); header(label, title, meta)
    slots = [(c, r) for r in range(2) for c in range(4)]
    if note:
        slots = [s for s in slots if s not in (note_pos, (note_pos[0] + 1, note_pos[1]))]
        note_card(cell_rect(*note_pos, cols=2), *note)
    assert len(items) == len(slots), (len(items), len(slots))
    for (c, r), it in zip(slots, items):
        photo(cell_rect(c, r), it['path'], it['name'], it.get('note'), it.get('fx', .5), it.get('fy', .5), it.get('region'), it.get('halal', False), it.get('tag'))

def mosaic(x0, paths):
    """2x2 full-bleed photo mosaic from x0 to the right page edge."""
    g = 6; cw = (W - x0 - g) / 2; ch = (H - g) / 2
    for i, (p, fx, fy) in enumerate(paths):
        x = x0 + (i % 2) * (cw + g); y = (i // 2) * (ch + g)
        D.image((x, y, x + cw, y + ch), p, fx=fx, fy=fy, stroke=None, scale=2.5)

# ====================================================================== 01 cover
D.new_page()
mosaic(540, [(I('p12_x91.jpeg'), .5, .5), (I('p10_x156.jpeg'), .5, .5), (P('a5dcde27-image.jpg'), .45, .45), (I('p11_x87.jpeg'), .5, .5)])
x = 80
D.text(x, 128, 'PRODUCT R&D PORTFOLIO · 2026', 10, 'm', RED, tracking=2)
D.text(x, 196, '惠志杨', 66, 'b', INK)
D.text(x, 240, '食品产品研发', 24, 'm', INK)
D.rect((x, 258, x + 56, 260), fill=RED)
D.text(x, 296, '轻食沙拉 · 烘焙研发 · 中式产品 · 饮品乳制品 · 酱料研发 · 门店落地', 14, 'r', BODY)
D.text(x, 322, '求职意向：轻食/食品研发工程师 · 产品研发主管（门店 · OEM/ODM方向）', 13, 'r', MUTED)
D.text(x, 346, '6年+餐饮及食品相关经验 ｜ 现居江苏扬州', 13, 'r', MUTED)
w = D.text(x, 376, '17318877700', 13.5, 'm', INK)
D.line(x + w + 14, 365, x + w + 14, 379, LINE, 0.8)
D.text(x + w + 28, 376, 'zhiyzone@foxmail.com', 13.5, 'm', INK)
for k, (v, lab) in enumerate([('150+', '累计开发新品'), ('130+', '上市产品'), ('25+', '推动量产产品'), ('10+', '合作OEM工厂')]):
    sx = x + k * 112
    if k: D.line(sx - 16, 436, sx - 16, 482, LINE, 0.6)
    stat(sx, 462, v, lab)

# ====================================================================== 02 profile
D.new_page(); header('01 · PROFILE', '个人概况', '食品产品研发｜轻食 · 烘焙 · 中式产品 · 饮品乳制品 · 酱料｜门店端落地')
D.paragraph(M, 150, '6年+餐饮及食品相关经验，从门店店员、店长转岗产品研发；覆盖西式烘焙、中式糕点与面点、饮品乳制品、酱料与基础组件四大品类，累计开发新品150+款、上市130+款，熟悉从配方试制到OEM量产、门店落地的全流程。',
            13.5, 'r', BODY, maxw=576, leading=21, max_lines=3)
adv = [('品类覆盖广', '西式烘焙、中式糕点与面点、饮品乳制品、酱料与基础组件四大品类；累计开发新品150+款，上市130+款。'),
       ('全流程落地', '熟悉配方试制、成本核算、SOP标准化到OEM/ODM打样与量产衔接；接洽20+家OEM工厂，合作10+家，推动25+款量产。'),
       ('懂门店', '从店员做到店长再转岗研发，兼顾出品效率、操作难度与成本；20+款预制产品将门店出品时间从约5分钟缩短至30–60秒。'),
       ('懂设备、懂视觉', '机电一体化专业背景，能结合工厂设备条件调整工艺；2年+游戏原画经历，「莫奈花园」月销200+、无锡恒隆店蛋糕TOP1。')]
cw_, ch_ = (576 - 12) / 2, 104
for i, (h_, b_) in enumerate(adv):
    x = M + (i % 2) * (cw_ + 12); y = 214 + (i // 2) * (ch_ + 12)
    D.rect((x, y, x + cw_, y + ch_), fill=SURFACE, radius=6)
    D.text(x + 16, y + 24, '0%d' % (i + 1), 9.5, 'm', RED, tracking=1)
    D.text(x + 38, y + 24, h_, 13, 'b', INK)
    D.paragraph(x + 16, y + 46, b_, 11.5, 'r', BODY, maxw=cw_ - 32, leading=16.5, max_lines=3)
D.text(M, 470, '核心能力', 12, 'b', INK)
px = M + 62
for t in ['配方开发', '风味设计', '工艺优化', 'SOP标准化', '成本核算', 'OEM/ODM', '门店落地']:
    tw_ = D.width(t, 11, 'r') + 18
    D.rect((px, 456, px + tw_, 476), fill=SURFACE, radius=10)
    D.text(px + 9, 470, t, 11, 'r', BODY); px += tw_ + 6
assert px <= 640, px
D.line(680, 134, 680, 482, LINE, 0.6)
D.image((720, 134, 896, 346), L('portrait.png'), fx=.5, fy=.4, stroke=None)
D.text(720, 376, '教育背景', 12.5, 'b', INK)
D.text(720, 396, '四川农业大学', 12.5, 'r', INK)
D.text(720, 414, '专科｜机电一体化技术 · 2015 – 2018', 11, 'r', MUTED)
D.text(720, 444, '联系方式', 12.5, 'b', INK)
D.text(720, 463, '17318877700', 12.5, 'm', INK)
D.text(720, 481, 'zhiyzone@foxmail.com', 12, 'r', INK)
footer(2)

# ====================================================================== 03 experience overview
D.new_page(); header('02 · EXPERIENCE', '职业经历')
lx = M + D.text(M, 114, '2018 – 2026 ｜ ', 12.5, 'r', MUTED)
D.rect((lx, 105.5, lx + 9, 114.5), fill=RED, radius=1.5); lx += 15
lx += D.text(lx, 114, '食品研发与门店 · 4段', 12.5, 'r', MUTED) + 16
D.rect((lx, 105.5, lx + 9, 114.5), fill=LIGHT, radius=1.5); lx += 15
D.text(lx, 114, '美术与教育 · 2段', 12.5, 'r', MUTED)
jobs = [  # name, logo, start, end, tags, food?
    ('扬州市一亩草原餐饮有限公司', 'logo_yimu.png', (2026, 2), (2026, 9), '清真食品研发｜饮品乳制品｜OEM生产衔接', True, '一亩草原'),
    ('扬州陈永春餐饮管理有限公司', 'logo_yongchun.png', (2023, 12), (2025, 10), '中式产品研发｜新店落地｜包装与供应链', True, '陈永春'),
    ('苏州欧瑞芙食品科技有限公司', 'logo_jj.png', (2022, 10), (2023, 9), '蛋糕研发｜法式西点｜果酱研发', True, '欧瑞芙'),
    ('苏州元亿嘉合餐饮管理有限公司', 'logo_pei.png', (2019, 11), (2022, 10), '多品类烘焙研发｜门店管理｜新品开发', True, '胚'),
    ('上海厚薄教育科技有限公司', 'logo_houbo.png', (2023, 2), (2023, 11), 'Krenz绘画教室｜助教', False, '厚薄'),
    ('月蚀文化发展（北京）有限公司', 'logo_yueshi.png', (2018, 6), (2019, 9), '游戏原画｜概念视觉', False, '月蚀'),
]
t0, t1 = 2018 + 5 / 12, 2026 + 9 / 12
X = lambda ym: M + ((ym[0] + (ym[1] - 1) / 12) - t0) / (t1 - t0) * CW
D.line(M, 170, W - M, 170, LINE, 0.8)
for yr in range(2019, 2027):
    D.line(X((yr, 1)), 167, X((yr, 1)), 173, LIGHT, 0.6)
    D.text(X((yr, 1)), 186, str(yr), 9, 'm', MUTED, align='center')
for name, logo, s, e, tags, food, short in jobs:
    x0, x1 = X(s), X((e[0], e[1] + 1))
    if food:
        D.rect((x0, 154, x1, 162), fill=RED, radius=2); D.text(x0, 148, short, 9.5, 'm', INK)
    else:
        D.rect((x0, 196, x1, 204), fill=LIGHT, radius=2); D.text(x0, 218, short, 9.5, 'm', MUTED)
cw3 = (CW - 32) / 3; ch3 = 118
for i, (name, logo, s, e, tags, food, short) in enumerate(jobs):
    x = M + (i % 3) * (cw3 + 16); y = 236 + (i // 3) * (ch3 + 12)
    if food: D.rect((x, y, x + cw3, y + ch3), fill=SURFACE, radius=6)
    else: D.rect((x, y, x + cw3, y + ch3), stroke=LINE, radius=6); D.text(x + cw3 - 14, y + 22, '非食品经历', 9, 'm', MUTED, align='right')
    D.image_fit((x + 16, y + 14, x + 100, y + 46), L(logo))
    D.text(x + 16, y + 70, name, 12.5, 'b', INK if food else BODY)
    D.text(x + 16, y + 87, '%d.%02d – %d.%02d' % (s + e), 10.5, 'm', MUTED)
    D.text(x + 16, y + 104, tags, 10.5, 'r', BODY if food else MUTED)
footer(3)

# ====================================================================== 04–07 experience detail
def exp_page(n, label, title, company, meta, logo, stats, cards):
    D.new_page(); header(label, title, None, None, logo)
    D.text(M, 114, company, 13.5, 'b', INK); D.text(M, 132, meta, 12, 'r', MUTED)
    stat_strip(172, stats)
    cards_2x2(216, 478, cards)
    footer(n)

exp_page(4, '02 · EXPERIENCE', '清真食品研发与生产落地', '扬州市一亩草原餐饮有限公司', '2026.02 – 2026.09｜清真产品 + 饮品乳制品 + 面点 + OEM生产衔接', 'logo_yimu_big.png',
    [('20+', '开发新品，全部上市'), ('20+', '接洽评估OEM工厂'), ('10+', '最终合作工厂'), ('25+', '推动产品量产')],
    [('产品研发', '负责清真饮品、乳制品、包子面点及清真甜点研发，开发新品20+款并全部上市；结合线上及门店渠道定位，调整配方、风味与产品形态。'),
     ('配方与工艺优化', '跟进量产过程中的工艺与品质表现，根据工厂设备条件调整配方与工艺参数，使产品在规模化生产中保持与研发样品一致的口感与外观。'),
     ('OEM对接与项目推进', '主导OEM工厂筛选：接洽评估20+家，从资质、清真认证、产能及品控等方面筛选，最终合作10+家；组织多轮打样与样品确认，推动25+款产品量产。'),
     ('产品与渠道协同', '根据线上及门店渠道需求，调整产品规格、包装与储运形式（冷冻/冷藏、单份装/组合装），对接厂家确认样品与生产标准，适配不同销售场景。')])

exp_page(5, '02 · EXPERIENCE', '中式产品研发与门店项目落地', '扬州陈永春餐饮管理有限公司', '2023.12 – 2025.10｜中式产品 + 新店落地 + 包装供应链 + 外部工厂', 'logo_yongchun.png',
    [('40+', '开发新品，上新35+款'), ('6家', '新门店项目落地'), ('20+', '预制产品，出品缩至30–60秒'), ('20%', '包装成本平均降低')],
    [('产品研发', '研发中式糕点、酥点、糖水及包子面点，开发新品40+款，上新35+款；研发醪糟黑芝麻酸奶等门店甜品，兼顾风味与出品操作。'),
     ('门店项目落地', '参与6家新门店项目落地，结合产品特点协同空间布局、产品展示、陈列、美陈与展示器具选型，兼顾视觉呈现和实际出品。'),
     ('包装与供应商', '对接包装及物料供应商，完成50+款产品包装方案；协调包装形式、陈列器具与物料选型，提升产品视觉呈现，包装成本平均降低20%。'),
     ('开发预制产品', '对接外部工厂开发20+款预制产品（如饮品预制包），经5轮打样后落地；门店出品时间由约5分钟缩短至30–60秒，降低对人员技术的依赖。')])

exp_page(6, '02 · EXPERIENCE', '蛋糕与创意西点产品研发', '苏州欧瑞芙食品科技有限公司（Jessy & Jerry · 卷心卷意）', '2022.10 – 2023.09｜蛋糕造型 + 创意产品 + 风味与果酱研发', 'logo_jj.png',
    [('30+', '开发新品，25+款上市'), ('15+', '新风味组合，全部上市'), ('200+', '「莫奈花园」月销量'), ('TOP1', '无锡恒隆店蛋糕品类销量')],
    [('产品方向', '负责奶油蛋糕、造型蛋糕、现代法式西点及创意艺术蛋糕研发，开发新品30+款，其中25+款上市；兼顾配方试制、结构稳定性与实际出品。'),
     ('风味开发', '开发15+种新风味组合并全部上市；「莫奈花园」月销200+，成为无锡恒隆店蛋糕品类销量TOP1，并作为常驻单品持续销售。'),
     ('果酱与量产对接', '负责果酱配方设计与自有加工厂量产对接，控制糖度、pH与果胶体系，热灌装后成品供应门店，保证门店夹层与淋酱风味稳定。'),
     ('产品造型与呈现', '发挥美术背景优势，开发产品造型与视觉风格，兼顾风味搭配、稳定性和食用体验；参与产品陈列与展示方案，提升门店视觉呈现。')])

exp_page(7, '02 · EXPERIENCE', '门店管理与多品类烘焙研发', '苏州元亿嘉合餐饮管理有限公司 · 品牌「胚」', '2019.11 – 2022.10｜店员 → 后厨负责人 → 店长 → 产品研发｜门店运营 + 多品类西式烘焙研发', 'logo_pei.png',
    [('15+', '人团队管理'), ('40+万', '门店月营业额'), ('60+', '开发新品，约50款上市'), ('10+', '城市门店与产品调研')],
    [('团队管理与门店对接', '从店员晋升为后厨负责人、店长，任职期间转向产品研发；管理15+人团队，负责排班、后厨出品与日常运营，月营业额40+万元。'),
     ('多品类烘焙研发', '研发涵盖面包、蛋糕、慕斯、开酥、派塔、法式甜点、冷冻甜品及巧克力等，开发新品60+款，约50款上市；兼顾风味、操作与门店出品效率。'),
     ('风味与基础组件', '开发果酱、坚果酱、夹心、淋面及糖浆等基础组件；负责配方设计、工艺调试与自有小型加工厂生产对接，成品供应门店，结合应用调整风味、口感与结构。'),
     ('市场调研与新品开发', '赴10+个城市开展门店与产品调研，结合当地口味偏好与产品特点，其中20+款新品基于调研成果开发，为上新及风味调整提供参考。')])

# ====================================================================== 08 store-side R&D process
D.new_page(); header('03 · STORE R&D', '门店端产品研发与落地', '从概念到门店推广的全流程跟进｜门店运营经验 + 预制产品 + SOP标准化 + 试销跟进 + 合规与保质期')
steps = [('概念定位', None), ('配方试制', None), ('成本核算', 'SOP固化'), ('门店小试', None), ('门店试销', '驻店跟进'), ('区域 / 全国', '门店推广'), ('数据复盘', '菜单迭代')]
sw = (CW - 6 * 10) / 7
D.line(M, 142, W - M, 142, LINE, 0.8)
for i, (s1, s2) in enumerate(steps):
    x = M + i * (sw + 10)
    D.circle(x + 3, 142, 3.2, fill=RED)
    D.text(x, 162, '0%d' % (i + 1), 9.5, 'm', RED, tracking=1)
    D.text(x, 182, s1, 12.5, 'm', INK)
    if s2: D.text(x, 199, s2, 11, 'r', MUTED)
cards_2x2(222, 478, [
    ('门店出品导向的配方与SOP', '从店员、店长转岗研发，配方按门店设备条件、人员操作水平与出餐效率落地；开发20+款预制产品，门店出品时间由约5分钟缩短至30–60秒。'),
    ('门店小试、试销与驻店跟进', '参与6家新门店项目落地，现场协同设备适配、出品流程、陈列与器具选型；预制产品经5轮打样后上线；赴10+个城市做门店调研，20+款新品基于调研开发。'),
    ('成本控制与供应链协同', '配方成本核算与研发记录标准化；对接包装及物料供应商，完成50+款产品包装方案，包装成本平均降低20%；OEM/ODM工厂按资质、产能、品控筛选。'),
    ('合规、品控与保质期', '对接清真认证、SC资质与品控评估；酱料以Brix/pH终点判定、≥85℃热灌装、批次留样控制；按未开封/开封后分别设定保质期与冷链/温控储运条件。')])
footer(8)

# ====================================================================== 09 skills
D.new_page(); header('04 · SKILLS', '专业技能与工具', '研发与生产技能 · 办公应用 · 专业补充')
tick(M, 142); D.text(M + 12, 154, '研发与生产技能', 13, 'b', INK)
skills = [('配方开发', '品类定位 · 原料筛选 · 风味组合'), ('工艺调整', '试制评估 · 工艺测试 · 配方优化'), ('生产衔接', 'OEM/ODM打样 · 样品确认 · 量产跟进'),
          ('成本与标准化', '配方成本 · SOP · 研发记录'), ('项目协同', '包装物料 · 供应商 · 门店落地'), ('产品视觉', '造型 · 配色 · 陈列与展示')]
for i, (n_, d_) in enumerate(skills):
    y = 176 + i * 50
    D.text(M, y + 16, '0%d' % (i + 1), 10, 'm', RED, tracking=1)
    D.text(M + 30, y + 16, n_, 13.5, 'b', INK)
    D.text(M + 30, y + 34, d_, 11.5, 'r', MUTED)
    D.line(M, y + 46, M + 384, y + 46, LINE, 0.6)
xr = 496
tick(xr, 142); D.text(xr + 12, 154, '办公应用', 13, 'b', INK)
for i, (n_, d_) in enumerate([('Excel', '配方表、成本核算与研发报表'), ('Word', '研发文档、SOP与试验记录'), ('PowerPoint', '产品提案、项目汇报与培训材料'), ('Visio', '工艺流程图与流程梳理')]):
    y = 184 + i * 28
    D.text(xr, y, n_, 12.5, 'b', INK); D.text(xr + 110, y, d_, 12, 'r', BODY)
    D.line(xr, y + 10, W - M, y + 10, LINE, 0.6)
tick(xr, 318); D.text(xr + 12, 330, '专业补充', 13, 'b', INK)
for i, (n_, d_) in enumerate([('设备与产线', '机电专业背景，能结合设备条件调整工艺参数'), ('酱料工艺', '糖度（Brix）、pH与果胶体系控制，热灌装与冷藏储运'), ('清真合规', 'OEM工厂清真认证、资质、产能与品控评估')]):
    y = 360 + i * 28
    D.text(xr, y, n_, 12.5, 'b', INK); D.text(xr + 110, y, d_, 12, 'r', BODY)
    D.line(xr, y + 10, W - M, y + 10, LINE, 0.6)
footer(9)

# ====================================================================== 10 sauce table
D.new_page(); header('05 · R&D CASE', '酱料研发与工厂生产衔接', '胚 · 欧瑞芙｜负责配方设计、工艺调试与自有小型加工厂量产对接，成品供应门店；夹层锅小批量生产，单批约20–30 kg')
D.rect((M, 134, W - M, 160), fill=SURFACE, radius=4)
D.text(M + 12, 151, '果酱工艺', 11, 'b', RED)
flow = ['原料验收', '清洗切丁 · 护色', '分次加糖熬制', '加果胶 · 调酸', 'Brix/pH终点判定', '≥85℃热灌装', '倒置 · 冷却', '批次留样', '入库配送门店']
x = M + 72
for i, s in enumerate(flow):
    x += D.text(x, 151, s, 10.5, 'r', INK) + 6
    if i < len(flow) - 1: x += D.text(x, 151, '→', 10.5, 'm', RED) + 6
assert x <= W - M, x
LX, DX = M, 150.0; colw = (W - M - DX) / 5
sauces = [('p09_x75.jpeg', '草莓果酱'), ('p09_x74.jpeg', '香草凤梨酱'), ('p09_x73.jpeg', '蜜桃果酱'), ('p09_x155.jpeg', '开心果酱'), ('p09_x76.jpeg', '辣牛肉酱')]
for k, (p, n_) in enumerate(sauces):
    x = DX + k * colw
    D.image((x, 172, x + 140, 272), I(p))
    D.text(x + 70, 289, n_, 12.5, 'b', INK, align='center')
rows = [('应用场景', None), ('关键指标', None), ('凝胶与稳定', None), ('工艺要点', None), ('灌装与杀菌', None), ('保质期', '未开封｜开封后')]
data = [
    [['蛋糕夹层 · 面包夹心', '酸奶/饮品淋酱'], ['60–65 °Bx ｜ pH 3.2–3.5'], ['高酯果胶 + 柠檬酸', '保留果粒口感'], ['分次加糖、缩短熬煮', '保色保香'], ['≥85℃热灌装、倒置', '冷藏储存更保色'], ['未开封 阴凉避光6个月', '开封后 冷藏14天']],
    [['挞类/酥点馅料', '面包夹心'], ['62–66 °Bx ｜ pH 3.2–3.5'], ['高酯果胶 + 少量变性淀粉', '提升耐烘烤性'], ['≥85℃熬煮灭活凤梨蛋白酶', '防止分解奶油；香草后加'], ['≥85℃热灌装、倒置', '常温避光储存'], ['未开封 阴凉避光6个月', '开封后 冷藏14天']],
    [['饮品底料（果茶/气泡）', '蛋糕夹层'], ['58–62 °Bx ｜ pH 3.3–3.5'], ['高酯果胶 + 柠檬酸', '果块保形不碎烂'], ['切块即护色（柠檬酸/维C）', '防止褐变'], ['≥85℃热灌装、倒置', '建议冷藏，减缓褐变'], ['未开封 阴凉避光4个月', '开封后 冷藏10天']],
    [['蛋糕抹面 · 夹心', '可颂/泡芙内馅'], ['Aw ≤ 0.6（油基坚果酱）', '监控酸价、过氧化值'], ['开心果仁 + 糖粉 + 奶粉', '植物油，防止油脂析出'], ['低温烘烤保留翠绿色', '多次精磨，细腻无颗粒'], ['密封避光灌装', '≤20℃存放，冷藏会变硬'], ['未开封 阴凉避光6个月', '开封后 密封30天，勿沾水']],
    [['咸面包/贝果夹馅', '简餐拌酱'], ['低酸食品（pH>4.6）', '按商业无菌控制'], ['牛肉粒 + 辣椒 + 豆瓣', '香辛料，油脂包裹'], ['炒制收干水分', '表面油层隔氧'], ['封口后121℃杀菌', '（15′–30′–15′）反压冷却'], ['未开封 常温12个月', '开封后 冷藏7天']],
]
RH, TY = 30.0, 298.0
for r, (lab, lab2) in enumerate(rows):
    y = TY + r * RH
    if r % 2 == 0: D.rect((M, y, W - M, y + RH), fill=SURFACE)
    D.line(M, y + RH, W - M, y + RH, LINE, 0.5)
    if lab2:
        D.text(M + 8, y + 12.5, lab, 10.5, 'b', INK); D.text(M + 8, y + 24.5, lab2, 9.5, 'b', INK)
    else:
        D.text(M + 8, y + 19, lab, 10.5, 'b', INK)
    for c in range(5):
        cell = data[c][r]; x = DX + c * colw
        if len(cell) == 1:
            D.text(x, y + 19, cell[0], 10.5, 'r', BODY)
        else:
            D.text(x, y + 12.5, cell[0], 10.5, 'r', BODY); D.text(x, y + 24.5, cell[1], 10.5, 'r', BODY)
        for t in cell: assert D.width(t, 10.5) <= colw - 6, (t, D.width(t, 10.5))
footer(10)

# ====================================================================== 11 轻食
gallery('06 · PRODUCTS', '轻食 / 沙拉 / 酱汁', '三明治 · 沙拉碗 · 塔可 · 烤串 · 轻食酱汁｜门店端轻食产品',
    [dict(path=P('a5dcde27-image.jpg'), name='牛油果三文鱼三明治', fy=.42), dict(path=P('d9e2a08c-image.jpg'), name='鲜虾牛油果藜麦碗'),
     dict(path=P('bac0b659-image.jpg'), name='缤纷果蔬沙拉盒', fy=.55), dict(path=P('e71dc291-image.jpg'), name='菠萝彩椒鸡肉串', fy=.55),
     dict(path=P('a111c697-image.jpg'), name='鲜虾芒果塔可', fy=.5), dict(path=P('33aa635c-image.jpg'), name='轻食酱汁与抹酱')],
    note=('轻食 · 门店方向', '按门店出餐方式设计的轻食组合', '三明治、沙拉碗、塔可、烤串与配套酱汁（牛油果酱、蜂蜜芥末酱、奶油奶酪抹酱）；以现制、复热、组装三类门店操作方式为前提设计配方与组合，兼顾出餐效率与成本。'))
footer(11)

# ====================================================================== 12 包子 / 中式面点
D.new_page(); header('06 · PRODUCTS', '包子 / 中式面点', '一亩草原 · 陈永春｜均已上市销售')
photo(cell_rect(0, 0, cols=2, rows=2), I('p10_x156.jpeg'), '清真鲜牛肉包', halal=True)
photo(cell_rect(2, 0, rows=2), I('p10_x157.jpeg'), '港式叉烧包', note='陈永春', fy=.5)
photo(cell_rect(3, 0), I('p10_x158.jpeg'), '糖火烧', halal=True)
photo(cell_rect(3, 1), I('p10_x159.jpeg'), '芝麻烧饼', halal=True)
footer(12)

# ====================================================================== 13 饮品 / 乳制品
gallery('06 · PRODUCTS', '饮品 / 乳制品', '一亩草原 · 陈永春｜均已上市销售',
    [dict(path=I('p11_x88.jpeg'), name='清真手工奶皮子酸奶', halal=True), dict(path=I('p11_x89.jpeg'), name='芒芒酸奶'), dict(path=I('p11_x86.jpeg'), name='奇亚籽羽衣甘蓝酸奶'),
     dict(path=I('p11_x87.jpeg'), name='小麦草青提'), dict(path=I('p11_x164.jpeg'), name='野莓桑雾'), dict(path=I('p11_x85.jpeg'), name='蜜瓜气泡特调', region=(.3, 0, .7, 1), fy=.45)],
    note=('一亩草原 · 清真', '清真饮品与乳制品', '负责清真饮品、乳制品及清真甜点研发，开发新品20+款并全部上市；结合线上及门店渠道定位调整配方、风味与产品形态，并按冷冻/冷藏、单份装/组合装等储运形式对接工厂生产。'))
footer(13)

# ====================================================================== 14 蛋糕（一）
gallery('06 · PRODUCTS', '蛋糕（一）', '欧瑞芙 · 胚｜均已上市销售',
    [dict(path=I('p12_x93.jpeg'), name='南法暮色'), dict(path=I('p12_x92.jpeg'), name='维也纳榛巧'), dict(path=I('p12_x95.jpeg'), name='紫晶葡萄无花果丝绒蛋糕'),
     dict(path=I('p12_x94.jpeg'), name='芒柚双生'), dict(path=I('p12_x91.jpeg'), name='莫奈花园', tag='月销200+ · 无锡恒隆店 TOP1'), dict(path=I('p12_x165.jpeg'), name='天鹅湖蛋糕')],
    note=('欧瑞芙 · JESSY & JERRY', '奶油蛋糕与创意艺术蛋糕', '负责奶油蛋糕、造型蛋糕、现代法式西点及创意艺术蛋糕研发，开发新品30+款，25+款上市；「莫奈花园」月销200+，成为无锡恒隆店蛋糕品类销量TOP1常驻单品。'))
footer(14)

# ====================================================================== 15 蛋糕（二）
gallery('06 · PRODUCTS', '蛋糕（二）', '胚｜均已上市销售',
    [dict(path=I('p13_x105.jpeg'), name='抹茶草莓香缇蛋糕'), dict(path=I('p13_x101.jpeg'), name='草莓开心果蛋糕'), dict(path=I('p13_x104.jpeg'), name='日本柚子榛子磅蛋糕'),
     dict(path=I('p13_x166.jpeg'), name='桑葚荔枝奶油蛋糕卷'), dict(path=I('p13_x103.jpeg'), name='提拉米苏'), dict(path=I('p13_x102.jpeg'), name='咖啡巧克力巴斯克')],
    note=('胚 · PEI CAKE', '多品类西式烘焙', '研发涵盖面包、蛋糕、慕斯、开酥、派塔、法式甜点、冷冻甜品及巧克力等，开发新品60+款，约50款上市；兼顾风味、操作与门店出品效率，并开发果酱、坚果酱、夹心、淋面等基础组件。'))
footer(15)

# ====================================================================== 16 法式西点 / 面包 / 伴手礼
gallery('06 · PRODUCTS', '法式西点 / 面包 / 伴手礼', '胚｜均已上市销售',
    [dict(path=I('p14_x111.jpeg'), name='巧克力水果塔', region=(.12, 0, .88, 1)), dict(path=I('p14_x112.jpeg'), name='水果脆皮泡芙卷'), dict(path=I('p14_x107.jpeg'), name='巧克力闪电泡芙'), dict(path=I('p14_x167.jpeg'), name='歌剧院'),
     dict(path=I('p14_x168.jpeg'), name='香煎黑胡椒爆蛋吐司'), dict(path=I('p14_x108.jpeg'), name='罗米亚巧克力脆片曲奇'), dict(path=I('p14_x110.jpeg'), name='香酥叶子饼干'), dict(path=I('p14_x109.jpeg'), name='乳酪夹心饼干')])
footer(16)

# ====================================================================== 17 中式糕点 / 点心
gallery('06 · PRODUCTS', '中式糕点 / 点心', '胚 · 陈永春｜均已上市销售',
    [dict(path=I('p15_x116.jpeg'), name='开心果柚子拿酥月饼'), dict(path=I('p15_x119.jpeg'), name='抹茶山药茉莉花饼'), dict(path=I('p15_x115.jpeg'), name='樱花酥饼'),
     dict(path=I('p15_x114.jpeg'), name='抹茶茉莉绿豆饼'), dict(path=I('p15_x118.jpeg'), name='芡实糕'), dict(path=I('p15_x117.jpeg'), name='粽子')],
    note=('陈永春 · 永春园', '中式糕点与酥点', '研发中式糕点、酥点、糖水及包子面点，开发新品40+款，上新35+款；完成50+款产品包装方案，协调包装形式、陈列器具与物料选型，包装成本平均降低20%。'))
footer(17)

# ====================================================================== 18 中式糖水 / 冰淇淋
gallery('06 · PRODUCTS', '中式糖水 / 冰淇淋', '胚 · 陈永春｜均已上市销售',
    [dict(path=I('p16_x121.jpeg'), name='醪糟黑芝麻酸奶', region=(.3, 0, .7, 1)), dict(path=I('p16_x169.jpeg'), name='雪芋琉璃盏', region=(.3, 0, .7, 1)),
     dict(path=I('p16_x123.jpeg'), name='青提荔枝银耳羹', region=(.27, 0, .73, 1)), dict(path=I('p16_x122.jpeg'), name='日式酱油冰淇淋', region=(.3, 0, .7, 1), fy=.45),
     dict(path=I('p16_x124.jpeg'), name='杨梅雪芭'), dict(path=I('p16_x125.jpeg'), name='茉莉飘雪冰淇淋', region=(.28, 0, .72, 1))],
    note=('陈永春 · 胚', '门店甜品与冰品', '研发醪糟黑芝麻酸奶等门店甜品，兼顾风味与出品操作；在「胚」期间研发涵盖冷冻甜品等品类，开发新品60+款，约50款上市。'))
footer(18)

# ====================================================================== 19 end
D.new_page()
mosaic(540, [(I('p12_x95.jpeg'), .5, .5), (I('p15_x119.jpeg'), .5, .5), (I('p16_x124.jpeg'), .5, .5), (I('p14_x107.jpeg'), .5, .5)])
x = 80
D.text(x, 96, 'THANK YOU', 10, 'm', RED, tracking=2)
D.text(x, 236, '感谢阅览', 48, 'b', INK)
D.text(x, 274, '期待进一步交流', 18, 'm', INK)
D.rect((x, 292, x + 56, 294), fill=RED)
D.text(x, 340, '惠志杨 · 食品产品研发', 14, 'm', INK)
D.text(x, 366, '17318877700', 13.5, 'r', BODY)
D.text(x, 388, 'zhiyzone@foxmail.com', 13.5, 'r', BODY)
D.text(x, 410, '现居江苏扬州', 13, 'r', MUTED)

D.save(OUT)
print('saved', OUT, 'pages', D.pages)
