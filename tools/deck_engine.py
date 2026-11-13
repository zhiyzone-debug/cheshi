"""Small layout engine on top of PyMuPDF: mixed CJK/Latin text, wrapping,
cover-cropped images, shapes. Fonts are embedded once per document as
CID TrueType (FontFile2) — the format every viewer, including iOS, renders.
"""
import os, re, io, hashlib
import pymupdf as fz
from PIL import Image, ImageOps

W, H = 960.0, 540.0
M = 64.0                      # side margin
CW = W - 2 * M                # content width = 832

def rgb(hexs):
    hexs = hexs.lstrip('#'); return tuple(int(hexs[i:i + 2], 16) / 255 for i in (0, 2, 4))

INK = rgb('1F2124'); BODY = rgb('3D4045'); MUTED = rgb('80848B'); LIGHT = rgb('A9ADB3')
RED = rgb('B32637'); RED_SOFT = rgb('F7ECED'); SURFACE = rgb('F7F5F2'); SURFACE2 = rgb('EFECE7')
LINE = rgb('E4E1DC'); WHITE = (1, 1, 1)

LATIN_OK = re.compile(r'[\x20-\x7e -ÿ–—‘’“”…′→℃≤≥°]')
CLOSE_PUNCT = set('）》」』、，。；：！？％）]}>,.;:!?)%')
OPEN_PUNCT = set('（《「『([{<')

class Deck:
    def __init__(self, fontdir, imgcache):
        self.doc = fz.open()
        self.fontdir = fontdir
        self.imgcache = imgcache; os.makedirs(imgcache, exist_ok=True)
        F = lambda n: fz.Font(fontfile=os.path.join(fontdir, n))
        self.fonts = {
            ('cjk', 'r'): F('NotoSansSC-Regular.ttf'), ('cjk', 'm'): F('NotoSansSC-Medium.ttf'), ('cjk', 'b'): F('NotoSansSC-Bold.ttf'),
            ('lat', 'r'): F('Inter-Regular.ttf'), ('lat', 'm'): F('Inter-Medium.ttf'), ('lat', 'b'): F('Inter-SemiBold.ttf'),
            ('lat', 'x'): F('Inter-Bold.ttf'), ('cjk', 'x'): F('NotoSansSC-Bold.ttf'),
        }
        self.page = None; self.writers = {}; self.pages = 0

    # ---------------------------------------------------------------- pages
    def new_page(self):
        self.flush()
        self.page = self.doc.new_page(width=W, height=H); self.pages += 1
        return self.page

    def flush(self):
        for (color,), tw in self.writers.items():
            tw.write_text(self.page)
        self.writers = {}

    def save(self, path):
        self.flush()
        self.doc.subset_fonts()
        self.doc.save(path, garbage=4, deflate=True, deflate_images=False)

    # ---------------------------------------------------------------- text
    def _runs(self, text, weight):
        """Split text into (font, substring) runs: Latin→Inter, else Noto."""
        runs = []
        for ch in text:
            use_lat = bool(LATIN_OK.match(ch)) and self.fonts[('lat', weight)].has_glyph(ord(ch))
            key = ('lat', weight) if use_lat else ('cjk', weight)
            if runs and runs[-1][0] == key: runs[-1][1] += ch
            else: runs.append([key, ch])
        return runs

    def width(self, text, size, weight='r', tracking=0):
        w = sum(self.fonts[k].text_length(s, fontsize=size) for k, s in self._runs(text, weight))
        return w + tracking * max(0, len(text) - 1)

    def text(self, x, y, text, size, weight='r', color=INK, align='left', tracking=0):
        """Draw one line; (x, y) is the baseline start (or end/center for align)."""
        if not text: return 0
        w = self.width(text, size, weight, tracking)
        if align == 'right': x -= w
        elif align == 'center': x -= w / 2
        tw = self.writers.setdefault((color,), fz.TextWriter(self.page.rect, color=color))
        cx = x
        for k, s in self._runs(text, weight):
            font = self.fonts[k]
            if tracking:
                for ch in s:
                    tw.append((cx, y), ch, font=font, fontsize=size); cx += font.text_length(ch, fontsize=size) + tracking
            else:
                tw.append((cx, y), s, font=font, fontsize=size); cx += font.text_length(s, fontsize=size)
        return w

    def wrap(self, text, size, weight, maxw):
        """Greedy line breaking for mixed CJK/Latin text."""
        # tokens: latin words stay whole, CJK chars are individual tokens
        tokens = re.findall(r'[A-Za-z0-9+%.\-–/°℃′≥≤]+|\s+|.', text)
        lines = []; cur = ''
        for t in tokens:
            cand = cur + t
            if self.width(cand.rstrip(), size, weight) <= maxw or not cur:
                cur = cand
            else:
                # don't leave an opening punct at the end, or start with closing punct
                if t and t[0] in CLOSE_PUNCT and cur:
                    # move last token of cur to the next line together with t
                    lines.append(cur.rstrip()); cur = t
                else:
                    lines.append(cur.rstrip()); cur = t.lstrip()
        if cur.strip(): lines.append(cur.rstrip())
        # fix lines that start with closing punctuation by pulling the last char of the previous line
        for i in range(1, len(lines)):
            if lines[i] and lines[i][0] in CLOSE_PUNCT and lines[i - 1]:
                lines[i] = lines[i - 1][-1] + lines[i]; lines[i - 1] = lines[i - 1][:-1]
        return lines

    def paragraph(self, x, y, text, size, weight='r', color=BODY, maxw=CW, leading=None, max_lines=None):
        leading = leading or size * 1.55
        lines = self.wrap(text, size, weight, maxw)
        if max_lines: assert len(lines) <= max_lines, (len(lines), lines)
        for i, ln in enumerate(lines):
            self.text(x, y + i * leading, ln, size, weight, color)
        return y + len(lines) * leading

    # ---------------------------------------------------------------- shapes
    def rect(self, r, fill=None, stroke=None, width=0.6, radius=0):
        sh = self.page.new_shape()
        r = fz.Rect(r)
        if radius: sh.draw_rect(r, radius=(radius / r.width, radius / r.height))
        else: sh.draw_rect(r)
        sh.finish(fill=fill, color=stroke, width=width if stroke else 0)
        sh.commit()

    def line(self, x0, y0, x1, y1, color=LINE, width=0.6):
        sh = self.page.new_shape(); sh.draw_line((x0, y0), (x1, y1)); sh.finish(color=color, width=width); sh.commit()

    def circle(self, cx, cy, r, fill=None, stroke=None, width=0.6):
        sh = self.page.new_shape(); sh.draw_circle((cx, cy), r); sh.finish(fill=fill, color=stroke, width=width if stroke else 0); sh.commit()

    # ---------------------------------------------------------------- images
    def _prep(self, path, ar, fx, fy, region, px_w):
        key = hashlib.md5(f'{path}|{ar:.4f}|{fx}|{fy}|{region}|{px_w}'.encode()).hexdigest()[:12]
        out = os.path.join(self.imgcache, key + '.jpg')
        if os.path.exists(out): return out
        im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
        if region:
            w, h = im.size; im = im.crop((int(region[0] * w), int(region[1] * h), int(region[2] * w), int(region[3] * h)))
        w, h = im.size
        if w / h > ar: cw, ch = int(h * ar), h
        else: cw, ch = w, int(w / ar)
        x0 = int(min(max(0, fx * w - cw / 2), w - cw)); y0 = int(min(max(0, fy * h - ch / 2), h - ch))
        im = im.crop((x0, y0, x0 + cw, y0 + ch))
        if im.width > px_w: im = im.resize((px_w, int(px_w / ar)), Image.LANCZOS)
        im.save(out, quality=86, optimize=True, subsampling=1)
        return out

    def image(self, r, path, fx=0.5, fy=0.5, region=None, stroke=LINE, scale=3):
        """Cover-crop `path` into rect r (focus point fx, fy in 0..1; region = fractional sharp area)."""
        r = fz.Rect(r)
        f = self._prep(path, r.width / r.height, fx, fy, region, int(r.width * scale))
        self.page.insert_image(r, filename=f, keep_proportion=True)
        if stroke: self.rect(r, stroke=stroke, width=0.6)

    def image_fit(self, r, path, align='left'):
        """Contain-fit (logos, transparent PNG)."""
        r = fz.Rect(r); im = Image.open(path); ar = im.width / im.height
        if r.width / r.height > ar: w, h = r.height * ar, r.height
        else: w, h = r.width, r.width / ar
        x = r.x0 if align == 'left' else (r.x1 - w if align == 'right' else r.x0 + (r.width - w) / 2)
        y = r.y0 + (r.height - h) / 2
        self.page.insert_image(fz.Rect(x, y, x + w, y + h), filename=path, keep_proportion=True)
