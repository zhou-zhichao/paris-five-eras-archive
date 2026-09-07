"""Resume assigned frames, validating PNG CRCs and publishing new frames atomically."""
import argparse
from pathlib import Path
import runpy
import struct
import sys
import zlib
import bpy

root=Path(__file__).resolve().parent
runpy.run_path(str(root/'configure_v50.py'))
parser=argparse.ArgumentParser();parser.add_argument('--worker',type=int,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
def valid_png(path):
    try:
        with path.open('rb') as stream:
            if stream.read(8)!=b'\x89PNG\r\n\x1a\n':return False
            while True:
                header=stream.read(8)
                if len(header)!=8:return False
                size,kind=struct.unpack('>I4s',header)
                if size>100_000_000:return False
                data=stream.read(size);crc=stream.read(4)
                if len(data)!=size or len(crc)!=4:return False
                if zlib.crc32(kind+data)!=struct.unpack('>I',crc)[0]:return False
                if kind==b'IEND':return True
    except OSError:return False
scene=bpy.context.scene
for frame in range(args.worker+1,3601,16):
    output=root/'frames'/f'frame_{frame:04d}.png'
    if valid_png(output):continue
    pending=output.with_name(f'.frame_{frame:04d}.pending.png')
    scene.frame_set(frame)
    scene.render.filepath=str(pending)
    bpy.ops.render.render(write_still=True)
    if not valid_png(pending):raise RuntimeError(f'Invalid generated frame {frame}')
    pending.replace(output)
    print('FRAME_COMPLETE',frame,flush=True)
print('WORKER_COMPLETE',args.worker,flush=True)
