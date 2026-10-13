"""Execute the built ARM bridge with mocked game exports; no Android runtime required."""
from pathlib import Path
import sys, struct
ROOT = Path(__file__).resolve().parents[1]

from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC

BASE=0x100000; MOCK=0x200000; HEAP=0x300000; STACK=0x400000; STOP=0x2ff000
class Machine:
    def __init__(self):
        self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        for addr,size in [(BASE,0x40000),(MOCK,0x100000),(HEAP,0x20000),(STACK,0x10000)]: self.u.mem_map(addr,size)
        self.functions={}; self.callbacks={}; self.next=MOCK
        self.farm=HEAP; self.ui=HEAP+0x1000; self.monster=HEAP+0x2000; self.data=HEAP+0x3000
        self.vtable=HEAP+0x4000; self.global_=HEAP+0x5000; self.count=2; self.eggs=0
        self.active=True; self.flush=[]; self.refresh=[]; self.spawned=[]; self.saved=0
        self.put(self.farm,self.vtable+8); self.put(self.farm+0x234,self.monster); self.put(self.farm+0x238,self.ui)
        self.put(self.global_,self.data)
        for i in range(3): self.put(self.data+0x28+i*4,100)
        self.functions['g_GData']=self.global_; self.functions['_ZTV9FarmScene']=self.vtable
        self.add('dlopen',lambda r: 123)
        self.add('dlsym',lambda r: self.functions.get(self.cstring(r[1]),0))
        self.add('_ZN7cocos2d8Director11getInstanceEv',lambda r: HEAP+0x6000)
        self.add('_ZN7cocos2d8Director15getRunningSceneEv',lambda r: HEAP+0x6100)
        self.add('_ZN7cocos2d4Node11getChildrenEv',lambda r: HEAP+0x6200)
        self.add('_ZNK7cocos2d6VectorIPNS_4NodeEE4sizeEv',lambda r: int(self.active))
        self.add('_ZNK7cocos2d6VectorIPNS_4NodeEE2atEi',lambda r: self.farm)
        for i,name in enumerate(['Gold','Cash','Ruby']):
            self.add('_ZN10GDataClass7get'+name+'Eib',lambda r,i=i: self.money(r,i))
            self.add('_ZN11FarmUiClass7set'+name+'Ev',lambda r,i=i: self.update(r,i))
        self.add('_ZN12MonsterClass15getMonsterCountEv',lambda r:self.count)
        self.add('_ZN12MonsterClass16getHatchEggCountEv',lambda r:self.eggs)
        self.add('_ZN12MonsterClass11makeMonsterEiii',self.spawn)
        self.add('_ZN12MonsterClass11saveMonsterEv',self.save)
        with open(ROOT/'.work/guest-decoded/lib/armeabi/libHatchimonDev.so','rb') as f:
            e=ELFFile(f)
            for segment in e.iter_segments():
                if segment['p_type']=='PT_LOAD': self.u.mem_write(BASE+segment['p_vaddr'],segment.data())
            for name in ['.rel.dyn','.rel.plt']:
                section=e.get_section_by_name(name)
                if not section: continue
                symbols=e.get_section(section['sh_link'])
                for rel in section.iter_relocations():
                    addr=BASE+rel['r_offset']; kind=rel['r_info_type']
                    if kind==23: self.put(addr,self.get(addr)+BASE)
                    elif kind in [21,22]: self.put(addr,self.functions[symbols.get_symbol(rel['r_info_sym']).name])
                    else: raise AssertionError('Unsupported relocation '+str(kind))
            self.entry=BASE+next(s['st_value'] for s in e.get_section_by_name('.dynsym').iter_symbols() if s.name=='Java_org_cocos2dx_cpp_DevMenu_nativeApply')
        self.u.hook_add(UC_HOOK_CODE,self.hook)
    def put(self,a,n): self.u.mem_write(a,struct.pack('<I',n&0xffffffff))
    def get(self,a): return struct.unpack('<I',self.u.mem_read(a,4))[0]
    def cstring(self,a):
        b=bytearray()
        while self.u.mem_read(a,1)!=b'\0': b.extend(self.u.mem_read(a,1)); a+=1
        return b.decode()
    def add(self,name,callback):
        addr=self.next;self.next+=4;self.functions[name]=addr;self.callbacks[addr]=callback
    def hook(self,u,addr,size,user):
        if addr==STOP: u.emu_stop(); return
        if addr in self.callbacks:
            r=[u.reg_read(reg) for reg in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]
            result=self.callbacks[addr](r)
            u.reg_write(UC_ARM_REG_R0,(result or 0)&0xffffffff); u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
    def money(self,r,i):
        assert r[0]==self.data and r[2]==1
        self.put(self.data+0x28+i*4,self.get(self.data+0x28+i*4)+r[1]);self.flush.append(i)
    def update(self,r,i):
        assert r[0]==self.ui
        assert self.get(self.ui+0x14c+i*4)==self.get(self.data+0x28+i*4)
        self.refresh.append(i)
    def spawn(self,r):
        assert r[0]==self.monster
        self.spawned.append(tuple(r[1:]));self.count+=1
    def save(self,r): assert r[0]==self.monster;self.saved+=1
    def call(self,cmd,a,b,c,d):
        sp=STACK+0xff00
        for reg,value in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],[0,0,cmd,a]): self.u.reg_write(reg,value&0xffffffff)
        for i,n in enumerate([b,c,d]): self.put(sp+i*4,n)
        self.u.reg_write(UC_ARM_REG_SP,sp);self.u.reg_write(UC_ARM_REG_LR,STOP)
        self.u.emu_start(self.entry,STOP+4,count=20000)
        value=self.u.reg_read(UC_ARM_REG_R0)
        return value if value<0x80000000 else value-0x100000000

cases=0
for currency in range(3):
    m=Machine();assert m.call(1,currency,10000,0,0)==0
    assert m.get(m.data+0x28+currency*4)==10100 and m.flush==[currency] and m.refresh==[currency];cases+=1
m=Machine();m.put(m.data+0x28,1999999999);assert m.call(1,0,100000000,0,0)==0;assert m.get(m.data+0x28)==2000000000;cases+=1
m=Machine();m.put(m.data+0x28,2000000000);assert m.call(1,0,1,0,0)==0;assert m.flush==[];cases+=1
for tier in range(24):
    for form in range(3):
        for kind in range(-1,4):
            m=Machine();assert m.call(2,tier,form,kind,1)==1
            assert m.spawned==[(tier,form,kind&0xffffffff)] and m.saved==1;cases+=1
m=Machine();assert m.call(2,11,2,3,10)==10;assert len(m.spawned)==10;cases+=1
m=Machine();m.count=118;m.eggs=1;assert m.call(2,0,0,-1,10)==1;cases+=1
m=Machine();m.count=120;assert m.call(2,0,0,0,1)==-3;assert m.spawned==[];cases+=1
m=Machine();m.active=False;assert m.call(1,0,10000,0,0)==-2;assert m.flush==[];cases+=1
for args in [(1,3,1,0,0),(1,0,0,0,0),(1,0,1000000001,0,0),(2,24,0,0,1),(2,0,3,0,1),(2,0,0,4,1),(2,0,0,0,11),(3,0,0,0,0)]:
    m=Machine();assert m.call(*args)==-4;assert not m.flush and not m.spawned;cases+=1
for currency in range(3):
    m=Machine();assert m.call(1,currency,1000000000,0,0)==0
    assert m.get(m.data+0x28+currency*4)==1000000100;cases+=1
    m=Machine();m.put(m.data+0x28+currency*4,1500000000)
    assert m.call(1,currency,1000000000,0,0)==0
    assert m.get(m.data+0x28+currency*4)==2000000000;cases+=1
for level in range(1,73):
    tier,form=divmod(level-1,3)
    m=Machine();assert m.call(2,tier,form,0,1)==1
    assert m.spawned==[(tier,form,0)];cases+=1
print(f'PASS: {cases} ARM bridge cases, including 360 tier/form/type combinations, levels 1..72, billion grants, persistence calls, UI caches, capacity and overflow.')
