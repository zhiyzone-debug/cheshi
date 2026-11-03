"""Edit page 9 (酱料研发与工厂生产衔接) table + flow bar of the portfolio PDF.

Usage: python3 -I edit_p9.py IN.pdf OUT.pdf FONTDIR [B]
FONTDIR holds NotoSansSC-Regular.otf / NotoSansSC-Bold.otf (or swap in msyh files).
Pass 'B' as 4th arg to use 方案B for 辣牛肉酱.
"""
import sys, re, json, os
import pymupdf as fz
from fontTools.ttLib import TTFont
from fontTools import subset

SRC, DST, FONTDIR = sys.argv[1:4]
PLAN = sys.argv[4] if len(sys.argv) > 4 else 'A'
WORK = os.path.dirname(os.path.abspath(DST))

# ---------------------------------------------------------------- content
LABELS = ['应用场景', '关键指标', '凝胶与稳定', '工艺要点', '灌装与杀菌',
          ['保质期', '未开封/开封后']]          # label of last row: see note in report
COLS = [
    [  # 草莓果酱
        ['蛋糕夹层 · 面包夹心', '酸奶/饮品淋酱'],
        ['60–65 °Bx ｜ pH 3.2–3.5'],
        ['高酯果胶 + 柠檬酸', '保留果粒口感'],
        ['分次加糖、缩短熬煮', '保色保香'],
        ['≥85℃热灌装、倒置', '冷藏储存更保色'],
        ['未开封 阴凉避光6个月', '开封后 冷藏14天'],
    ],
    [  # 香草凤梨酱
        ['挞类/酥点馅料', '面包夹心'],
        ['62–66 °Bx ｜ pH 3.2–3.5'],
        ['高酯果胶 + 少量变性', '淀粉，提升耐烘烤性'],
        ['≥85℃熬煮灭活凤梨蛋白酶', '防止分解奶油；香草后加'],
        ['≥85℃热灌装、倒置', '常温避光储存'],
        ['未开封 阴凉避光6个月', '开封后 冷藏14天'],
    ],
    [  # 蜜桃果酱
        ['饮品底料（果茶/气泡）', '蛋糕夹层'],
        ['58–62 °Bx ｜ pH 3.3–3.5'],
        ['高酯果胶 + 柠檬酸', '果块保形不碎烂'],
        ['切块即护色（柠檬酸/', '维C），防止褐变'],
        ['≥85℃热灌装、倒置', '建议冷藏，减缓褐变'],
        ['未开封 阴凉避光4个月', '开封后 冷藏10天'],
    ],
    [  # 开心果酱
        ['蛋糕抹面 · 夹心', '可颂/泡芙内馅'],
        ['Aw ≤ 0.6（油基坚果酱）', '监控酸价、过氧化值'],
        ['开心果仁 + 糖粉 + 奶粉', '植物油，防止油脂析出'],
        ['低温烘烤保留翠绿色', '多次精磨，细腻无颗粒'],
        ['密封避光灌装', '≤20℃存放，冷藏会变硬'],
        ['未开封 阴凉避光6个月', '开封后 密封30天，勿沾水'],
    ],
    [  # 辣牛肉酱 方案A
        ['咸面包/贝果夹馅', '简餐拌酱'],
        ['低酸食品（pH>4.6）', '按商业无菌控制'],
        ['牛肉粒 + 辣椒 + 豆瓣', '香辛料，油脂包裹'],
        ['炒制收干水分', '表面油层隔氧'],
        ['封口后121℃杀菌', '（15′–30′–15′）反压冷却'],
        ['未开封 常温12个月', '开封后 冷藏7天'],
    ],
]
if PLAN == 'B':
    COLS[4][1] = ['低酸食品（pH>4.6）', '短保，全程冷链']
    COLS[4][4] = ['≥85℃热灌装', '0–4℃冷藏储运']
    COLS[4][5] = ['未开封 冷藏14天', '开封后 冷藏3天']

# ---------------------------------------------------------------- geometry (PDF user space, y up)
TABLE_TOP = 241.0          # unchanged (top of first row)
ROW_H = 31.0               # was 35 (two-line rows) / 21.5 (one-line rows)
COL_X = [148, 300.4, 452.8, 605.2, 757.6]
COL_RIGHT = [286.4, 438.8, 591.2, 743.6, 896.0]   # image/column right edges
LABEL_X = 72
DATA_SIZE, LABEL_SIZE = 10.8, 11.0
LINE1, LINE2 = 12.15, 25.65    # baseline offsets from row top (orig 14.15/27.65 in 35pt rows)
LABEL_1L = 18.9                # single-line label baseline offset (orig 20.9 in 35pt rows)
C_DATA = (.270588, .282353, .298039)
C_LABEL = (.141176, .141176, .14902)
C_FILL = (.980392, .972549, .968627)
C_RULE = (.92549, .917647, .909804)
FOOTER_Y = 43.0

# ---------------------------------------------------------------- fonts: subset Noto, map · to proportional glyph
def make_subset(src, text, out):
    f = TTFont(src)
    cmap = f.getBestCmap()
    # proportional middle dot via 'pwid'/'palt'-style GSUB single substitution, if present
    alt = None
    if 'GSUB' in f:
        g = f['GSUB'].table
        for fr in g.FeatureList.FeatureRecord:
            if fr.FeatureTag in ('pwid',):
                for li in fr.Feature.LookupListIndex:
                    lk = g.LookupList.Lookup[li]
                    for st in lk.SubTable:
                        m = getattr(st, 'mapping', None) or getattr(getattr(st, 'ExtSubTable', None), 'mapping', None)
                        if m and cmap.get(0xB7) in m:
                            alt = m[cmap[0xB7]]
    opts = subset.Options(); opts.layout_features = []; opts.name_IDs = ['*']
    opts.notdef_outline = True
    ss = subset.Subsetter(opts)
    gl = [cmap[ord(c)] for c in set(text)] + ([alt] if alt else [])
    ss.populate(glyphs=gl, unicodes=[ord(c) for c in set(text)])
    ss.subset(f)
    if alt:
        for t in f['cmap'].tables:
            if 0xB7 in t.cmap:
                t.cmap[0xB7] = alt
    f.save(out)
    return TTFont(out)

all_data = ''.join(''.join(l) for col in COLS for cell in col for l in cell)
all_data = ''.join(c for c in all_data if c not in '·≥≤')
all_lab = ''.join(x if isinstance(x, str) else ''.join(x) for x in LABELS)
REG = os.path.join(WORK, 'p9_reg_subset.otf')
BLD = os.path.join(WORK, 'p9_bold_subset.otf')
SYM = set('·≥≤')
SYMF = os.path.join(WORK, 'p9_sym_subset.otf')
fsym = make_subset(os.path.join(FONTDIR, 'Inter-Regular.otf'), ''.join(SYM), SYMF)
freg = make_subset(os.path.join(FONTDIR, 'NotoSansSC-Regular.otf'), all_data, REG)
fbld = make_subset(os.path.join(FONTDIR, 'NotoSansSC-Bold.otf'), all_lab, BLD)

def width(ft, s, size):
    if ft is freg and any(c in SYM for c in s):
        return sum(width(fsym if c in SYM else freg, c, size) for c in s)
    cm = ft.getBestCmap(); hm = ft['hmtx']; upm = ft['head'].unitsPerEm
    missing = [c for c in s if ord(c) not in cm]
    assert not missing, ('missing glyphs', missing)
    return sum(hm[cm[ord(c)]][0] for c in s) / upm * size

# ---------------------------------------------------------------- open & cut old table from page 9 stream
doc = fz.open(SRC)
page = doc[8]
assert len(page.get_contents()) == 1
cx = page.get_contents()[0]
s = doc.xref_stream(cx)
start_marker = b'n .980392 .972549 .968627 rg 64 206 832 35 re f*'
i = s.index(start_marker)
assert s.rstrip().endswith(b'Q')
j = s.rstrip().rindex(b'Q')
new = s[:i] + s[j:]

# ---------------------------------------------------------------- flow bar: "Brix终点判定" -> "Brix/pH终点判定"
F = {}
for name, xr in (('F2+0', 12), ('F2+1', 16)):
    o = doc.xref_object(xr)
    w = [float(v) for v in re.search(r'/Widths \[([^\]]*)\]', o).group(1).split()]
    F[name] = w
old_brix = b'<42726978bc8f>Tj'
assert new.count(old_brix) == 1
# '/', 'p', 'H' exist in subset F2+0 at their ASCII codes (used in "pH" / "/")
new = new.replace(old_brix, b'<427269782f7048bc8f>Tj')
extra = (F['F2+0'][0x2f] + F['F2+0'][0x70] + F['F2+0'][0x48]) / 1000 * 11.2

# flow bar items: re-space every element after the first so last item ends where it did
flow = re.compile(rb'(BT/F2\+[01] 11\.2 Tf )([\d.]+)( 398 TD)')
items = list(flow.finditer(new))
xs = [float(m.group(2)) for m in items]
assert len(xs) == 17 and xs[0] == 136.0, xs
# each element k>=1 sits after k gaps of 6pt; shrink gaps evenly to absorb `extra`
gap_old = 6.0
n_gaps = 16
delta = extra / n_gaps                     # gap reduction
# element index of Brix item is 8 (0-based): items after it also shift by +extra
out = bytearray(); last = 0
for k, m in enumerate(items):
    x = xs[k] - k * delta + (extra if k > 8 else 0)
    out += new[last:m.start(2)] + (b'%.4f' % x)
    last = m.end(2)
out += new[last:]
new = bytes(out)
gap_new = gap_old - delta

doc.update_stream(cx, new)

# ---------------------------------------------------------------- draw new table
page.insert_font(fontname='NotoR', fontfile=REG)
page.insert_font(fontname='NotoB', fontfile=BLD)
page.insert_font(fontname='SymR', fontfile=SYMF)

def put_data(x, y, t):
    run = ''; sym = None
    for ch in t + '\0':
        is_sym = ch in SYM
        if ch == '\0' or (run and is_sym != sym):
            ft = fsym if sym else freg
            page.insert_text((x, y), run, fontname='SymR' if sym else 'NotoR', fontsize=DATA_SIZE, color=C_DATA)
            x += width(ft, run, DATA_SIZE); run = ''
        if ch != '\0':
            run += ch; sym = is_sym
H = page.rect.height
report = []
shape = page.new_shape()
for r in range(6):
    top = TABLE_TOP - r * ROW_H
    bot = top - ROW_H
    if r % 2 == 0:
        shape.draw_rect(fz.Rect(64, H - top, 896, H - bot))
        shape.finish(fill=C_FILL, color=None, width=0)
    shape.draw_line(fz.Point(64, H - bot), fz.Point(896, H - bot))
    shape.finish(color=C_RULE, width=0.5)
shape.commit(overlay=True)

for r in range(6):
    top = TABLE_TOP - r * ROW_H
    lab = LABELS[r]
    if isinstance(lab, str):
        wdt = width(fbld, lab, LABEL_SIZE)
        assert LABEL_X + wdt <= COL_X[0] - 4, (lab, wdt)
        page.insert_text((LABEL_X, H - (top - LABEL_1L)), lab, fontname='NotoB', fontsize=LABEL_SIZE, color=C_LABEL)
    else:
        for k, t in enumerate(lab):
            wdt = width(fbld, t, LABEL_SIZE)
            assert LABEL_X + wdt <= COL_X[0] - 4, (t, wdt)
            page.insert_text((LABEL_X, H - (top - (LINE1, LINE2)[k])), t, fontname='NotoB', fontsize=LABEL_SIZE, color=C_LABEL)
    for c in range(5):
        cell = COLS[c][r]
        assert 1 <= len(cell) <= 2
        lines = cell if len(cell) == 2 else cell
        offs = (LINE1, LINE2) if len(cell) == 2 else (LABEL_1L - 0.0,)
        for k, t in enumerate(lines):
            wdt = width(freg, t, DATA_SIZE)
            room = COL_RIGHT[c] - COL_X[c] - 4
            report.append((r, c, t, round(wdt, 1), round(room, 1)))
            assert wdt <= room, (t, wdt, room)
            put_data(COL_X[c], H - (top - offs[k]), t)

bottom = TABLE_TOP - 6 * ROW_H
assert bottom - FOOTER_Y >= 8, bottom
doc.save(DST, garbage=1, deflate=False)
print('flow extra %.2f, gap %.2f -> %.2f; table bottom y=%.1f (footer rule %.1f)' % (extra, gap_old, gap_new, bottom, FOOTER_Y))
for x in report:
    print(x)
