"""Reduce oversized late-era trees without changing early geometry or clearance."""
import json
from pathlib import Path
import bpy
import numpy as np
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
scene = bpy.context.scene
targets = set()
for frame in (2800, 3550):
    scene.frame_set(frame)
    targets.update(o.name for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Forest_') and not o.hide_render)

def evaluated_coordinates(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    coords = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', coords)
    evaluated.to_mesh_clear()
    return coords

before = {}
for frame in (750, 1450, 2100, 2174):
    scene.frame_set(frame)
    before[frame] = {name: evaluated_coordinates(bpy.data.objects[name]) for name in targets}

report = {'objects': [], 'early_max_coordinate_difference': {}, 'scale': [0.32, 0.32, 0.30]}
for name in sorted(targets):
    obj = bpy.data.objects[name]
    mesh = obj.data
    if not mesh.shape_keys:
        obj.shape_key_add(name='Basis')
    basis = mesh.shape_keys.key_blocks[0]
    shrink = mesh.shape_keys.key_blocks.get('Tree_Shrink')
    key = obj.shape_key_add(name='Late_Tree_Proportion')
    if shrink:
        centers = [p.co.copy() for p in shrink.data]
    else:
        # Each procedural tree has separate trunk and crown components.
        parent = list(range(len(mesh.vertices)))
        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for edge in mesh.edges:
            a, b = map(find, edge.vertices)
            parent[a] = b
        groups = {}
        for i in range(len(parent)):
            groups.setdefault(find(i), []).append(i)
        trunks = set()
        for polygon in mesh.polygons:
            material = mesh.materials[polygon.material_index]
            if material and 'Trunk' in material.name:
                trunks.add(find(polygon.vertices[0]))
        if not trunks:
            raise RuntimeError(f'No trunk anchors in {name}')
        anchors = []
        for root in sorted(trunks):
            coords = [basis.data[i].co for i in groups[root]]
            anchors.append((sum(p.x for p in coords)/len(coords), sum(p.y for p in coords)/len(coords), min(p.z for p in coords)))
        tree = KDTree(len(anchors))
        for i, (x,y,z) in enumerate(anchors):
            tree.insert((x,y,0),i)
        tree.balance()
        centers = [None] * len(parent)
        orphan_components = []
        for indices in groups.values():
            x = sum(basis.data[i].co.x for i in indices)/len(indices)
            y = sum(basis.data[i].co.y for i in indices)/len(indices)
            _, nearest, distance = tree.find((x,y,0))
            anchor = anchors[nearest]
            if distance > 0.05:
                # Prior clearance edits can leave crown-only components.
                # Keep them centered in place instead of attaching to another tree.
                anchor = (x, y, 0.022)
                orphan_components.append({'vertices':len(indices),'center':[x,y],'nearest_trunk_distance':distance})
            for i in indices:
                centers[i] = anchor
        report.setdefault('crown_only_components', {})[name] = orphan_components
    for i, center in enumerate(centers):
        p = basis.data[i].co
        key.data[i].co = (center[0]+(p.x-center[0])*.32, center[1]+(p.y-center[1])*.32, center[2]+(p.z-center[2])*.30)
    obj['late_tree_blend'] = 0.0
    obj.keyframe_insert(data_path='["late_tree_blend"]',frame=1)
    obj.keyframe_insert(data_path='["late_tree_blend"]',frame=2174)
    obj['late_tree_blend'] = 1.0
    obj.keyframe_insert(data_path='["late_tree_blend"]',frame=2500)
    fc = key.driver_add('value')
    driver = fc.driver
    mix = driver.variables.new(); mix.name = 'mix'; mix.type = 'SINGLE_PROP'
    mix.targets[0].id = obj; mix.targets[0].data_path = '["late_tree_blend"]'
    if shrink:
        clearance = driver.variables.new(); clearance.name = 'clearance'; clearance.type = 'SINGLE_PROP'
        clearance.targets[0].id_type = 'KEY'; clearance.targets[0].id = mesh.shape_keys
        clearance.targets[0].data_path = 'key_blocks["Tree_Shrink"].value'
        driver.expression = 'mix * (1 - clearance)'
    else:
        driver.expression = 'mix'
    report['objects'].append({'name': name, 'vertices': len(mesh.vertices), 'has_clearance': bool(shrink)})

for frame, coordinates in before.items():
    scene.frame_set(frame)
    differences = [float(np.max(np.abs(evaluated_coordinates(bpy.data.objects[name])-coords))) for name, coords in coordinates.items()]
    report['early_max_coordinate_difference'][frame] = max(differences, default=0)
    assert max(differences,default=0) < 1e-6, (frame, max(differences))
scene.frame_set(2800)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/paris_v49_late_vegetation.blend'))
(ROOT/'reports/vegetation-v49.json').write_text(json.dumps(report,indent=2))
print('VEGETATION_COMPLETE', json.dumps(report), flush=True)
