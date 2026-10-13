"""Execute original ARM instructions for IDs, merge targets and sprite selection.

This verifies the actual game's routines, but does not run its renderer or Android.
"""
from pathlib import Path
import sys,struct,io,zipfile,json
ROOT=Path(__file__).resolve().parents[1]

from elftools.elf.elffile import ELFFile
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_FP,UC_ARM_REG_PC
with zipfile.ZipFile(str(ROOT/'inputs/base.apk')) as apk:
    elf=ELFFile(io.BytesIO(apk.read('lib/armeabi/libMyGame.so')))
    assets=set(apk.namelist())
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
u.mem_map(0,0x1000000);u.mem_map(0x2000000,0x20000)
for segment in elf.iter_segments():
    if segment['p_type']=='PT_LOAD':u.mem_write(segment['p_vaddr'],segment.data())
syms={s.name:s for s in elf.get_section_by_name('.dynsym').iter_symbols()}
DB=0x2001000;LINK=0x2002000;STACK=0x201f000;STOP=0x200f000
def put(addr,n):u.mem_write(addr,struct.pack('<I',n))
def get(addr):return struct.unpack('<I',u.mem_read(addr,4))[0]
def hook(uc,addr,size,user):
    if addr==0x86b4ac: # getMonster's allocation PLT slot; allocator only is mocked.
        assert uc.reg_read(UC_ARM_REG_R0)==16
        uc.reg_write(UC_ARM_REG_R0,DB)
        uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
def call(name,a,b=0):
    u.reg_write(UC_ARM_REG_SP,STACK);u.reg_write(UC_ARM_REG_LR,STOP)
    u.reg_write(UC_ARM_REG_R0,a);u.reg_write(UC_ARM_REG_R1,b)
    u.emu_start(syms[name]['st_value'],STOP,count=2000)
    return u.reg_read(UC_ARM_REG_R0)
cases=0
for tier in range(24):
    for form in range(3):
        for kind in range(4):
            id_=tier*12+kind*3+form
            assert call('_ZN14MonsterDBClass10getMonsterEi',id_)==DB
            assert [get(DB+offset) for offset in [0,4,8,12]]==[id_,kind,tier,form]
            wanted=(tier+1)*12+kind*3 if form==2 else id_+1
            assert call('_ZN12MonsterClass12getComposeIDEP10_MonsterDB',0,DB)==wanted
            # Execute the actual makeMonster tier-to-sprite normalization block.
            fp=STACK-0x800;put(LINK,DB);put(fp-0x34c,LINK);put(fp-0x354,tier)
            u.reg_write(UC_ARM_REG_FP,fp)
            u.emu_start(0x50ad94,0x50adb4,count=30)
            spriteTier=get(fp-0x354)
            assert spriteTier==(tier if tier<=11 else tier-12)
            assert f'assets/monster/m_{spriteTier}_{kind}_{form}.png' in assets
            # Check the reload path uses the same sprites after saving/restarting.
            put(fp-0x374,LINK);put(fp-0x37c,tier)
            u.reg_write(UC_ARM_REG_FP,fp)
            u.emu_start(0x502d1c,0x502d3c,count=30)
            assert get(fp-0x37c)==spriteTier
            cases+=1
assert 'assets/monster/m_12_0_0.png' not in assets
result={'original_instruction_cases':cases,'coverage':'all 288 original tier/form/type IDs, merge target routine and makeMonster sprite normalization',
        'maximum_defined_level':72,'glow_starts_at_level':37,'android_renderer_test':'not run'}
(ROOT/'output/original-level-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS:',json.dumps(result))
