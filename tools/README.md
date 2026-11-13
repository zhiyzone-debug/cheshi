# 作品集生成说明

- `deck.py` + `deck_engine.py`：从素材重新生成整本作品集（统一字体、网格、图片裁切）。
  运行：`python3 deck.py 输出.pdf 字体目录 assets/原图 assets/logo 轻食照片目录 缓存目录`
  字体目录需包含：NotoSansSC-{Regular,Medium,Bold}.ttf（由 Noto Sans SC 可变字体静态化）、
  Inter-{Regular,Medium,SemiBold,Bold}.ttf（由 InterVariable.ttf 静态化）、DejaVuSans.ttf。
  所有字体以 CID TrueType 形式嵌入，iOS / 微信 / 电脑均可正常显示。
- `edit_p9.py`、`build.py`：旧版（PPT 导出版式）的局部修改脚本，仅作留档。
