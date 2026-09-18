"""Repack locally installed campaign components without changing their contents.

Build CascLib and StormLib first; see docs/CAMPAIGN.md. Extracted game assets are
local-only and ignored by Git. No campaign trigger content is sent to Jev.
"""
import argparse
import ctypes as c
from pathlib import Path
import tempfile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--casc',required=True)
parser.add_argument('--storm',required=True)
parser.add_argument('--mission',default='traynor01')
parser.add_argument('--storage',default='/Applications/StarCraft II')
args=parser.parse_args()
if not args.mission.isalnum(): raise ValueError('Mission must be an alphanumeric internal map name')
C=c.CDLL(args.casc)
S=c.CDLL(args.storm)
P=c.c_void_p; U=c.c_uint32; B=c.c_char_p

def fn(lib,name,args,ret=c.c_bool):
 f=getattr(lib,name);f.argtypes=args;f.restype=ret;return f
open_store=fn(C,'CascOpenStorage',[B,U,c.POINTER(P)])
open_file=fn(C,'CascOpenFile',[P,B,U,U,c.POINTER(P)])
read=fn(C,'CascReadFile',[P,P,U,c.POINTER(U)])
close_file=fn(C,'CascCloseFile',[P]);close_store=fn(C,'CascCloseStorage',[P])
find_first=fn(C,'CascFindFirstFile',[P,B,P,B],P)
find_next=fn(C,'CascFindNextFile',[P,P]);find_close=fn(C,'CascFindClose',[P])
create=fn(S,'SFileCreateArchive',[B,U,U,c.POINTER(P)])
add=fn(S,'SFileAddFileEx',[P,B,B,U,U,U]);close_mpq=fn(S,'SFileCloseArchive',[P])
store=P();assert open_store(args.storage.encode(),0,c.byref(store))
prefix=b'campaigns\\liberty.sc2campaign\\base.sc2maps\\maps\\campaign\\' + args.mission.encode() + b'.sc2map\\'
finddata=c.create_string_buffer(65536);h=find_first(store,prefix+b'*',finddata,None)
assert h and h!=P(-1).value
names=[]
while True:
 names.append(finddata.value)
 if not find_next(h,finddata):break
find_close(h)
out=Path(__file__).resolve().parent.parent/'maps'/f'{args.mission}.SC2Map'
assert not out.exists(), 'Refuse to overwrite map'
archive=P();assert create(str(out).encode(),0x00100000,1024,c.byref(archive))
count=0
with tempfile.TemporaryDirectory(prefix='jev-map-') as tmp:
 for name in names:
  relative=name[len(prefix):]
  first=relative.split(b'\\')[0]
  if first.endswith(b'.sc2data') and first not in {b'base.sc2data',b'enus.sc2data'}: continue
  f=P();assert open_file(store,name,0,0,c.byref(f)),name
  payload=bytearray();buf=c.create_string_buffer(65536);n=U()
  while True:
   assert read(f,buf,len(buf),c.byref(n)),name
   if not n.value:break
   payload.extend(buf.raw[:n.value])
  close_file(f)
  local=Path(tmp)/str(count);local.write_bytes(payload)
  assert add(archive,str(local).encode(),relative,0x200,2,2),relative
  count+=1
assert close_mpq(archive)
close_store(store)
print({'map':str(out),'components':count,'bytes':out.stat().st_size})
