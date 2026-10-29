"""FLYPHARM · Genera web/index.html (solo ASCII) a partir de web/index.src.html (UTF-8).
Texto HTML -> entidades numéricas; dentro de <script> -> escapes \\uXXXX.
Así los acentos sobreviven aunque el servidor no declare la codificación."""
import re
from pathlib import Path
src = Path('web/index.src.html').read_text(encoding='utf-8')
def html_esc(s): return ''.join(c if ord(c)<128 else f'&#x{ord(c):X};' for c in s)
def js_esc(s):   return ''.join(c if ord(c)<128 else (f'\\u{ord(c):04X}' if ord(c)<0x10000 else ''.join(f'\\u{x:04X}' for x in (0xD800+((ord(c)-0x10000)>>10), 0xDC00+((ord(c)-0x10000)&0x3FF)))) for c in s)
out, pos = [], 0
for m in re.finditer(r'<script\b[^>]*>.*?</script>', src, flags=re.S):
    out.append(html_esc(src[pos:m.start()]))
    blk = m.group(0); tag_end = blk.index('>')+1
    out.append(blk[:tag_end] + js_esc(blk[tag_end:-9]) + '</script>')
    pos = m.end()
out.append(html_esc(src[pos:]))
res = ''.join(out); assert all(ord(c)<128 for c in res)
Path('web/index.html').write_text(res, encoding='ascii')
print(f"web/index.html generado: {len(res):,} bytes, 100% ASCII")
