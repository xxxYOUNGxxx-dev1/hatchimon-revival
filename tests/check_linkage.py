"""Check strong undefined symbols/NEEDED names against the bundled ARM guest runtime."""
from pathlib import Path
import sys,io,zipfile,json
ROOT=Path(__file__).resolve().parents[1]

from elftools.elf.elffile import ELFFile
files=list((ROOT/'.work/runtime-decoded/assets/zb').rglob('*.so'))
files+=list((ROOT/'.work/guest-decoded/lib/armeabi').glob('*.so'))
exports=set();records=[]
for path in files:
    elf=ELFFile(io.BytesIO(path.read_bytes()))
    if elf.elfclass!=32:continue
    symbols=list(elf.get_section_by_name('.dynsym').iter_symbols())
    exports.update(s.name for s in symbols if s['st_shndx']!='SHN_UNDEF')
    dynamic=elf.get_section_by_name('.dynamic')
    needed=[t.needed for t in dynamic.iter_tags() if t.entry.d_tag=='DT_NEEDED'] if dynamic else []
    records.append((path,symbols,needed))
names={p.name for p,s,n in records}
errors=[]
for path,symbols,needed in records:
    if path.name not in ['libMyGame.so','libHatchimonDev.so','libOpenSLES.so','libGLESv1_CM.so']:continue
    missing=[s.name for s in symbols if s['st_shndx']=='SHN_UNDEF' and s.name and s['st_info']['bind']!='STB_WEAK' and s.name not in exports]
    absent=[n for n in needed if Path(n).name not in names]
    if missing or absent:errors.append({'library':path.name,'undefined':missing,'needed':absent})
result={'guest_linkage_errors':errors,'checked_game_dependencies':10,'scope':'static exported-symbol/DT_NEEDED coverage; not a real loader or renderer test'}
(ROOT/'output/linkage-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2));assert not errors
