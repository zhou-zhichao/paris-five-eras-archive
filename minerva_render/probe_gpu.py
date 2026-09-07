import bpy
import os
import subprocess
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=64
scene.render.resolution_y=64
scene.render.resolution_percentage=100
scene.eevee.taa_render_samples=1
bpy.ops.render.render()
print('PROBE_PID',os.getpid(),flush=True)
print(subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader'],text=True),flush=True)
