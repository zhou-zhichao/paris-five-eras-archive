"""Deterministic native-frame renderer, usable locally or in an L4 Slurm task."""
from pathlib import Path
import argparse
import json
import sys
import time
import hashlib
import os
import bpy

p=argparse.ArgumentParser()
p.add_argument('--root',required=True)
p.add_argument('--worker',type=int,default=0)
p.add_argument('--workers',type=int,default=1)
p.add_argument('--frames',type=int,nargs='*')
p.add_argument('--width',type=int,default=1920)
p.add_argument('--samples',type=int,default=64)
p.add_argument('--engine',default='BLENDER_EEVEE_NEXT')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if not os.environ.get('SLURM_JOB_ID') and (not a.frames or len(a.frames)>8):
    raise RuntimeError('Local rendering is limited to explicit inspection frames. Run the full film on Minerva through Slurm.')
root=Path(a.root);s=bpy.context.scene
checksum=root/'input.sha256'
if checksum.exists():
    expected=checksum.read_text().split()[0].lower()
    actual=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
    if actual!=expected:raise RuntimeError(f'Scene checksum mismatch: {actual} != {expected}')
s.render.engine=a.engine
s.render.resolution_x=a.width;s.render.resolution_y=round(a.width*9/16);s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=15
s.render.use_persistent_data=True
if a.engine=='CYCLES':
    cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='OPTIX';cp.get_devices()
    for d in cp.devices:d.use=d.type=='OPTIX'
    s.cycles.device='GPU';s.cycles.samples=a.samples;s.cycles.use_denoising=True
else:s.eevee.taa_render_samples=a.samples
frames=a.frames or range(a.worker+1,5401,a.workers)
(root/'frames').mkdir(exist_ok=True,parents=True)
(root/'logs').mkdir(exist_ok=True,parents=True)
results=[]
for f in frames:
    path=root/f'frames/frame_{f:05d}.png'
    if path.exists() and path.stat().st_size>10000:
        with path.open('rb') as existing:
            existing.seek(-12,2)
            complete=existing.read()==b'\x00\x00\x00\x00IEND\xaeB`\x82'
        if complete:continue
    started=time.monotonic();s.frame_set(f);s.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    record={'frame':f,'seconds':round(time.monotonic()-started,3),'bytes':path.stat().st_size}
    results.append(record)
    with (root/f'logs/worker-{a.worker}.jsonl').open('a') as handle:handle.write(json.dumps(record)+'\n')
    print('FRAME_COMPLETE',json.dumps(record),flush=True)
print('WORKER_COMPLETE',a.worker,len(results),flush=True)
