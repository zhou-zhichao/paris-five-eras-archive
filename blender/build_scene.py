import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


FPS = 30
TOTAL_FRAMES = 3600
# The opening lands on the Ile de la Cite in four seconds. Roads lead each
# urban wave; buildings then keep changing until the next era starts.
PHASE_FRAMES = [150, 825, 1500, 2175, 2850]
ROAD_LEAD_FRAMES = [30, 45, 45, 45, 60]
PHASE_REVEAL_FRAMES = [660, 660, 660, 660, 735]
ROAD_REVEAL_FRAMES = [420, 480, 510, 510, 540]
BUILDING_CHUNKS = [1400, 2200, 3000, 3800, 4600]
BUILDING_GROW_FRAMES = [6, 6, 7, 7, 8]
# Each era arrives in visible neighborhood waves across the full era window.
# A wave lasts less than a second, then the next wave begins roughly 1.5
# seconds later. Individual chunks still start on different frames, so
# buildings shoot up instead of fading in as one large slab.
BUILDING_BATCH_STRIDE_FRAMES = 45
BUILDING_BATCH_SPREAD_FRAMES = 24
ROAD_GROW_FRAMES = [18, 20, 22, 24, 26]
FOREST_TREE_COUNT = 15500

# Multiple delayed origins prevent a single circular reveal front. Later-era
# origins sit on the former urban edge or at infrastructure hubs so new fabric
# visibly joins the already-built city.
ERA_GROWTH_CENTERS = [
    [
        (0.0, 0.0, 0.00, 0.86),
        (-4.5, 2.5, 0.12, 0.92),
        (3.6, -4.4, 0.20, 0.88),
    ],
    [
        (0.2, 0.2, 0.00, 0.82),
        (-8.5, 4.8, 0.10, 0.92),
        (7.8, -3.5, 0.18, 0.88),
        (-3.0, -9.2, 0.25, 0.84),
    ],
    [
        (-10.8, 11.85, 0.00, 0.78),
        (-14.0, -4.0, 0.09, 0.88),
        (9.0, -7.0, 0.16, 0.86),
        (15.0, 8.0, 0.24, 0.82),
    ],
    [
        (-40.2, 23.2, 0.00, 0.72),
        (-17.0, 7.0, 0.07, 0.82),
        (11.0, -5.0, 0.14, 0.82),
        (27.0, 13.0, 0.22, 0.78),
        (-9.0, -22.0, 0.28, 0.76),
    ],
    [
        (-45.0, 28.5, 0.00, 0.66),
        (-40.6, 6.0, 0.05, 0.72),
        (-18.0, 18.0, 0.09, 0.72),
        (6.5, 24.0, 0.13, 0.70),
        (14.0, -11.0, 0.16, 0.70),
        (-10.0, -16.0, 0.20, 0.68),
        (35.0, 8.0, 0.27, 0.64),
    ],
]
ERA_GROWTH_RADII = [15.0, 24.0, 36.0, 50.0, 70.0]

MODERN_STATIONS = [
    {
        "name": "Gare_du_Nord",
        "location": (6.5, 24.0),
        "rotation": math.radians(5.0),
        "size": (3.4, 1.65),
        "track": [(6.5, 24.0), (7.4, 31.0), (10.5, 42.0)],
    },
    {
        "name": "Gare_Saint_Lazare",
        "location": (-18.0, 18.0),
        "rotation": math.radians(-28.0),
        "size": (3.1, 1.55),
        "track": [(-18.0, 18.0), (-26.0, 26.0), (-39.0, 35.0)],
    },
    {
        "name": "Gare_de_Lyon",
        "location": (14.0, -4.0),
        "rotation": math.radians(45.0),
        "size": (3.3, 1.6),
        "track": [(14.0, -4.0), (23.0, -13.0), (39.0, -29.0)],
    },
    {
        "name": "Gare_Montparnasse",
        "location": (-10.0, -16.0),
        "rotation": math.radians(24.0),
        "size": (3.2, 1.55),
        "track": [(-10.0, -16.0), (-18.0, -27.0), (-27.0, -42.0)],
    },
]
PROJECT_DIR = Path(__file__).resolve().parents[1]
STILLS_DIR = PROJECT_DIR / "stills"
PREVIEWS_DIR = PROJECT_DIR / "previews"
RENDERS_DIR = PROJECT_DIR / "renders"
ASSETS_DIR = PROJECT_DIR / "assets"
GEODATA_PATH = PROJECT_DIR / "data" / "paris_geodata.json"
BLEND_PATH = PROJECT_DIR / "blender" / "paris_5_eras.blend"
NOTRE_DAME_GLB_PATH = ASSETS_DIR / "models" / "notre-dame-clean-200k.glb"


# Deliberately irregular historical envelopes. They are not survey-grade
# reconstructions, but they avoid the concentric-ellipse look of the first pass.
CITY_POLYGONS = [
    [
        (-9.0, -4.0),
        (-7.0, -10.0),
        (1.0, -11.0),
        (9.0, -6.0),
        (9.0, 3.0),
        (4.0, 8.0),
        (-4.0, 8.0),
        (-9.0, 4.0),
    ],
    [
        (-18.0, -4.0),
        (-13.0, -11.5),
        (-3.0, -15.0),
        (9.0, -13.0),
        (16.5, -6.0),
        (17.0, 3.5),
        (11.0, 11.5),
        (2.0, 14.0),
        (-10.0, 11.0),
        (-17.0, 5.0),
    ],
    [
        (-29.0, -3.0),
        (-24.0, -14.0),
        (-16.0, -21.0),
        (-3.0, -24.0),
        (11.0, -22.0),
        (23.0, -14.0),
        (29.0, -3.0),
        (25.0, 12.0),
        (15.0, 20.0),
        (1.0, 22.0),
        (-13.0, 19.0),
        (-25.0, 11.0),
    ],
    [
        (-43.0, -3.0),
        (-38.0, -17.0),
        (-27.0, -27.0),
        (-10.0, -32.0),
        (10.0, -31.0),
        (28.0, -25.0),
        (40.0, -13.0),
        (43.0, 3.0),
        (36.0, 18.0),
        (22.0, 28.0),
        (3.0, 32.0),
        (-17.0, 29.0),
        (-34.0, 19.0),
    ],
    [
        (-61.0, -3.0),
        (-54.0, -21.0),
        (-42.0, -35.0),
        (-23.0, -44.0),
        (-1.0, -47.0),
        (21.0, -43.0),
        (40.0, -34.0),
        (53.0, -20.0),
        (59.0, -2.0),
        (52.0, 18.0),
        (36.0, 35.0),
        (12.0, 43.0),
        (-13.0, 42.0),
        (-36.0, 33.0),
        (-53.0, 17.0),
    ],
]
ROAD_SPEC_CACHE = {}
GEODATA_CACHE = None
REAL_ROAD_SEGMENTS = None
REAL_ROAD_GRID = None
ROAD_GRID_SIZE = 3.0
BUILDING_FOOTPRINTS = []
BUILDING_FOOTPRINT_GRID = {}
BUILDING_FOOTPRINT_CELL = 0.8
ALL_ERA_FOOTPRINTS = []
RIVER_POINTS_CACHE = None
BUILDING_WINDOW_DARK_ID = 9
BUILDING_WINDOW_WARM_ID = 10
BUILDING_DOOR_ID = 11
BUILDING_TRIM_ID = 12


def load_geodata():
    global GEODATA_CACHE
    if GEODATA_CACHE is None:
        GEODATA_CACHE = json.loads(GEODATA_PATH.read_text(encoding="utf-8"))
    return GEODATA_CACHE


def parse_args():
    args = sys.argv
    args = args[args.index("--") + 1 :] if "--" in args else []
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["setup", "stills", "opening", "preview", "render"],
        default="setup",
    )
    return parser.parse_args(args)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def make_material(name, color, metallic=0.0, roughness=0.72, ior_level=0.5, coat_weight=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"),
        None,
    )
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        output = next((node for node in nodes if node.type == "OUTPUT_MATERIAL"), None)
        if output is None:
            output = nodes.new("ShaderNodeOutputMaterial")
        mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "IOR Level" in bsdf.inputs:
        bsdf.inputs["IOR Level"].default_value = ior_level
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat_weight
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = max(0.08, roughness * 0.45)
    return mat


def make_water_material():
    mat = bpy.data.materials.new(name="Water_Material")
    mat.diffuse_color = (0.11, 0.34, 0.34, 1.0)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (720, 80)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (430, 80)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.333
    if "IOR Level" in bsdf.inputs:
        bsdf.inputs["IOR Level"].default_value = 0.48
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.2
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = 0.24
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.03

    coordinates = nodes.new("ShaderNodeTexCoord")
    coordinates.location = (-900, 40)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-700, 40)
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)

    broad_noise = nodes.new("ShaderNodeTexNoise")
    broad_noise.location = (-470, 160)
    broad_noise.noise_dimensions = "3D"
    broad_noise.inputs["Scale"].default_value = 0.45
    broad_noise.inputs["Detail"].default_value = 2.0
    broad_noise.inputs["Roughness"].default_value = 0.38
    broad_noise.inputs["Distortion"].default_value = 0.0

    ripple_noise = nodes.new("ShaderNodeTexNoise")
    ripple_noise.location = (-470, -220)
    ripple_noise.noise_dimensions = "3D"
    ripple_noise.inputs["Scale"].default_value = 3.6
    ripple_noise.inputs["Detail"].default_value = 1.6
    ripple_noise.inputs["Roughness"].default_value = 0.32
    ripple_noise.inputs["Distortion"].default_value = 0.0

    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.location = (-170, 220)
    color_ramp.color_ramp.interpolation = "EASE"
    color_ramp.color_ramp.elements[0].position = 0.22
    color_ramp.color_ramp.elements[0].color = (0.08, 0.30, 0.315, 1.0)
    color_ramp.color_ramp.elements[1].position = 0.78
    color_ramp.color_ramp.elements[1].color = (0.145, 0.39, 0.38, 1.0)

    roughness_range = nodes.new("ShaderNodeMapRange")
    roughness_range.location = (-150, 30)
    roughness_range.inputs["From Min"].default_value = 0.0
    roughness_range.inputs["From Max"].default_value = 1.0
    roughness_range.inputs["To Min"].default_value = 0.31
    roughness_range.inputs["To Max"].default_value = 0.39

    bump = nodes.new("ShaderNodeBump")
    bump.location = (150, -170)
    bump.inputs["Strength"].default_value = 0.025
    bump.inputs["Distance"].default_value = 0.02

    links.new(coordinates.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], broad_noise.inputs["Vector"])
    links.new(mapping.outputs["Vector"], ripple_noise.inputs["Vector"])
    links.new(broad_noise.outputs["Fac"], color_ramp.inputs["Fac"])
    links.new(broad_noise.outputs["Fac"], roughness_range.inputs["Value"])
    links.new(ripple_noise.outputs["Fac"], bump.inputs["Height"])
    links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(roughness_range.outputs["Result"], bsdf.inputs["Roughness"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat


def add_box_geometry(
    vertices,
    faces,
    material_ids,
    x,
    y,
    width,
    depth,
    height,
    rotation,
    wall_id,
    roof_id,
    roof_style="gable",
):
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    roof_height = min(0.28, max(0.04, min(width, depth) * 0.48))
    local = [
        (-width / 2, -depth / 2, 0),
        (width / 2, -depth / 2, 0),
        (width / 2, depth / 2, 0),
        (-width / 2, depth / 2, 0),
        (-width / 2, -depth / 2, height),
        (width / 2, -depth / 2, height),
        (width / 2, depth / 2, height),
        (-width / 2, depth / 2, height),
    ]
    if height <= 1.55 and roof_style == "gable":
        if width >= depth:
            local.extend(
                [
                    (-width / 2, 0.0, height + roof_height),
                    (width / 2, 0.0, height + roof_height),
                ]
            )
        else:
            local.extend(
                [
                    (0.0, -depth / 2, height + roof_height),
                    (0.0, depth / 2, height + roof_height),
                ]
            )
    start = len(vertices)
    for lx, ly, lz in local:
        vertices.append((x + lx * cos_r - ly * sin_r, y + lx * sin_r + ly * cos_r, lz))
    faces.extend(
        [
            (start, start + 1, start + 2, start + 3),
            (start, start + 4, start + 5, start + 1),
            (start + 1, start + 5, start + 6, start + 2),
            (start + 2, start + 6, start + 7, start + 3),
            (start + 3, start + 7, start + 4, start),
        ]
    )
    material_ids.extend([wall_id] * 5)
    if height > 1.55 or roof_style == "flat":
        faces.append((start + 4, start + 7, start + 6, start + 5))
        material_ids.append(roof_id)
    elif roof_style == "pyramid":
        apex = len(vertices)
        vertices.append((x, y, height + roof_height * 1.18))
        faces.extend(
            [
                (start + 4, start + 5, apex),
                (start + 5, start + 6, apex),
                (start + 6, start + 7, apex),
                (start + 7, start + 4, apex),
            ]
        )
        material_ids.extend([roof_id] * 4)
    elif roof_style == "hip":
        ridge_start = len(vertices)
        if width >= depth:
            ridge_local = [
                (-width * 0.31, 0.0, height + roof_height),
                (width * 0.31, 0.0, height + roof_height),
            ]
        else:
            ridge_local = [
                (0.0, -depth * 0.31, height + roof_height),
                (0.0, depth * 0.31, height + roof_height),
            ]
        for lx, ly, lz in ridge_local:
            vertices.append((x + lx * cos_r - ly * sin_r, y + lx * sin_r + ly * cos_r, lz))
        if width >= depth:
            faces.extend(
                [
                    (start + 4, ridge_start, ridge_start + 1, start + 5),
                    (start + 7, start + 6, ridge_start + 1, ridge_start),
                    (start + 4, start + 7, ridge_start),
                    (start + 5, ridge_start + 1, start + 6),
                ]
            )
        else:
            faces.extend(
                [
                    (start + 4, start + 5, ridge_start),
                    (start + 7, ridge_start + 1, start + 6),
                    (start + 4, ridge_start, ridge_start + 1, start + 7),
                    (start + 5, start + 6, ridge_start + 1, ridge_start),
                ]
            )
        material_ids.extend([roof_id] * 4)
    elif roof_style == "mansard":
        upper_start = len(vertices)
        inset_x = width * 0.36
        inset_y = depth * 0.36
        upper_local = [
            (-inset_x, -inset_y, height + roof_height),
            (inset_x, -inset_y, height + roof_height),
            (inset_x, inset_y, height + roof_height),
            (-inset_x, inset_y, height + roof_height),
        ]
        for lx, ly, lz in upper_local:
            vertices.append((x + lx * cos_r - ly * sin_r, y + lx * sin_r + ly * cos_r, lz))
        faces.extend(
            [
                (start + 4, start + 5, upper_start + 1, upper_start),
                (start + 5, start + 6, upper_start + 2, upper_start + 1),
                (start + 6, start + 7, upper_start + 3, upper_start + 2),
                (start + 7, start + 4, upper_start, upper_start + 3),
                (upper_start, upper_start + 1, upper_start + 2, upper_start + 3),
            ]
        )
        material_ids.extend([roof_id] * 5)
    elif width >= depth:
        faces.extend(
            [
                (start + 4, start + 8, start + 9, start + 5),
                (start + 7, start + 6, start + 9, start + 8),
                (start + 4, start + 7, start + 8),
                (start + 5, start + 9, start + 6),
            ]
        )
        material_ids.extend([roof_id, roof_id, wall_id, wall_id])
    else:
        faces.extend(
            [
                (start + 4, start + 7, start + 9, start + 8),
                (start + 5, start + 8, start + 9, start + 6),
                (start + 4, start + 8, start + 5),
                (start + 7, start + 6, start + 9),
            ]
        )
        material_ids.extend([roof_id, roof_id, wall_id, wall_id])


def weighted_choice(rng, options):
    total = sum(weight for _, weight in options)
    target = rng.random() * total
    accumulated = 0.0
    for value, weight in options:
        accumulated += weight
        if target <= accumulated:
            return value
    return options[-1][0]


def building_variant(rng, style, height):
    if height > 1.55:
        return "flat", "standard"
    roof_options = {
        "roman": [("gable", 0.42), ("hip", 0.3), ("flat", 0.2), ("pyramid", 0.08)],
        "medieval": [("gable", 0.43), ("hip", 0.27), ("pyramid", 0.14), ("mansard", 0.08), ("flat", 0.08)],
        "royal": [("gable", 0.2), ("hip", 0.28), ("mansard", 0.38), ("pyramid", 0.06), ("flat", 0.08)],
        "haussmann": [("mansard", 0.5), ("hip", 0.2), ("gable", 0.13), ("flat", 0.17)],
        "modern": [("flat", 0.42), ("mansard", 0.3), ("hip", 0.14), ("gable", 0.1), ("pyramid", 0.04)],
    }
    plan_options = {
        "roman": [("standard", 0.61), ("annex", 0.2), ("courtyard", 0.12), ("chapel", 0.05), ("tower", 0.02)],
        "medieval": [("standard", 0.48), ("annex", 0.25), ("tower", 0.13), ("courtyard", 0.07), ("chapel", 0.07)],
        "royal": [("standard", 0.43), ("annex", 0.24), ("courtyard", 0.19), ("tower", 0.07), ("chapel", 0.07)],
        "haussmann": [("standard", 0.44), ("annex", 0.24), ("courtyard", 0.24), ("tower", 0.04), ("chapel", 0.04)],
        "modern": [("standard", 0.52), ("annex", 0.22), ("courtyard", 0.18), ("tower", 0.04), ("chapel", 0.04)],
    }
    roof_style = weighted_choice(rng, roof_options[style])
    plan_style = weighted_choice(rng, plan_options[style])
    if plan_style == "chapel":
        roof_style = "gable"
    return roof_style, plan_style


def building_material_ids(rng, style):
    wall_options = {
        "roman": [(2, 0.42), (0, 0.25), (1, 0.16), (6, 0.08), (7, 0.09)],
        "medieval": [(0, 0.26), (1, 0.23), (2, 0.2), (6, 0.18), (7, 0.13)],
        "royal": [(1, 0.36), (0, 0.22), (2, 0.18), (7, 0.16), (6, 0.08)],
        "haussmann": [(1, 0.46), (0, 0.23), (2, 0.17), (7, 0.1), (6, 0.04)],
        "modern": [(1, 0.3), (2, 0.25), (0, 0.2), (7, 0.14), (6, 0.11)],
    }
    roof_options = {
        "roman": [(3, 0.68), (8, 0.2), (4, 0.12)],
        "medieval": [(3, 0.58), (8, 0.22), (4, 0.17), (5, 0.03)],
        "royal": [(4, 0.34), (3, 0.28), (8, 0.2), (5, 0.18)],
        "haussmann": [(4, 0.45), (5, 0.31), (3, 0.14), (8, 0.1)],
        "modern": [(5, 0.38), (4, 0.28), (3, 0.2), (8, 0.14)],
    }
    return weighted_choice(rng, wall_options[style]), weighted_choice(rng, roof_options[style])


def rotated_offset(x, y, rotation, local_x, local_y):
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    return (
        x + local_x * cos_r - local_y * sin_r,
        y + local_x * sin_r + local_y * cos_r,
    )


def house_half_extents(width, depth, plan_style):
    half_width = width * 0.5
    half_depth = depth * 0.5
    if plan_style == "annex":
        half_depth = depth * 1.16
    elif plan_style == "courtyard":
        half_depth = depth * 1.24
    elif plan_style == "tower":
        half_width *= 1.03
        half_depth *= 1.03
    elif plan_style == "chapel":
        half_width *= 1.32
        half_depth *= 1.45
    return half_width, half_depth


def footprint_grid_cells(footprint):
    x, y, half_width, half_depth, _rotation = footprint
    radius = math.hypot(half_width, half_depth)
    min_grid_x = math.floor((x - radius) / BUILDING_FOOTPRINT_CELL)
    max_grid_x = math.floor((x + radius) / BUILDING_FOOTPRINT_CELL)
    min_grid_y = math.floor((y - radius) / BUILDING_FOOTPRINT_CELL)
    max_grid_y = math.floor((y + radius) / BUILDING_FOOTPRINT_CELL)
    for grid_x in range(min_grid_x, max_grid_x + 1):
        for grid_y in range(min_grid_y, max_grid_y + 1):
            yield grid_x, grid_y


def footprints_overlap(first, second, gap=0.006):
    first_x, first_y, first_half_width, first_half_depth, first_rotation = first
    second_x, second_y, second_half_width, second_half_depth, second_rotation = second
    first_u = (math.cos(first_rotation), math.sin(first_rotation))
    first_v = (-first_u[1], first_u[0])
    second_u = (math.cos(second_rotation), math.sin(second_rotation))
    second_v = (-second_u[1], second_u[0])
    delta = (second_x - first_x, second_y - first_y)

    for axis in (first_u, first_v, second_u, second_v):
        first_radius = (
            first_half_width * abs(axis[0] * first_u[0] + axis[1] * first_u[1])
            + first_half_depth * abs(axis[0] * first_v[0] + axis[1] * first_v[1])
        )
        second_radius = (
            second_half_width * abs(axis[0] * second_u[0] + axis[1] * second_u[1])
            + second_half_depth * abs(axis[0] * second_v[0] + axis[1] * second_v[1])
        )
        distance = abs(delta[0] * axis[0] + delta[1] * axis[1])
        if distance >= first_radius + second_radius + gap:
            return False
    return True


def can_place_footprint(footprint):
    nearby_indices = set()
    for cell in footprint_grid_cells(footprint):
        nearby_indices.update(BUILDING_FOOTPRINT_GRID.get(cell, ()))
    return not any(footprints_overlap(footprint, BUILDING_FOOTPRINTS[index]) for index in nearby_indices)


def register_footprint(footprint):
    index = len(BUILDING_FOOTPRINTS)
    BUILDING_FOOTPRINTS.append(footprint)
    for cell in footprint_grid_cells(footprint):
        BUILDING_FOOTPRINT_GRID.setdefault(cell, []).append(index)


def circle_overlaps_footprint(x, y, radius, footprint, gap=0.025):
    center_x, center_y, half_width, half_depth, rotation = footprint
    delta_x = x - center_x
    delta_y = y - center_y
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    local_x = delta_x * cos_r + delta_y * sin_r
    local_y = -delta_x * sin_r + delta_y * cos_r
    closest_x = min(half_width, max(-half_width, local_x))
    closest_y = min(half_depth, max(-half_depth, local_y))
    distance_sq = (local_x - closest_x) ** 2 + (local_y - closest_y) ** 2
    return distance_sq < (radius + gap) ** 2


def can_place_tree(x, y, radius):
    query_footprint = (x, y, radius, radius, 0.0)
    nearby_indices = set()
    for cell in footprint_grid_cells(query_footprint):
        nearby_indices.update(BUILDING_FOOTPRINT_GRID.get(cell, ()))
    return not any(
        circle_overlaps_footprint(x, y, radius, BUILDING_FOOTPRINTS[index])
        for index in nearby_indices
    )


def projected_extent(half_width, half_depth, building_rotation, axis_angle):
    delta = axis_angle - building_rotation
    return abs(math.cos(delta)) * half_width + abs(math.sin(delta)) * half_depth


def reserve_landmark_footprints(era_index):
    if era_index == 0:
        register_footprint((6.4, 6.25, 1.55, 1.08, 0.0))
        register_footprint((1.4, -8.5, 1.45, 1.02, 0.0))
    if era_index >= 1:
        register_footprint((0.15, 0.25, 1.15, 0.7, -0.55))
    if era_index >= 2:
        register_footprint((-10.8, 11.85, 2.15, 1.65, 0.0))
    if era_index >= 3:
        register_footprint((-40.2, 23.2, 0.5, 0.42, 0.0))
    if era_index >= 4:
        register_footprint((-40.6, 6.0, 1.0, 0.82, 0.0))
        register_footprint((-45.0, 28.5, 2.6, 1.85, 0.0))
        for station in MODERN_STATIONS:
            station_x, station_y = station["location"]
            station_width, station_depth = station["size"]
            register_footprint(
                (
                    station_x,
                    station_y,
                    station_width * 0.58,
                    station_depth * 0.62,
                    station["rotation"],
                )
            )


def begin_era_footprints(era_index):
    BUILDING_FOOTPRINTS.clear()
    BUILDING_FOOTPRINT_GRID.clear()
    reserve_landmark_footprints(era_index)


def archive_era_footprints():
    ALL_ERA_FOOTPRINTS.extend(BUILDING_FOOTPRINTS)


def restore_tree_exclusion_footprints():
    BUILDING_FOOTPRINTS.clear()
    BUILDING_FOOTPRINT_GRID.clear()
    for footprint in ALL_ERA_FOOTPRINTS:
        register_footprint(footprint)


def audit_footprint_overlaps():
    checked_pairs = set()
    overlap_count = 0
    for indices in BUILDING_FOOTPRINT_GRID.values():
        for first_position, first_index in enumerate(indices):
            for second_index in indices[first_position + 1 :]:
                pair = (min(first_index, second_index), max(first_index, second_index))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                if footprints_overlap(
                    BUILDING_FOOTPRINTS[first_index],
                    BUILDING_FOOTPRINTS[second_index],
                    gap=-0.0001,
                ):
                    overlap_count += 1
    print(f"Footprint audit: {len(BUILDING_FOOTPRINTS)} placements, {overlap_count} intersections")
    return overlap_count


def add_vertical_panel_geometry(
    vertices,
    faces,
    material_ids,
    x,
    y,
    z,
    panel_width,
    panel_height,
    rotation,
    local_center_x,
    local_center_y,
    tangent_axis,
    material_id,
):
    if tangent_axis == "x":
        local = [
            (local_center_x - panel_width * 0.5, local_center_y, z - panel_height * 0.5),
            (local_center_x + panel_width * 0.5, local_center_y, z - panel_height * 0.5),
            (local_center_x + panel_width * 0.5, local_center_y, z + panel_height * 0.5),
            (local_center_x - panel_width * 0.5, local_center_y, z + panel_height * 0.5),
        ]
    else:
        local = [
            (local_center_x, local_center_y - panel_width * 0.5, z - panel_height * 0.5),
            (local_center_x, local_center_y + panel_width * 0.5, z - panel_height * 0.5),
            (local_center_x, local_center_y + panel_width * 0.5, z + panel_height * 0.5),
            (local_center_x, local_center_y - panel_width * 0.5, z + panel_height * 0.5),
        ]
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    start = len(vertices)
    for local_x, local_y, local_z in local:
        vertices.append(
            (
                x + local_x * cos_r - local_y * sin_r,
                y + local_x * sin_r + local_y * cos_r,
                local_z,
            )
        )
    faces.append((start, start + 1, start + 2, start + 3))
    material_ids.append(material_id)


def add_facade_detail_geometry(
    vertices,
    faces,
    material_ids,
    x,
    y,
    width,
    depth,
    height,
    rotation,
    style,
    rng,
):
    max_floors = {"roman": 2, "medieval": 3, "royal": 4, "haussmann": 5, "modern": 8}[style]
    nominal_floor_height = {"roman": 0.17, "medieval": 0.15, "royal": 0.145, "haussmann": 0.14, "modern": 0.16}[style]
    floor_count = max(1, min(max_floors, round(height / nominal_floor_height)))
    column_cap = 5 if style in {"haussmann", "modern"} else 4
    front_columns = max(1, min(column_cap, int(width / 0.09)))
    side_columns = max(1, min(column_cap, int(depth / 0.09)))
    aspect_scale = {"roman": 0.72, "medieval": 0.68, "royal": 0.9, "haussmann": 0.88, "modern": 1.16}[style]
    window_height = min(0.095, max(0.034, height / (floor_count + 1) * 0.52))
    front_window_width = min(0.072, max(0.025, width / (front_columns * 2.15) * aspect_scale))
    side_window_width = min(0.068, max(0.024, depth / (side_columns * 2.15) * aspect_scale))
    warm_probability = {"roman": 0.03, "medieval": 0.07, "royal": 0.12, "haussmann": 0.16, "modern": 0.24}[style]
    panel_offset = 0.0045
    frame_scale = {
        "roman": (1.34, 1.24),
        "medieval": (1.3, 1.22),
        "royal": (1.24, 1.2),
        "haussmann": (1.22, 1.18),
        "modern": (1.14, 1.14),
    }[style]

    if floor_count == 1:
        floor_heights = [height * 0.56]
    else:
        floor_heights = [
            height * 0.28 + height * 0.5 * floor_index / (floor_count - 1)
            for floor_index in range(floor_count)
        ]

    def glazing_id():
        return BUILDING_WINDOW_WARM_ID if rng.random() < warm_probability else BUILDING_WINDOW_DARK_ID

    def add_window(local_center_x, local_center_y, tangent_axis, window_z, window_width, facade_side):
        if tangent_axis == "x":
            frame_center_x = local_center_x
            frame_center_y = facade_side * (depth * 0.5 + panel_offset)
            glass_center_x = local_center_x
            glass_center_y = facade_side * (depth * 0.5 + panel_offset * 1.7)
        else:
            frame_center_x = facade_side * (width * 0.5 + panel_offset)
            frame_center_y = local_center_y
            glass_center_x = facade_side * (width * 0.5 + panel_offset * 1.7)
            glass_center_y = local_center_y
        add_vertical_panel_geometry(
            vertices,
            faces,
            material_ids,
            x,
            y,
            window_z,
            window_width * frame_scale[0],
            window_height * frame_scale[1],
            rotation,
            frame_center_x,
            frame_center_y,
            tangent_axis,
            BUILDING_TRIM_ID,
        )
        add_vertical_panel_geometry(
            vertices,
            faces,
            material_ids,
            x,
            y,
            window_z,
            window_width,
            window_height,
            rotation,
            glass_center_x,
            glass_center_y,
            tangent_axis,
            glazing_id(),
        )

    for facade_side in (-1.0, 1.0):
        for floor_index, window_z in enumerate(floor_heights):
            for column_index in range(front_columns):
                if facade_side < 0.0 and floor_index == 0 and column_index == front_columns // 2:
                    continue
                local_x = width * 0.76 * ((column_index + 0.5) / front_columns - 0.5)
                add_window(local_x, 0.0, "x", window_z, front_window_width, facade_side)

    for facade_side in (-1.0, 1.0):
        for window_z in floor_heights:
            for column_index in range(side_columns):
                local_y = depth * 0.76 * ((column_index + 0.5) / side_columns - 0.5)
                add_window(0.0, local_y, "y", window_z, side_window_width, facade_side)

    if style in {"royal", "haussmann"}:
        band_levels = [height * 0.88]
        if floor_count >= 4:
            band_levels.append(height * 0.22)
        for band_z in band_levels:
            band_height = 0.012 if style == "royal" else 0.01
            for facade_side in (-1.0, 1.0):
                add_vertical_panel_geometry(
                    vertices,
                    faces,
                    material_ids,
                    x,
                    y,
                    band_z,
                    width * 0.94,
                    band_height,
                    rotation,
                    0.0,
                    facade_side * (depth * 0.5 + panel_offset * 1.05),
                    "x",
                    BUILDING_TRIM_ID,
                )
                add_vertical_panel_geometry(
                    vertices,
                    faces,
                    material_ids,
                    x,
                    y,
                    band_z,
                    depth * 0.94,
                    band_height,
                    rotation,
                    facade_side * (width * 0.5 + panel_offset * 1.05),
                    0.0,
                    "y",
                    BUILDING_TRIM_ID,
                )

    door_height = min(0.15, max(0.055, height * 0.46))
    door_width = min(0.08, max(0.032, width * 0.22))
    add_vertical_panel_geometry(
        vertices,
        faces,
        material_ids,
        x,
        y,
        0.018 + door_height * 0.5,
        door_width * 1.24,
        door_height * 1.1,
        rotation,
        0.0,
        -(depth * 0.5 + panel_offset),
        "x",
        BUILDING_TRIM_ID,
    )
    add_vertical_panel_geometry(
        vertices,
        faces,
        material_ids,
        x,
        y,
        0.018 + door_height * 0.5,
        door_width,
        door_height,
        rotation,
        0.0,
        -(depth * 0.5 + panel_offset * 1.7),
        "x",
        BUILDING_DOOR_ID,
    )


def add_house_geometry(
    vertices,
    faces,
    material_ids,
    x,
    y,
    width,
    depth,
    height,
    rotation,
    wall_id,
    roof_id,
    roof_style,
    plan_style,
    style,
    rng,
):
    add_box_geometry(
        vertices,
        faces,
        material_ids,
        x,
        y,
        width,
        depth,
        height,
        rotation,
        wall_id,
        roof_id,
        roof_style,
    )
    add_facade_detail_geometry(
        vertices,
        faces,
        material_ids,
        x,
        y,
        width,
        depth,
        height,
        rotation,
        style,
        rng,
    )
    if plan_style == "standard":
        return

    side = rng.choice([-1.0, 1.0])
    front = rng.choice([-1.0, 1.0])
    if plan_style in {"annex", "courtyard"}:
        wing_sides = [side] if plan_style == "annex" else [-1.0, 1.0]
        for wing_side in wing_sides:
            wing_width = width * (0.42 if plan_style == "annex" else 0.3)
            wing_depth = depth * (1.42 if plan_style == "annex" else 1.58)
            wing_x = wing_side * (width * 0.5 - wing_width * 0.5)
            wing_y = front * depth * 0.43
            world_x, world_y = rotated_offset(x, y, rotation, wing_x, wing_y)
            wing_roof = "hip" if roof_style == "pyramid" else roof_style
            wing_height = height * rng.uniform(0.78, 0.93)
            add_box_geometry(
                vertices,
                faces,
                material_ids,
                world_x,
                world_y,
                wing_width,
                wing_depth,
                wing_height,
                rotation,
                wall_id,
                roof_id,
                wing_roof,
            )
            add_facade_detail_geometry(
                vertices,
                faces,
                material_ids,
                world_x,
                world_y,
                wing_width,
                wing_depth,
                wing_height,
                rotation,
                style,
                rng,
            )
    elif plan_style == "tower":
        tower_size = max(0.065, min(width, depth) * 0.62)
        local_x = side * (width * 0.5 - tower_size * 0.48)
        local_y = front * (depth * 0.5 - tower_size * 0.48)
        world_x, world_y = rotated_offset(x, y, rotation, local_x, local_y)
        tower_height = height * rng.uniform(1.25, 1.55)
        add_box_geometry(
            vertices,
            faces,
            material_ids,
            world_x,
            world_y,
            tower_size,
            tower_size,
            tower_height,
            rotation,
            wall_id,
            roof_id,
            "pyramid",
        )
        add_facade_detail_geometry(
            vertices,
            faces,
            material_ids,
            world_x,
            world_y,
            tower_size,
            tower_size,
            tower_height,
            rotation,
            style,
            rng,
        )
    elif plan_style == "chapel":
        transept_width = max(0.065, width * 0.38)
        transept_depth = depth * 1.38
        add_box_geometry(
            vertices,
            faces,
            material_ids,
            x,
            y,
            transept_width,
            transept_depth,
            height * 0.82,
            rotation,
            wall_id,
            roof_id,
            "gable",
        )
        add_facade_detail_geometry(
            vertices,
            faces,
            material_ids,
            x,
            y,
            transept_width,
            transept_depth,
            height * 0.82,
            rotation,
            style,
            rng,
        )
        tower_size = max(0.06, min(width, depth) * 0.58)
        tower_x, tower_y = rotated_offset(x, y, rotation, -width * 0.3, 0.0)
        tower_height = height * rng.uniform(1.35, 1.65)
        add_box_geometry(
            vertices,
            faces,
            material_ids,
            tower_x,
            tower_y,
            tower_size,
            tower_size,
            tower_height,
            rotation,
            wall_id,
            roof_id,
            "pyramid",
        )
        add_facade_detail_geometry(
            vertices,
            faces,
            material_ids,
            tower_x,
            tower_y,
            tower_size,
            tower_size,
            tower_height,
            rotation,
            style,
            rng,
        )


def add_rect_geometry(vertices, faces, material_ids, x, y, width, depth, rotation, z, material_id):
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    local = [
        (-width / 2, -depth / 2, z),
        (width / 2, -depth / 2, z),
        (width / 2, depth / 2, z),
        (-width / 2, depth / 2, z),
    ]
    start = len(vertices)
    for lx, ly, lz in local:
        vertices.append((x + lx * cos_r - ly * sin_r, y + lx * sin_r + ly * cos_r, lz))
    faces.append((start, start + 1, start + 2, start + 3))
    material_ids.append(material_id)


def mesh_object(name, vertices, faces, material_ids, materials):
    mesh = bpy.data.meshes.new(name=f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for material in materials:
        mesh.materials.append(material)
    for polygon, material_id in zip(mesh.polygons, material_ids):
        polygon.material_index = material_id
    return obj


def geometry_buckets(count):
    return [{"vertices": [], "faces": [], "material_ids": []} for _ in range(count)]


def polygon_reveal_metrics(polygon):
    center_x = sum(point[0] for point in polygon) / len(polygon)
    center_y = sum(point[1] for point in polygon) / len(polygon)
    max_distance = max(math.hypot(x - center_x, y - center_y) for x, y in polygon)
    return (center_x, center_y), max(0.001, max_distance)


def reveal_bucket_index(x, y, center, max_distance, count, jitter):
    center_x, center_y = center
    radial = min(1.0, math.hypot(x - center_x, y - center_y) / max_distance)
    sweep = (math.atan2(y - center_y, x - center_x) + math.pi) / (2.0 * math.pi)
    progress = min(0.999, max(0.0, radial * 0.68 + sweep * 0.22 + jitter * 0.1))
    return min(count - 1, int(progress * count))


def growth_progress(x, y, era_index, jitter=0.5):
    radius = ERA_GROWTH_RADII[era_index]
    center_scores = []
    for center_x, center_y, delay, speed in ERA_GROWTH_CENTERS[era_index]:
        dx = x - center_x
        dy = y - center_y
        distance = math.hypot(dx, dy)
        direction_bias = 0.035 * (0.5 + 0.5 * math.sin(math.atan2(dy, dx) * 2.3 + era_index))
        center_scores.append(delay + distance / radius * speed + direction_bias)
    progress = min(center_scores)

    if era_index > 0:
        previous_polygon = CITY_POLYGONS[era_index - 1]
        if point_in_polygon(x, y, previous_polygon):
            progress *= 0.82
        else:
            frontier_distance = polygon_edge_distance(x, y, previous_polygon)
            frontier_wave = min(1.0, frontier_distance / max(1.0, radius * 0.42))
            sector = 0.5 + 0.5 * math.sin(
                math.atan2(y, x) * (2.4 + era_index * 0.37) + era_index * 1.71
            )
            connection_score = 0.08 + frontier_wave * 0.58 + sector * 0.14
            progress = progress * 0.62 + connection_score * 0.38

    local_wave = math.sin(x * 0.41 + y * 0.29 + era_index * 1.37) * 0.035
    progress += local_wave + (jitter - 0.5) * 0.11
    return min(0.999, max(0.0, progress))


def growth_bucket_index(x, y, era_index, count, jitter):
    return min(count - 1, int(growth_progress(x, y, era_index, jitter) * count))


def road_growth_progress(x, y, phase, jitter=0.5):
    if phase == 0:
        distance = math.hypot(x, y)
        angle = math.atan2(y, x)
        progress = distance / 13.5 * 0.86
        progress += (0.5 + 0.5 * math.sin(angle * 3.0 + 0.7)) * 0.08
        progress += (jitter - 0.5) * 0.035
        return min(0.999, max(0.0, progress))
    return min(0.999, max(0.0, growth_progress(x, y, phase, jitter) * 0.93))


def add_road_draw_shape(obj, bucket):
    ranges = bucket.get("road_ranges", ())
    if not ranges:
        return None
    obj.shape_key_add(name="Basis")
    collapsed = obj.shape_key_add(name="Road_Draw_Collapsed")
    for vertex_start in ranges:
        collapsed.data[vertex_start + 1].co = collapsed.data[vertex_start].co
        collapsed.data[vertex_start + 2].co = collapsed.data[vertex_start + 3].co
    return collapsed


def batched_stagger_frame(
    item_index,
    item_count,
    start_frame,
    reveal_frames,
    timing_rng,
    stride_frames=BUILDING_BATCH_STRIDE_FRAMES,
    batch_spread_frames=BUILDING_BATCH_SPREAD_FRAMES,
):
    if item_count <= 1:
        return start_frame

    usable_batch_span = max(0, reveal_frames - batch_spread_frames)
    target_batch_count = max(1, math.floor(usable_batch_span / stride_frames) + 1)
    batch_capacity = max(1, math.ceil(item_count / target_batch_count))
    batch_count = max(1, math.ceil(item_count / batch_capacity))

    batch_index = min(batch_count - 1, item_index // batch_capacity)
    batch_first = batch_index * batch_capacity
    batch_size = min(batch_capacity, item_count - batch_first)
    within_batch = item_index - batch_first
    within_progress = within_batch / max(1, batch_size - 1)

    if batch_count <= 1:
        batch_start = start_frame
    else:
        batch_start = start_frame + round(
            usable_batch_span * batch_index / (batch_count - 1)
        )
    within_offset = round(batch_spread_frames * within_progress)
    frame_jitter = timing_rng.choice([-1, 0, 0, 0, 1])
    return min(
        start_frame + reveal_frames,
        max(start_frame, batch_start + within_offset + frame_jitter),
    )


def finalize_chunked_layer(
    name,
    buckets,
    materials,
    start_frame,
    reveal_frames,
    grow_frames,
    road=False,
    seed=0,
):
    root = bpy.data.objects.new(name, None)
    root.empty_display_type = "PLAIN_AXES"
    bpy.context.collection.objects.link(root)
    active_buckets = [
        (source_index, bucket)
        for source_index, bucket in enumerate(buckets)
        if bucket["vertices"]
    ]
    active_count = len(active_buckets)
    timing_rng = random.Random(seed + start_frame * 31 + len(buckets) * 17)
    for active_index, (source_index, bucket) in enumerate(active_buckets):
        chunk = mesh_object(
            f"{name}_Chunk_{source_index:05d}",
            bucket["vertices"],
            bucket["faces"],
            bucket["material_ids"],
            materials,
        )
        chunk.parent = root
        if road:
            active_progress = active_index / max(1, active_count - 1)
            chunk_start = start_frame + round(reveal_frames * active_progress)
        else:
            chunk_start = batched_stagger_frame(
                active_index,
                active_count,
                start_frame,
                reveal_frames,
                timing_rng,
            )
        max_height = max(vertex[2] for vertex in bucket["vertices"])
        if road:
            duration = max(8, round(grow_frames * timing_rng.uniform(0.72, 1.35)))
            shape_key = add_road_draw_shape(chunk, bucket)
            animate_road_draw(chunk, shape_key, chunk_start, duration)
        else:
            height_factor = min(0.12, max_height * 0.08)
            duration_factor = timing_rng.uniform(0.82, 1.08) + height_factor
            duration = min(9, max(5, round(grow_frames * duration_factor)))
            chunk["growth_start_frame"] = chunk_start
            chunk["growth_duration_frames"] = duration
            animate_building_sprout(chunk, chunk_start, duration=duration)
    return root


def river_center(x):
    points = load_geodata()["river"]
    if x <= points[0][0]:
        start, end = points[0], points[1]
    elif x >= points[-1][0]:
        start, end = points[-2], points[-1]
    else:
        start, end = points[0], points[1]
        for candidate_start, candidate_end in zip(points, points[1:]):
            if candidate_start[0] <= x <= candidate_end[0]:
                start, end = candidate_start, candidate_end
                break
    span = end[0] - start[0]
    if abs(span) < 1e-6:
        return (start[1] + end[1]) * 0.5
    t = (x - start[0]) / span
    return start[1] + (end[1] - start[1]) * t


def river_half_width(x):
    base_width = 1.62 + 0.16 * (0.5 + 0.5 * math.sin((x + 2.0) / 8.5))
    cite_channel = 2.18 * math.exp(-((x + 2.0) / 11.5) ** 4)
    saint_louis_channel = 0.68 * math.exp(-((x - 5.5) / 6.8) ** 4)
    return base_width + cite_channel + saint_louis_channel


def point_on_island(x, y):
    return any(point_in_polygon(x, y, polygon) for polygon in load_geodata()["islands"].values())


def river_clearance(x, y):
    best_clearance = float("inf")
    points = extended_river_points()
    for start, end in zip(points, points[1:]):
        if x < min(start[0], end[0]) - 8.0 or x > max(start[0], end[0]) + 8.0:
            continue
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-8:
            amount = 0.0
        else:
            amount = max(
                0.0,
                min(1.0, ((x - start[0]) * dx + (y - start[1]) * dy) / length_sq),
            )
        nearest_x = start[0] + dx * amount
        nearest_y = start[1] + dy * amount
        local_width = (
            river_half_width(start[0]) * (1.0 - amount)
            + river_half_width(end[0]) * amount
        )
        clearance = math.hypot(x - nearest_x, y - nearest_y) - local_width
        best_clearance = min(best_clearance, clearance)
    if best_clearance == float("inf"):
        return abs(y - river_center(x)) - river_half_width(x)
    return best_clearance


def is_water(x, y, margin=0.0):
    if point_on_island(x, y):
        return False
    return river_clearance(x, y) < margin


def assert_landmark_on_land(name, x, y, half_width, half_depth, rotation=0.0):
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    for u in (-1.0, -0.5, 0.0, 0.5, 1.0):
        for v in (-1.0, -0.5, 0.0, 0.5, 1.0):
            sample_x = x + u * half_width * cos_r - v * half_depth * sin_r
            sample_y = y + u * half_width * sin_r + v * half_depth * cos_r
            if is_water(sample_x, sample_y, margin=0.035):
                raise RuntimeError(
                    f"{name} footprint enters the river at ({sample_x:.3f}, {sample_y:.3f})"
                )


def point_in_polygon(x, y, polygon):
    inside = False
    previous = polygon[-1]
    for current in polygon:
        x1, y1 = previous
        x2, y2 = current
        if (y1 > y) != (y2 > y):
            crossing_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < crossing_x:
                inside = not inside
        previous = current
    return inside


def city_contains(era_index, x, y):
    return point_in_polygon(x, y, CITY_POLYGONS[era_index])


def first_urban_era(x, y):
    for era_index in range(len(CITY_POLYGONS)):
        if city_contains(era_index, x, y):
            return era_index
    return None


def is_park(x, y):
    bois_boulogne = ((x + 56.0) / 7.5) ** 2 + ((y - 4.0) / 11.0) ** 2 < 1.0
    bois_vincennes = ((x - 44.0) / 9.5) ** 2 + ((y + 5.0) / 13.0) ** 2 < 1.0
    central_park = ((x + 7.0) / 3.6) ** 2 + ((y - 12.0) / 2.8) ** 2 < 1.0
    southern_park = ((x - 9.0) / 3.2) ** 2 + ((y + 15.0) / 2.6) ** 2 < 1.0
    champ_de_mars = ((x + 40.6) / 2.25) ** 2 + ((y - 3.7) / 4.9) ** 2 < 1.0
    return bois_boulogne or bois_vincennes or central_park or southern_park or champ_de_mars


def road_specs_for_phase(phase):
    if phase in ROAD_SPEC_CACHE:
        return ROAD_SPEC_CACHE[phase]
    bridge_xs = [-6.0, -2.3, 0.7]
    riverfront_xs = [-8.5, -6.0, -3.8, -1.5, 0.7, 3.5, 6.5, 8.5]

    def bank_path(side, setback):
        return [
            (
                x,
                river_center(x) + side * (river_half_width(x) + setback),
            )
            for x in riverfront_xs
        ]

    roman_specs = [
        (0.095, bank_path(-1.0, 0.42)),
        (0.095, bank_path(1.0, 0.42)),
        (0.105, [(-8.4, -6.8), (-2.0, -4.2), (4.2, -1.6), (6.4, 6.25)]),
        (0.095, [(-7.5, 5.9), (-2.0, 2.8), (1.4, -8.5)]),
    ]
    for grid_x in (-8.0, -6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0, 8.0):
        roman_specs.append((0.075 if grid_x % 4 else 0.092, [(grid_x, -10.2), (grid_x, 7.2)]))
    for grid_y in (-9.0, -7.0, -5.0, -3.0, -1.0, 1.0, 3.0, 5.0, 7.0):
        roman_specs.append((0.075 if grid_y % 4 else 0.092, [(-8.6, grid_y), (8.6, grid_y)]))
    for index, x in enumerate(bridge_xs):
        south_y = river_center(x) - river_half_width(x) - 0.34
        north_y = river_center(x) + river_half_width(x) + 0.34
        roman_specs.extend(
            [
                (
                    0.075,
                    [
                        (x + 0.55 - index * 0.18, south_y - 3.2),
                        (x + 0.2, south_y - 1.45),
                        (x, south_y),
                    ],
                ),
                (
                    0.075,
                    [
                        (x - 0.5 + index * 0.16, north_y + 3.0),
                        (x - 0.18, north_y + 1.35),
                        (x, north_y),
                    ],
                ),
            ]
        )
    specs = {
        0: roman_specs,
        1: [
            (0.15, [(-18, -8), (-11, -5), (-4, -2), (3, -2), (10, -4), (17, -8)]),
            (0.15, [(-17, 6), (-10, 7), (-2, 6), (7, 8), (15, 6)]),
            (0.14, [(-14, -13), (-9, -7), (-5, -2), (-2, 4), (0, 13)]),
            (0.14, [(13, -12), (9, -6), (7, 0), (10, 6), (13, 11)]),
            (0.13, [(-17, 0), (-10, -1), (-5, -4), (-1, -9), (2, -14)]),
        ],
        2: [
            (0.17, [(-28, -15), (-18, -11), (-8, -8), (3, -8), (14, -11), (25, -15)]),
            (0.17, [(-28, 12), (-17, 12), (-7, 10), (4, 11), (15, 14), (24, 11)]),
            (0.16, [(-23, -21), (-20, -12), (-17, -3), (-14, 7), (-12, 18)]),
            (0.16, [(20, -20), (17, -10), (16, -1), (18, 9), (15, 18)]),
            (0.15, [(-26, 1), (-18, 3), (-9, 2), (-1, 4), (8, 4), (17, 2), (27, 1)]),
            (0.15, [(-7, -23), (-6, -15), (-4, -8), (-1, -2), (2, 7), (5, 20)]),
        ],
        3: [
            (0.30, [(-39, -22), (-27, -15), (-14, -8), (-2, -1), (12, 7), (29, 17)]),
            (0.28, [(-38, 18), (-25, 12), (-12, 6), (0, 1), (15, -6), (35, -17)]),
            (0.28, [(-32, -27), (-26, -14), (-20, -3), (-15, 10), (-8, 27)]),
            (0.26, [(30, -25), (24, -13), (21, -2), (23, 11), (28, 24)]),
            (0.24, [(-41, 1), (-30, 2), (-19, 1), (-7, 3), (5, 2), (18, 0), (40, 3)]),
            (0.24, [(-8, -31), (-6, -20), (-5, -10), (-2, -2), (2, 9), (7, 29)]),
        ],
        4: [
            (0.22, [(-58, -20), (-45, -19), (-31, -20), (-17, -23), (-2, -26), (14, -25), (31, -22), (50, -17)]),
            (0.22, [(-55, 20), (-39, 22), (-22, 25), (-4, 28), (15, 27), (34, 23), (52, 16)]),
            (0.20, [(-55, -33), (-43, -25), (-31, -15), (-20, -5), (-10, 7), (-1, 20), (7, 39)]),
            (0.20, [(50, -32), (39, -22), (31, -10), (27, 2), (31, 17), (39, 31)]),
            (0.19, [(-58, -2), (-44, -4), (-29, -2), (-15, -4), (1, -2), (18, -4), (35, -3), (56, -1)]),
        ],
    }
    result = list(specs[phase])
    rng = random.Random(1200 + phase)
    polygon = CITY_POLYGONS[phase]
    min_x = min(point[0] for point in polygon)
    max_x = max(point[0] for point in polygon)
    min_y = min(point[1] for point in polygon)
    max_y = max(point[1] for point in polygon)
    local_counts = [0, 8, 14, 22, 30]
    local_lengths = [6.0, 10.0, 15.0, 20.0, 26.0]
    created = 0
    while created < local_counts[phase]:
        cx = rng.uniform(min_x, max_x)
        cy = rng.uniform(min_y, max_y)
        if not city_contains(phase, cx, cy):
            continue
        axis = rng.choice([0.0, math.pi / 2, math.pi / 4, -math.pi / 4])
        angle = axis + rng.uniform(-0.18, 0.18)
        length = local_lengths[phase] * rng.uniform(0.55, 1.0)
        nx = -math.sin(angle)
        ny = math.cos(angle)
        curve = rng.uniform(-1.2, 1.2) * (0.25 + phase * 0.14)
        start = (cx - math.cos(angle) * length * 0.5, cy - math.sin(angle) * length * 0.5)
        middle = (cx + nx * curve, cy + ny * curve)
        end = (cx + math.cos(angle) * length * 0.5, cy + math.sin(angle) * length * 0.5)
        result.append((0.08 + phase * 0.014, [start, middle, end]))
        created += 1
    ROAD_SPEC_CACHE[phase] = result
    return result


def point_segment_distance(x, y, start, end):
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(x - x1, y - y1), 0.0
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / length_sq))
    nearest_x = x1 + t * dx
    nearest_y = y1 + t * dy
    return math.hypot(x - nearest_x, y - nearest_y), math.atan2(dy, dx)


def point_near_modern_rail(x, y, margin=0.3):
    for station in MODERN_STATIONS:
        station_x, station_y = station["location"]
        station_width, station_depth = station["size"]
        if math.hypot(x - station_x, y - station_y) < max(station_width, station_depth) * 0.72 + margin:
            return True
        for start, end in zip(station["track"], station["track"][1:]):
            distance, _angle = point_segment_distance(x, y, start, end)
            if distance < margin:
                return True
    return False


def polygon_edge_distance(x, y, polygon):
    return min(
        point_segment_distance(x, y, start, end)[0]
        for start, end in zip(polygon, polygon[1:] + polygon[:1])
    )


def build_real_road_index():
    global REAL_ROAD_SEGMENTS, REAL_ROAD_GRID
    if REAL_ROAD_SEGMENTS is not None:
        return REAL_ROAD_SEGMENTS, REAL_ROAD_GRID
    segments = []
    grid = {phase: {} for phase in range(1, 5)}
    for road in load_geodata()["roads"]:
        for start, end in zip(road["points"], road["points"][1:]):
            segment_index = len(segments)
            segments.append((road["phase"], road["width"], start, end, road["bridge"]))
            min_cell_x = math.floor(min(start[0], end[0]) / ROAD_GRID_SIZE)
            max_cell_x = math.floor(max(start[0], end[0]) / ROAD_GRID_SIZE)
            min_cell_y = math.floor(min(start[1], end[1]) / ROAD_GRID_SIZE)
            max_cell_y = math.floor(max(start[1], end[1]) / ROAD_GRID_SIZE)
            for cell_x in range(min_cell_x, max_cell_x + 1):
                for cell_y in range(min_cell_y, max_cell_y + 1):
                    grid[road["phase"]].setdefault((cell_x, cell_y), []).append(segment_index)
    REAL_ROAD_SEGMENTS = segments
    REAL_ROAD_GRID = grid
    cell_count = sum(len(phase_grid) for phase_grid in grid.values())
    print(f"Real road index: {len(segments)} segments in {cell_count} phase cells")
    return REAL_ROAD_SEGMENTS, REAL_ROAD_GRID


def nearest_road(era_index, x, y):
    best_distance = float("inf")
    best_angle = 0.0
    best_width = 0.0
    for width, points in road_specs_for_phase(0):
        for start, end in zip(points, points[1:]):
            distance, angle = point_segment_distance(x, y, start, end)
            if distance < best_distance:
                best_distance = distance
                best_angle = angle
                best_width = width
    if era_index == 0:
        return best_distance, best_angle, best_width

    segments, grid = build_real_road_index()
    center_cell_x = math.floor(x / ROAD_GRID_SIZE)
    center_cell_y = math.floor(y / ROAD_GRID_SIZE)
    candidates = set()
    for search_radius in (1, 2, 3):
        for phase in range(1, era_index + 1):
            phase_grid = grid[phase]
            for cell_x in range(center_cell_x - search_radius, center_cell_x + search_radius + 1):
                for cell_y in range(center_cell_y - search_radius, center_cell_y + search_radius + 1):
                    candidates.update(phase_grid.get((cell_x, cell_y), []))
        if candidates:
            break
    for segment_index in candidates:
        phase, width, start, end, _ = segments[segment_index]
        distance, angle = point_segment_distance(x, y, start, end)
        if distance < best_distance:
            best_distance = distance
            best_angle = angle
            best_width = width
    return best_distance, best_angle, best_width


def create_land(material):
    bpy.ops.mesh.primitive_plane_add(size=180, location=(0, 0, -0.04))
    land = bpy.context.object
    land.name = "Land"
    land.data.materials.append(material)
    return land


def extended_river_points():
    global RIVER_POINTS_CACHE
    if RIVER_POINTS_CACHE is not None:
        return RIVER_POINTS_CACHE
    points = [list(point) for point in load_geodata()["river"]]
    if points[0][0] > -92.0:
        slope = (points[1][1] - points[0][1]) / max(0.001, points[1][0] - points[0][0])
        points.insert(0, [-92.0, points[0][1] + slope * (-92.0 - points[0][0])])
    if points[-1][0] < 92.0:
        slope = (points[-1][1] - points[-2][1]) / max(0.001, points[-1][0] - points[-2][0])
        points.append([92.0, points[-1][1] + slope * (92.0 - points[-1][0])])
    RIVER_POINTS_CACHE = points
    return RIVER_POINTS_CACHE


def create_river(material):
    vertices = []
    faces = []
    points = extended_river_points()
    for index, (x, y) in enumerate(points):
        previous = points[max(0, index - 1)]
        following = points[min(len(points) - 1, index + 1)]
        slope = (following[1] - previous[1]) / max(0.001, following[0] - previous[0])
        normal = Vector((-slope, 1.0)).normalized()
        half_width = river_half_width(x)
        vertices.append((x + normal.x * half_width, y + normal.y * half_width, 0.02))
        vertices.append((x - normal.x * half_width, y - normal.y * half_width, 0.02))
    for index in range(len(points) - 1):
        start = index * 2
        faces.append((start, start + 2, start + 3, start + 1))
    river = mesh_object("Seine", vertices, faces, [0] * len(faces), [material])
    return river


def create_riverbank(material):
    vertices = []
    faces = []
    points = extended_river_points()
    bank_width = 0.58
    for index, (x, y) in enumerate(points):
        previous = points[max(0, index - 1)]
        following = points[min(len(points) - 1, index + 1)]
        slope = (following[1] - previous[1]) / max(0.001, following[0] - previous[0])
        normal = Vector((-slope, 1.0)).normalized()
        inner = river_half_width(x) - 0.04
        outer = river_half_width(x) + bank_width
        vertices.extend(
            [
                (x + normal.x * inner, y + normal.y * inner, 0.027),
                (x + normal.x * outer, y + normal.y * outer, 0.027),
                (x - normal.x * inner, y - normal.y * inner, 0.027),
                (x - normal.x * outer, y - normal.y * outer, 0.027),
            ]
        )
    for index in range(len(points) - 1):
        start = index * 4
        following = start + 4
        faces.append((start, following, following + 1, start + 1))
        faces.append((start + 2, start + 3, following + 3, following + 2))
    return mesh_object("Seine_Riverbank", vertices, faces, [0] * len(faces), [material])


def create_island_margin(material, name, polygon, expansion=1.13):
    center_x = sum(point[0] for point in polygon) / len(polygon)
    center_y = sum(point[1] for point in polygon) / len(polygon)
    inner = [(x, y, 0.032) for x, y in polygon]
    outer = [
        (
            center_x + (x - center_x) * expansion,
            center_y + (y - center_y) * expansion,
            0.032,
        )
        for x, y in polygon
    ]
    vertices = inner + outer
    faces = []
    count = len(polygon)
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, following, count + following, count + index))
    return mesh_object(name, vertices, faces, [0] * len(faces), [material])


def create_island(material, name, polygon):
    vertices = [(x, y, 0.055) for x, y in polygon]
    face = tuple(range(len(vertices)))
    return mesh_object(name, vertices, [face], [0], [material])


def create_island_building_layer(
    name,
    island_key,
    era_index,
    polygon,
    count,
    seed,
    style,
    materials,
    start_frame,
    reveal_frames,
    chunk_count,
    grow_frames,
):
    rng = random.Random(seed)
    reveal_rng = random.Random(seed + 10000)
    buckets = geometry_buckets(chunk_count)
    accepted = 0
    attempts = 0
    min_x = min(point[0] for point in polygon)
    max_x = max(point[0] for point in polygon)
    min_y = min(point[1] for point in polygon)
    max_y = max(point[1] for point in polygon)
    while accepted < count and attempts < count * 300:
        attempts += 1
        x = rng.uniform(min_x, max_x)
        y = rng.uniform(min_y, max_y)
        if not point_in_polygon(x, y, polygon):
            continue
        road_distance, road_angle, road_width = nearest_road(era_index, x, y)
        if style == "roman":
            width = rng.uniform(0.105, 0.225)
            depth = rng.uniform(0.09, 0.195)
            height = rng.uniform(0.13, 0.3)
        elif style == "medieval":
            width = rng.uniform(0.115, 0.255)
            depth = rng.uniform(0.1, 0.225)
            height = rng.uniform(0.15, 0.36)
        elif style == "royal":
            width = rng.uniform(0.12, 0.27)
            depth = rng.uniform(0.105, 0.235)
            height = rng.uniform(0.18, 0.42)
        else:
            width = rng.uniform(0.125, 0.285)
            depth = rng.uniform(0.11, 0.245)
            height = rng.uniform(0.2, 0.48)
        roof_style, plan_style = building_variant(rng, style, height)
        rotation = road_angle + rng.choice([0.0, math.pi / 2]) + rng.uniform(-0.07, 0.07)
        half_width, half_depth = house_half_extents(width, depth, plan_style)
        footprint_radius = math.hypot(half_width, half_depth)
        road_extent = projected_extent(half_width, half_depth, rotation, road_angle + math.pi / 2)
        if road_distance < road_width * 0.5 + road_extent + 0.008:
            continue
        if polygon_edge_distance(x, y, polygon) < footprint_radius + 0.08:
            continue
        footprint = (x, y, half_width, half_depth, rotation)
        if not can_place_footprint(footprint):
            continue
        register_footprint(footprint)
        wall_id, roof_id = building_material_ids(rng, style)
        bucket = buckets[
            growth_bucket_index(
                x,
                y,
                era_index,
                chunk_count,
                reveal_rng.random(),
            )
        ]
        add_house_geometry(
            bucket["vertices"],
            bucket["faces"],
            bucket["material_ids"],
            x,
            y,
            width,
            depth,
            height,
            rotation,
            wall_id,
            roof_id,
            roof_style,
            plan_style,
            style,
            rng,
        )
        accepted += 1
    print(f"{name}: {accepted}/{count} buildings after {attempts} attempts")
    return finalize_chunked_layer(
        name,
        buckets,
        materials,
        start_frame,
        reveal_frames,
        grow_frames,
        seed=seed,
    )


def create_building_layer(
    name,
    era_index,
    count,
    seed,
    style,
    materials,
    start_frame,
    reveal_frames,
    chunk_count,
    grow_frames,
):
    rng = random.Random(seed)
    reveal_rng = random.Random(seed + 10000)
    buckets = geometry_buckets(chunk_count)
    attempts = 0
    accepted = 0
    polygon = CITY_POLYGONS[era_index]
    min_x = min(point[0] for point in polygon)
    max_x = max(point[0] for point in polygon)
    min_y = min(point[1] for point in polygon)
    max_y = max(point[1] for point in polygon)
    while accepted < count and attempts < count * 80:
        attempts += 1
        x = rng.uniform(min_x, max_x)
        y = rng.uniform(min_y, max_y)
        if not city_contains(era_index, x, y):
            continue
        if era_index >= 3 and is_park(x, y):
            continue
        if point_on_island(x, y):
            continue
        if era_index >= 4 and point_near_modern_rail(x, y, margin=0.34):
            continue
        edge_distance = polygon_edge_distance(x, y, polygon)
        edge_keep_probability = min(1.0, 0.2 + edge_distance / (2.0 + era_index * 0.55))
        if rng.random() > edge_keep_probability:
            continue

        road_distance, road_angle, road_width = nearest_road(era_index, x, y)
        if era_index > 0 and road_distance > (3.4 - era_index * 0.3):
            continue

        if style == "roman":
            rotation = road_angle + rng.choice([0.0, math.pi / 2]) + rng.uniform(-0.04, 0.04)
            width = rng.uniform(0.12, 0.26)
            depth = rng.uniform(0.11, 0.23)
            height = rng.uniform(0.13, 0.3)
        elif style == "medieval":
            rotation = road_angle + rng.choice([0.0, math.pi / 2]) + rng.uniform(-0.14, 0.14)
            width = rng.uniform(0.15, 0.34)
            depth = rng.uniform(0.13, 0.3)
            height = rng.uniform(0.17, 0.43)
        elif style == "royal":
            rotation = road_angle + rng.choice([0.0, math.pi / 2]) + rng.uniform(-0.06, 0.06)
            width = rng.uniform(0.16, 0.38)
            depth = rng.uniform(0.15, 0.32)
            height = rng.uniform(0.21, 0.5)
        elif style == "haussmann":
            rotation = road_angle + rng.choice([0.0, math.pi / 2]) + rng.uniform(-0.035, 0.035)
            width = rng.uniform(0.17, 0.42)
            depth = rng.uniform(0.15, 0.34)
            height = rng.uniform(0.28, 0.64)
        else:
            rotation = road_angle + rng.choice([0.0, math.pi / 2]) + rng.uniform(-0.05, 0.05)
            width = rng.uniform(0.17, 0.46)
            depth = rng.uniform(0.15, 0.37)
            height = rng.uniform(0.27, 0.72)
            if abs(x + 54.0) < 7.0 and abs(y - 29.0) < 8.0 and rng.random() < 0.12:
                height = rng.uniform(1.7, 3.6)

        roof_style, plan_style = building_variant(rng, style, height)
        half_width, half_depth = house_half_extents(width, depth, plan_style)
        footprint_radius = math.hypot(half_width, half_depth)
        road_extent = projected_extent(half_width, half_depth, rotation, road_angle + math.pi / 2)
        if road_distance < road_width * 0.5 + road_extent + 0.018:
            continue
        if is_water(x, y, margin=0.08 + footprint_radius):
            continue
        footprint = (x, y, half_width, half_depth, rotation)
        if not can_place_footprint(footprint):
            continue
        register_footprint(footprint)

        wall_id, roof_id = building_material_ids(rng, style)
        bucket = buckets[
            growth_bucket_index(
                x,
                y,
                era_index,
                chunk_count,
                reveal_rng.random(),
            )
        ]
        add_house_geometry(
            bucket["vertices"],
            bucket["faces"],
            bucket["material_ids"],
            x,
            y,
            width,
            depth,
            height,
            rotation,
            wall_id,
            roof_id,
            roof_style,
            plan_style,
            style,
            rng,
        )
        accepted += 1

    print(f"{name}: {accepted}/{count} buildings after {attempts} attempts")
    return finalize_chunked_layer(
        name,
        buckets,
        materials,
        start_frame,
        reveal_frames,
        grow_frames,
        seed=seed,
    )


def add_road_segment(
    buckets,
    bucket_indexer,
    start,
    end,
    width,
    material_id=0,
    allow_water=False,
    max_piece_length=0.72,
    clip_polygon=None,
):
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length == 0:
        return
    segment_count = max(1, math.ceil(length / max_piece_length))
    for index in range(segment_count):
        t0 = index / segment_count
        t1 = (index + 1) / segment_count
        sx = x1 + dx * t0
        sy = y1 + dy * t0
        ex = x1 + dx * t1
        ey = y1 + dy * t1
        mx = (sx + ex) / 2
        my = (sy + ey) / 2
        if clip_polygon is not None and not point_in_polygon(mx, my, clip_polygon):
            continue
        if not allow_water and is_water(mx, my, margin=0.03):
            continue
        bucket = buckets[bucket_indexer(mx, my)]
        road_z = 0.061 if point_on_island(mx, my) else -0.026
        if allow_water:
            road_z = 0.145
        vertex_start = len(bucket["vertices"])
        add_rect_geometry(
            bucket["vertices"],
            bucket["faces"],
            bucket["material_ids"],
            mx,
            my,
            math.hypot(ex - sx, ey - sy) * 1.05,
            width,
            math.atan2(ey - sy, ex - sx),
            road_z,
            material_id,
        )
        bucket.setdefault("road_ranges", []).append(vertex_start)


def create_road_layer(name, phase, material, start_frame, reveal_frames, chunk_count=30):
    buckets = geometry_buckets(chunk_count)
    reveal_rng = random.Random(7000 + phase)

    def add_segment(start, end, width, bridge=False, max_piece_length=0.72):
        def bucket_indexer(midpoint_x, midpoint_y):
            progress = road_growth_progress(
                midpoint_x,
                midpoint_y,
                phase,
                reveal_rng.random(),
            )
            return min(chunk_count - 1, int(progress * chunk_count))

        add_road_segment(
            buckets,
            bucket_indexer,
            start,
            end,
            width,
            allow_water=bridge,
            max_piece_length=max_piece_length,
            clip_polygon=None if bridge else CITY_POLYGONS[phase],
        )

    if phase == 0:
        for width, points in road_specs_for_phase(phase):
            for start, end in zip(points, points[1:]):
                add_segment(start, end, width, max_piece_length=0.46)
    else:
        segments, _ = build_real_road_index()
        for road_phase, width, start, end, bridge in segments:
            if road_phase != phase:
                continue
            if bridge:
                continue
            add_segment(start, end, width, max_piece_length=1.15)
    road_piece_count = sum(len(bucket["faces"]) for bucket in buckets)
    print(f"{name}: {road_piece_count} road pieces")
    return finalize_chunked_layer(
        name,
        buckets,
        [material],
        start_frame,
        reveal_frames,
        ROAD_GROW_FRAMES[phase],
        road=True,
        seed=7000 + phase,
    )


def add_tree_geometry(
    vertices,
    faces,
    material_ids,
    x,
    y,
    radius,
    height,
    material_id,
    variant="broadleaf",
):
    tree_start = len(vertices)
    trunk_radius = radius * (0.11 if variant == "poplar" else 0.16)
    trunk_height = max(0.06, height * (0.14 if variant == "shrub" else 0.2))
    trunk_start = len(vertices)
    for z in (0.02, trunk_height):
        vertices.extend(
            [
                (x - trunk_radius, y - trunk_radius, z),
                (x + trunk_radius, y - trunk_radius, z),
                (x + trunk_radius, y + trunk_radius, z),
                (x - trunk_radius, y + trunk_radius, z),
            ]
        )
    faces.extend(
        [
            (trunk_start, trunk_start + 1, trunk_start + 5, trunk_start + 4),
            (trunk_start + 1, trunk_start + 2, trunk_start + 6, trunk_start + 5),
            (trunk_start + 2, trunk_start + 3, trunk_start + 7, trunk_start + 6),
            (trunk_start + 3, trunk_start, trunk_start + 4, trunk_start + 7),
            (trunk_start + 4, trunk_start + 5, trunk_start + 6, trunk_start + 7),
        ]
    )
    material_ids.extend([2] * 5)

    sides = 6
    if variant == "conifer":
        rings = [
            (trunk_height * 0.82, radius),
            (height * 0.6, radius * 0.62),
        ]
    elif variant == "round":
        rings = [
            (height * 0.28, radius * 0.62),
            (height * 0.46, radius),
            (height * 0.68, radius * 0.88),
            (height * 0.84, radius * 0.54),
        ]
    elif variant == "poplar":
        rings = [
            (height * 0.24, radius * 0.42),
            (height * 0.54, radius * 0.58),
            (height * 0.78, radius * 0.45),
        ]
    elif variant == "shrub":
        rings = [
            (height * 0.22, radius * 0.8),
            (height * 0.5, radius),
            (height * 0.72, radius * 0.68),
        ]
    else:
        rings = [
            (trunk_height * 0.82, radius * 0.62),
            (height * 0.43, radius),
            (height * 0.74, radius * 0.78),
        ]
    canopy_start = len(vertices)
    for z, ring_radius in rings:
        for index in range(sides):
            angle = 2.0 * math.pi * index / sides
            vertices.append(
                (
                    x + math.cos(angle) * ring_radius,
                    y + math.sin(angle) * ring_radius,
                    z,
                )
            )
    top_index = len(vertices)
    vertices.append((x, y, height))
    faces.append(tuple(canopy_start + index for index in reversed(range(sides))))
    material_ids.append(material_id)
    for ring_index in range(len(rings) - 1):
        lower = canopy_start + ring_index * sides
        upper = lower + sides
        for index in range(sides):
            next_index = (index + 1) % sides
            faces.append((lower + index, lower + next_index, upper + next_index, upper + index))
            material_ids.append(material_id)
    upper = canopy_start + (len(rings) - 1) * sides
    for index in range(sides):
        next_index = (index + 1) % sides
        faces.append((upper + index, upper + next_index, top_index))
        material_ids.append(material_id)
    return tree_start, len(vertices), x, y


def create_forest_layers(materials):
    rng = random.Random(909)
    group_bucket_counts = [120, 140, 160, 180, 200]
    groups = {
        group_id: geometry_buckets(group_bucket_counts[group_id] if group_id < 5 else 1)
        for group_id in range(6)
    }
    accepted = 0
    attempts = 0
    tree_count = FOREST_TREE_COUNT
    while accepted < tree_count and attempts < tree_count * 18:
        attempts += 1
        if rng.random() < 0.44:
            x = rng.gauss(0.0, 22.0)
            y = rng.gauss(0.0, 15.5)
        else:
            x = rng.uniform(-78.0, 78.0)
            y = rng.uniform(-55.0, 55.0)
        if not (-78.0 <= x <= 78.0 and -55.0 <= y <= 55.0):
            continue
        if is_water(x, y, margin=0.1):
            continue
        variant_roll = rng.random()
        if variant_roll < 0.22:
            variant = "conifer"
            radius = rng.uniform(0.12, 0.25)
            height = rng.uniform(0.58, 1.3)
        elif variant_roll < 0.47:
            variant = "broadleaf"
            radius = rng.uniform(0.16, 0.34)
            height = rng.uniform(0.48, 1.12)
        elif variant_roll < 0.68:
            variant = "round"
            radius = rng.uniform(0.18, 0.36)
            height = rng.uniform(0.46, 1.0)
        elif variant_roll < 0.84:
            variant = "poplar"
            radius = rng.uniform(0.11, 0.2)
            height = rng.uniform(0.72, 1.42)
        else:
            variant = "shrub"
            radius = rng.uniform(0.13, 0.28)
            height = rng.uniform(0.26, 0.58)

        overlaps_future_building = not can_place_tree(x, y, radius)
        era = first_urban_era(x, y)
        road_phase = 4 if era is None else era
        road_distance, _road_angle, road_width = nearest_road(road_phase, x, y)
        overlaps_future_road = road_distance < road_width * 0.5 + radius * 0.6
        if era is None and overlaps_future_road:
            continue
        requires_clearance = overlaps_future_building or overlaps_future_road
        keep_urban_tree = (
            era is not None
            and not requires_clearance
            and rng.random() < (0.17 - era * 0.016)
        )
        group_id = 5 if era is None or is_park(x, y) or keep_urban_tree else era
        if group_id == 5:
            bucket = groups[group_id][0]
        else:
            bucket = groups[group_id][
                growth_bucket_index(
                    x,
                    y,
                    group_id,
                    len(groups[group_id]),
                    rng.random(),
                )
            ]
        tree_range = add_tree_geometry(
            bucket["vertices"],
            bucket["faces"],
            bucket["material_ids"],
            x,
            y,
            radius,
            height,
            rng.choices([0, 1, 3, 4], weights=[42, 25, 21, 12], k=1)[0],
            variant=variant,
        )
        bucket.setdefault("tree_ranges", []).append(tree_range)
        accepted += 1

    print(f"Forest: {accepted}/{tree_count} trees after {attempts} attempts")
    for group_id, buckets in groups.items():
        denominator = max(1, len(buckets) - 1)
        for index, bucket in enumerate(buckets):
            if not bucket["vertices"]:
                continue
            if group_id == 5:
                name = "Forest_Persistent"
            else:
                name = f"Forest_Cleared_{group_id}_Chunk_{index:02d}"
            forest = mesh_object(
                name,
                bucket["vertices"],
                bucket["faces"],
                bucket["material_ids"],
                materials,
            )
            if group_id < 5:
                shrink_key = add_tree_shrink_shape(forest, bucket)
                progress = index / denominator
                road_start = PHASE_FRAMES[group_id] - ROAD_LEAD_FRAMES[group_id]
                removal_start = max(
                    road_start,
                    PHASE_FRAMES[group_id]
                    + round(PHASE_REVEAL_FRAMES[group_id] * progress)
                    - 75,
                )
                duration = 66 + round(24 * (0.5 + 0.5 * math.sin(index * 1.73 + group_id)))
                animate_tree_clearance(forest, shrink_key, removal_start, duration)


def set_constant_keyframes(obj, data_path):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    for fcurve in action.fcurves:
        if fcurve.data_path == data_path:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "CONSTANT"


def key_object_visibility(obj, start_frame):
    targets = [obj]
    stack = list(obj.children)
    while stack:
        target = stack.pop()
        targets.append(target)
        stack.extend(target.children)
    for target in targets:
        if start_frame > 1:
            target.hide_render = True
            target.keyframe_insert(data_path="hide_render", frame=1)
            target.keyframe_insert(data_path="hide_render", frame=start_frame - 1)
        target.hide_render = False
        target.keyframe_insert(data_path="hide_render", frame=start_frame)
        set_constant_keyframes(target, "hide_render")


def hide_object_after(obj, frame):
    targets = [obj]
    stack = list(obj.children)
    while stack:
        target = stack.pop()
        targets.append(target)
        stack.extend(target.children)
    for target in targets:
        target.hide_render = False
        target.keyframe_insert(data_path="hide_render", frame=frame)
        target.hide_render = True
        target.keyframe_insert(data_path="hide_render", frame=frame + 1)
        set_constant_keyframes(target, "hide_render")


def set_action_easing(animated_data, data_paths=None, interpolation="BEZIER"):
    if not animated_data or not animated_data.animation_data or not animated_data.animation_data.action:
        return
    for fcurve in animated_data.animation_data.action.fcurves:
        if data_paths is not None and fcurve.data_path not in data_paths:
            continue
        for keyframe in fcurve.keyframe_points:
            keyframe.interpolation = interpolation
            if interpolation == "BEZIER":
                keyframe.handle_left_type = "AUTO_CLAMPED"
                keyframe.handle_right_type = "AUTO_CLAMPED"


def animate_road_draw(obj, shape_key, start_frame, duration):
    key_object_visibility(obj, start_frame)
    if shape_key is None:
        obj.location.z = -0.08
        obj.keyframe_insert(data_path="location", frame=start_frame)
        obj.location.z = 0.0
        obj.keyframe_insert(data_path="location", frame=start_frame + duration)
        set_action_easing(obj, {"location"})
        return
    shape_key.value = 1.0
    shape_key.keyframe_insert(data_path="value", frame=start_frame)
    shape_key.value = 0.0
    shape_key.keyframe_insert(data_path="value", frame=start_frame + duration)
    set_action_easing(obj.data.shape_keys, {f'key_blocks["{shape_key.name}"].value'})


def animate_axis_growth(obj, start_frame, duration, axis="Y"):
    key_object_visibility(obj, start_frame)
    final_scale = tuple(obj.scale)
    start_scale = list(final_scale)
    axis_index = {"X": 0, "Y": 1, "Z": 2}[axis]
    start_scale[axis_index] = max(0.01, final_scale[axis_index] * 0.015)
    obj.scale = start_scale
    obj.keyframe_insert(data_path="scale", frame=start_frame)
    obj.scale = final_scale
    obj.keyframe_insert(data_path="scale", frame=start_frame + duration)
    set_action_easing(obj, {"scale"})


def add_tree_shrink_shape(obj, bucket):
    ranges = bucket.get("tree_ranges", ())
    if not ranges:
        return None
    obj.shape_key_add(name="Basis")
    shrink = obj.shape_key_add(name="Tree_Shrink")
    for vertex_start, vertex_end, center_x, center_y in ranges:
        for vertex_index in range(vertex_start, vertex_end):
            shrink.data[vertex_index].co = (center_x, center_y, 0.022)
    return shrink


def animate_tree_clearance(obj, shrink_key, start_frame, duration):
    if shrink_key is None:
        animate_removal(obj, start_frame, duration)
        return
    shrink_key.value = 0.0
    shrink_key.keyframe_insert(data_path="value", frame=start_frame)
    shrink_key.value = 1.0
    shrink_key.keyframe_insert(data_path="value", frame=start_frame + duration)
    set_action_easing(obj.data.shape_keys, {f'key_blocks["{shrink_key.name}"].value'})
    hide_object_after(obj, start_frame + duration)


def animate_building_sprout(obj, start_frame, duration):
    key_object_visibility(obj, start_frame)
    final_location = tuple(obj.location)
    final_scale = tuple(obj.scale)
    peak_frame = start_frame + max(3, duration - 2)

    obj.location = (final_location[0], final_location[1], final_location[2] - 0.14)
    obj.scale = (final_scale[0], final_scale[1], max(0.001, final_scale[2] * 0.012))
    obj.keyframe_insert(data_path="location", frame=start_frame)
    obj.keyframe_insert(data_path="scale", frame=start_frame)

    obj.location = (final_location[0], final_location[1], final_location[2] + 0.012)
    obj.scale = (final_scale[0], final_scale[1], final_scale[2] * 1.065)
    obj.keyframe_insert(data_path="location", frame=peak_frame)
    obj.keyframe_insert(data_path="scale", frame=peak_frame)

    obj.location = final_location
    obj.scale = final_scale
    obj.keyframe_insert(data_path="location", frame=start_frame + duration)
    obj.keyframe_insert(data_path="scale", frame=start_frame + duration)

    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path not in {"scale", "location"}:
                continue
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "QUAD"
                keyframe.easing = "EASE_OUT"


def animate_layer(obj, start_frame, road=False, duration=44):
    final_location = tuple(obj.location)
    final_scale = tuple(obj.scale)
    visibility_targets = [obj]
    stack = list(obj.children)
    while stack:
        target = stack.pop()
        visibility_targets.append(target)
        stack.extend(target.children)
    for target in visibility_targets:
        if start_frame > 1:
            target.hide_render = True
            target.keyframe_insert(data_path="hide_render", frame=1)
            target.keyframe_insert(data_path="hide_render", frame=start_frame - 1)
        target.hide_render = False
        target.keyframe_insert(data_path="hide_render", frame=start_frame)
        set_constant_keyframes(target, "hide_render")

    if road:
        obj.location = (final_location[0], final_location[1], final_location[2] - 0.12)
        obj.keyframe_insert(data_path="location", frame=start_frame)
        obj.location = final_location
        obj.keyframe_insert(data_path="location", frame=start_frame + duration)
    else:
        obj.location = (final_location[0], final_location[1], final_location[2] - 0.2)
        obj.keyframe_insert(data_path="location", frame=start_frame)
        obj.scale = (final_scale[0], final_scale[1], max(0.001, final_scale[2] * 0.015))
        obj.keyframe_insert(data_path="scale", frame=start_frame)
        obj.location = final_location
        obj.keyframe_insert(data_path="location", frame=start_frame + duration)
        obj.scale = final_scale
        obj.keyframe_insert(data_path="scale", frame=start_frame + duration)

    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path in {"scale", "location"}:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = "SINE"
                    keyframe.easing = "EASE_IN_OUT"


def animate_removal(obj, end_frame, duration=40):
    obj.location.z = 0.0
    obj.keyframe_insert(data_path="location", frame=end_frame)
    obj.scale = (1.0, 1.0, 1.0)
    obj.keyframe_insert(data_path="scale", frame=end_frame)
    obj.location.z = -0.2
    obj.keyframe_insert(data_path="location", frame=end_frame + duration)
    obj.scale = (1.0, 1.0, 0.02)
    obj.keyframe_insert(data_path="scale", frame=end_frame + duration)
    targets = [obj]
    stack = list(obj.children)
    while stack:
        target = stack.pop()
        targets.append(target)
        stack.extend(target.children)
    for target in targets:
        target.hide_render = False
        target.keyframe_insert(data_path="hide_render", frame=end_frame + duration)
        target.hide_render = True
        target.keyframe_insert(data_path="hide_render", frame=end_frame + duration + 1)
        set_constant_keyframes(target, "hide_render")
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path in {"scale", "location"}:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = "SINE"
                    keyframe.easing = "EASE_IN_OUT"


def animate_progressive_removal(
    root,
    start_frame,
    spread_frames=72,
    duration=64,
    road=False,
    reverse=False,
):
    chunks = sorted(root.children, key=lambda child: child.name, reverse=reverse)
    if not chunks:
        if road:
            animate_road_removal(root, start_frame, duration=duration)
        else:
            animate_removal(root, start_frame, duration=duration)
        return
    timing_rng = random.Random(len(chunks) * 43 + start_frame * 17)
    denominator = max(1, len(chunks) - 1)
    for index, chunk in enumerate(chunks):
        if road:
            chunk_start = start_frame + round(spread_frames * index / denominator)
            animate_road_removal(chunk, chunk_start, duration=duration)
        else:
            chunk_start = batched_stagger_frame(
                index,
                len(chunks),
                start_frame,
                spread_frames,
                timing_rng,
            )
            animate_removal(chunk, chunk_start, duration=duration)


def animate_road_removal(obj, end_frame, duration=38):
    obj.location.z = 0.0
    obj.keyframe_insert(data_path="location", frame=end_frame)
    obj.location.z = -0.16
    obj.keyframe_insert(data_path="location", frame=end_frame + duration)
    targets = [obj, *list(obj.children)]
    for target in targets:
        target.hide_render = False
        target.keyframe_insert(data_path="hide_render", frame=end_frame + duration)
        target.hide_render = True
        target.keyframe_insert(data_path="hide_render", frame=end_frame + duration + 1)
        set_constant_keyframes(target, "hide_render")
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path == "location":
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = "SINE"
                    keyframe.easing = "EASE_IN_OUT"


def add_cube(name, location, scale, material, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def add_mansard_roof(name, location, width, depth, height, material, parent=None):
    x, y, base_z = location
    inset_x = width * 0.34
    inset_y = depth * 0.34
    vertices = [
        (x - width * 0.5, y - depth * 0.5, base_z),
        (x + width * 0.5, y - depth * 0.5, base_z),
        (x + width * 0.5, y + depth * 0.5, base_z),
        (x - width * 0.5, y + depth * 0.5, base_z),
        (x - inset_x, y - inset_y, base_z + height),
        (x + inset_x, y - inset_y, base_z + height),
        (x + inset_x, y + inset_y, base_z + height),
        (x - inset_x, y + inset_y, base_z + height),
    ]
    faces = [
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
        (4, 5, 6, 7),
    ]
    roof = mesh_object(name, vertices, faces, [0] * len(faces), [material])
    if parent:
        roof.parent = parent
    return roof


def add_gable_roof(name, location, length, width, height, material, parent=None, rotation=0.0):
    x, y, base_z = location
    local = [
        (-length * 0.5, -width * 0.5, base_z),
        (length * 0.5, -width * 0.5, base_z),
        (length * 0.5, width * 0.5, base_z),
        (-length * 0.5, width * 0.5, base_z),
        (-length * 0.5, 0.0, base_z + height),
        (length * 0.5, 0.0, base_z + height),
    ]
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    vertices = [
        (x + lx * cos_r - ly * sin_r, y + lx * sin_r + ly * cos_r, lz)
        for lx, ly, lz in local
    ]
    faces = [
        (0, 1, 5, 4),
        (3, 4, 5, 2),
        (0, 4, 3),
        (1, 2, 5),
    ]
    roof = mesh_object(name, vertices, faces, [0] * len(faces), [material])
    if parent:
        roof.parent = parent
    return roof


def add_cylinder(name, location, radius, depth, material, parent=None, vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def add_cone(name, location, radius1, radius2, depth, material, parent=None, vertices=12):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def add_torus(
    name,
    location,
    major_radius,
    minor_radius,
    scale,
    material,
    parent=None,
    major_segments=40,
    minor_segments=8,
):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=major_segments,
        minor_segments=minor_segments,
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def add_arch_ring(
    name,
    location,
    inner_radius,
    outer_radius,
    depth,
    material,
    parent=None,
    segments=28,
):
    x, y, z = location
    vertices = []
    for depth_side in (-0.5, 0.5):
        for index in range(segments + 1):
            angle = math.pi * index / segments
            for radius in (outer_radius, inner_radius):
                vertices.append(
                    (
                        x + math.cos(angle) * radius,
                        y + depth_side * depth,
                        z + math.sin(angle) * radius,
                    )
                )
    stride = (segments + 1) * 2
    faces = []
    for index in range(segments):
        front = index * 2
        back = stride + front
        faces.extend(
            [
                (front, front + 2, front + 3, front + 1),
                (back + 1, back + 3, back + 2, back),
                (front, back, back + 2, front + 2),
                (front + 3, back + 3, back + 1, front + 1),
            ]
        )
    faces.extend(
        [
            (0, 1, stride + 1, stride),
            (segments * 2, stride + segments * 2, stride + segments * 2 + 1, segments * 2 + 1),
        ]
    )
    arch = mesh_object(name, vertices, faces, [0] * len(faces), [material])
    if parent:
        arch.parent = parent
    return arch


def add_beam(name, start, end, radius, material, parent=None):
    start_v = Vector(start)
    end_v = Vector(end)
    delta = end_v - start_v
    midpoint = (start_v + end_v) / 2
    obj = add_cylinder(name, midpoint, radius, delta.length, material, parent=parent, vertices=8)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return obj


def new_landmark_root(name, location=(0.0, 0.0, 0.0), rotation=0.0):
    root = bpy.data.objects.new(name, None)
    root.empty_display_type = "PLAIN_AXES"
    root.location = location
    root.rotation_euler[2] = rotation
    bpy.context.collection.objects.link(root)
    return root


def build_roman_theatre(stone_material, roof_material, arena_material, recess_material):
    root = new_landmark_root("Landmark_Roman_Theatre")
    x, y = 6.4, 6.25
    model_scale = 0.74

    arena = add_cylinder("Roman_Theatre_Arena", (x, y, 0.045), 1.0, 0.07, arena_material, root, 40)
    arena.scale = (1.25 * model_scale, 0.72 * model_scale, 1.0)
    bpy.context.view_layer.objects.active = arena
    arena.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    add_torus(
        "Roman_Theatre_Lower_Seats",
        (x, y, 0.13),
        0.78 * model_scale,
        0.16 * model_scale,
        (1.55, 1.0, 0.48),
        stone_material,
        root,
    )
    add_torus(
        "Roman_Theatre_Upper_Seats",
        (x, y, 0.27),
        0.98 * model_scale,
        0.14 * model_scale,
        (1.55, 1.0, 0.7),
        stone_material,
        root,
    )
    add_torus(
        "Roman_Theatre_Outer_Wall",
        (x, y, 0.35),
        1.12 * model_scale,
        0.115 * model_scale,
        (1.55, 1.0, 1.3),
        stone_material,
        root,
        major_segments=48,
    )

    add_cube(
        "Roman_Theatre_Stage",
        (x, y + 0.95 * model_scale, 0.23),
        (2.75 * model_scale, 0.46 * model_scale, 0.46),
        stone_material,
        root,
    )
    add_mansard_roof(
        "Roman_Theatre_Stage_Roof",
        (x, y + 0.95 * model_scale, 0.46),
        2.15,
        0.36,
        0.16,
        roof_material,
        root,
    )
    for index in range(9):
        column_x = x + (-1.12 + index * 0.28) * model_scale
        add_cylinder(
            f"Roman_Theatre_Column_{index:02d}",
            (column_x, y + 0.69 * model_scale, 0.265),
            0.032,
            0.43,
            stone_material,
            root,
            8,
        )
    for index in range(14):
        angle = 2.0 * math.pi * index / 14.0
        arch_x = x + math.cos(angle) * 1.73 * model_scale
        arch_y = y + math.sin(angle) * 1.11 * model_scale
        recess = add_cube(
            f"Roman_Theatre_Arch_{index:02d}",
            (arch_x, arch_y, 0.27),
            (0.12, 0.028, 0.17),
            recess_material,
            root,
        )
        recess.rotation_euler[2] = angle + math.pi / 2

    animate_layer(root, PHASE_FRAMES[0] + 45, duration=220)
    animate_removal(root, PHASE_FRAMES[1] + 180, duration=240)
    return root


def build_roman_forum(stone_material, roof_material, courtyard_material, recess_material):
    x, y = 1.4, -8.5
    assert_landmark_on_land("Roman Forum", x, y, 1.45, 1.02)
    root = new_landmark_root("Landmark_Roman_Forum", (x, y, 0.0))

    add_cube("Roman_Forum_Plaza", (0.0, 0.0, 0.035), (2.55, 1.68, 0.07), courtyard_material, root)
    for side, suffix in ((-1.0, "South"), (1.0, "North")):
        stoa_y = side * 0.7
        add_cube(f"Roman_Forum_{suffix}_Stoa", (0.0, stoa_y, 0.22), (2.45, 0.22, 0.38), stone_material, root)
        add_gable_roof(
            f"Roman_Forum_{suffix}_Roof",
            (0.0, stoa_y, 0.41),
            2.5,
            0.3,
            0.12,
            roof_material,
            root,
        )
        for index in range(10):
            column_x = -1.05 + index * (2.1 / 9)
            add_cylinder(
                f"Roman_Forum_{suffix}_Column_{index:02d}",
                (column_x, side * 0.53, 0.2),
                0.032,
                0.34,
                stone_material,
                root,
                10,
            )
            add_cube(
                f"Roman_Forum_{suffix}_Column_Cap_{index:02d}",
                (column_x, side * 0.53, 0.385),
                (0.085, 0.085, 0.04),
                stone_material,
                root,
            )

    add_cube("Roman_Forum_West_Basilica", (-1.12, 0.0, 0.25), (0.28, 1.25, 0.5), stone_material, root)
    add_gable_roof("Roman_Forum_West_Roof", (-1.12, 0.0, 0.5), 1.25, 0.34, 0.16, roof_material, root, math.pi / 2)
    for index, doorway_y in enumerate((-0.38, 0.0, 0.38)):
        add_cube(
            f"Roman_Forum_West_Door_{index:02d}",
            (-1.27, doorway_y, 0.19),
            (0.025, 0.13, 0.24),
            recess_material,
            root,
        )

    temple_x = 0.86
    for index, (width, depth, z) in enumerate(((0.9, 1.08, 0.07), (0.78, 0.96, 0.12), (0.68, 0.84, 0.17))):
        add_cube(f"Roman_Forum_Temple_Step_{index:02d}", (temple_x, 0.0, z), (width, depth, 0.1), stone_material, root)
    add_cube("Roman_Forum_Temple_Cella", (temple_x + 0.1, 0.14, 0.46), (0.48, 0.58, 0.58), stone_material, root)
    add_gable_roof("Roman_Forum_Temple_Roof", (temple_x + 0.02, 0.08, 0.75), 0.72, 0.82, 0.22, roof_material, root, math.pi / 2)
    for column_index, column_y in enumerate((-0.28, 0.0, 0.28)):
        add_cylinder(
            f"Roman_Forum_Temple_Portico_{column_index:02d}",
            (temple_x - 0.28, column_y, 0.47),
            0.045,
            0.55,
            stone_material,
            root,
            10,
        )
    add_cube("Roman_Forum_Temple_Door", (temple_x - 0.145, 0.14, 0.48), (0.022, 0.16, 0.3), recess_material, root)
    add_cube("Roman_Forum_Altar", (0.0, 0.0, 0.15), (0.28, 0.22, 0.23), stone_material, root)
    for index, market_x in enumerate((-0.62, -0.28, 0.08)):
        add_cube(f"Roman_Forum_Stall_{index:02d}", (market_x, -0.22, 0.16), (0.22, 0.18, 0.26), stone_material, root)
        add_gable_roof(
            f"Roman_Forum_Stall_Roof_{index:02d}",
            (market_x, -0.22, 0.29),
            0.25,
            0.22,
            0.09,
            roof_material,
            root,
        )

    animate_layer(root, PHASE_FRAMES[0] + 20, duration=210)
    animate_removal(root, PHASE_FRAMES[1] + 210, duration=240)
    return root


def build_medieval_island_wall(material, roof_material, polygon):
    root = new_landmark_root("Landmark_Medieval_Cite_Wall")
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        wall = add_cube(
            f"Cite_Wall_{index:02d}",
            ((start[0] + end[0]) * 0.5, (start[1] + end[1]) * 0.5, 0.2),
            (length + 0.04, 0.1, 0.29),
            material,
            root,
        )
        wall.rotation_euler[2] = math.atan2(dy, dx)
        if index % 4 == 0:
            add_cylinder(
                f"Cite_Wall_Tower_{index:02d}",
                (start[0], start[1], 0.27),
                0.15,
                0.48,
                material,
                root,
                10,
            )
            add_cone(
                f"Cite_Wall_Tower_Roof_{index:02d}",
                (start[0], start[1], 0.58),
                0.19,
                0.0,
                0.2,
                roof_material,
                root,
                10,
            )
    animate_layer(root, PHASE_FRAMES[1] + 50, duration=220)
    animate_removal(root, PHASE_FRAMES[2] + 180, duration=240)
    return root


def build_notre_dame(material, roof_material, window_material):
    x, y, rotation = 0.15, 0.25, -0.55
    assert_landmark_on_land("Notre-Dame", x, y, 1.15, 0.7, rotation)
    root = new_landmark_root("Landmark_Notre_Dame", (x, y, 0.0), rotation)
    if not NOTRE_DAME_GLB_PATH.exists():
        raise FileNotFoundError(f"Notre-Dame GLB not found: {NOTRE_DAME_GLB_PATH}")

    objects_before_import = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(NOTRE_DAME_GLB_PATH))
    imported_objects = [obj for obj in bpy.data.objects if obj not in objects_before_import]
    cathedral_meshes = [
        obj
        for obj in imported_objects
        if obj.type == "MESH" and len(obj.data.polygons) > 1000
    ]
    if len(cathedral_meshes) != 1:
        raise RuntimeError(
            f"Expected one detailed Notre-Dame mesh, found {len(cathedral_meshes)}"
        )

    cathedral = cathedral_meshes[0]
    cathedral.parent = root
    cathedral.name = "Notre_Dame_GLTF_Detailed"
    cathedral.location = (0.0, 0.0, 0.82)
    cathedral.rotation_euler = (0.0, 0.0, 0.0)
    cathedral.scale = (2.05, 1.42, 2.35)

    for imported in imported_objects:
        if imported != cathedral:
            bpy.data.objects.remove(imported, do_unlink=True)

    for imported_material in cathedral.data.materials:
        if imported_material:
            imported_material.name = f"Notre_Dame_{imported_material.name}"

    animate_layer(root, PHASE_FRAMES[1] + 120, duration=300)
    return root


def add_louvre_window_row(root, prefix, axis, fixed, start, end, count, z, window_material):
    for index in range(count):
        amount = index / max(1, count - 1)
        moving = start + (end - start) * amount
        if axis == "x":
            location = (moving, fixed, z)
            dimensions = (0.105, 0.022, 0.105)
        else:
            location = (fixed, moving, z)
            dimensions = (0.022, 0.105, 0.105)
        add_cube(f"{prefix}_{index:02d}", location, dimensions, window_material, root)


def build_louvre(material, roof_material, courtyard_material, window_material):
    root = new_landmark_root("Landmark_Louvre")
    x, river_side_y = -10.8, 10.7
    courtyard_y = 11.9

    add_cube("Louvre_Courtyard", (x, courtyard_y, 0.068), (2.5, 1.72, 0.026), courtyard_material, root)
    add_cube("Louvre_River_Wing", (x, river_side_y, 0.25), (3.75, 0.68, 0.5), material, root)
    add_mansard_roof("Louvre_River_Roof", (x, river_side_y, 0.5), 3.65, 0.66, 0.24, roof_material, root)
    add_cube("Louvre_River_Cornice", (x, river_side_y - 0.35, 0.49), (3.82, 0.045, 0.055), material, root)
    add_louvre_window_row(root, "Louvre_River_Lower_Window", "x", river_side_y - 0.348, x - 1.68, x + 1.68, 13, 0.16, window_material)
    add_louvre_window_row(root, "Louvre_River_Upper_Window", "x", river_side_y - 0.35, x - 1.68, x + 1.68, 13, 0.36, window_material)
    for index in range(7):
        pilaster_x = x - 1.72 + index * (3.44 / 6)
        add_cube(
            f"Louvre_River_Pilaster_{index:02d}",
            (pilaster_x, river_side_y - 0.37, 0.25),
            (0.045, 0.045, 0.5),
            material,
            root,
        )
    for index in range(9):
        dormer_x = x - 1.48 + index * (2.96 / 8)
        add_cube(
            f"Louvre_River_Dormer_{index:02d}",
            (dormer_x, river_side_y - 0.2, 0.68),
            (0.12, 0.105, 0.15),
            material,
            root,
        )
        dormer_roof = add_cone(
            f"Louvre_River_Dormer_Roof_{index:02d}",
            (dormer_x, river_side_y - 0.2, 0.79),
            0.09,
            0.0,
            0.09,
            roof_material,
            root,
            4,
        )
        dormer_roof.rotation_euler[2] = math.pi / 4

    for side, suffix in [(-1.0, "West"), (1.0, "East")]:
        wing_x = x + side * 1.55
        add_cube(f"Louvre_{suffix}_Wing", (wing_x, 11.82, 0.24), (0.68, 2.58, 0.48), material, root)
        add_mansard_roof(f"Louvre_{suffix}_Roof", (wing_x, 11.82, 0.48), 0.66, 2.5, 0.23, roof_material, root)
        outer_x = wing_x + side * 0.35
        add_cube(f"Louvre_{suffix}_Cornice", (outer_x, 11.82, 0.47), (0.045, 2.62, 0.05), material, root)
        add_louvre_window_row(root, f"Louvre_{suffix}_Lower_Window", "y", outer_x, 10.82, 12.82, 8, 0.15, window_material)
        add_louvre_window_row(root, f"Louvre_{suffix}_Upper_Window", "y", outer_x, 10.82, 12.82, 8, 0.34, window_material)
        for index in range(5):
            pilaster_y = 10.7 + index * 0.55
            add_cube(
                f"Louvre_{suffix}_Pilaster_{index:02d}",
                (outer_x + side * 0.018, pilaster_y, 0.24),
                (0.045, 0.045, 0.48),
                material,
                root,
            )
        for index in range(5):
            dormer_y = 10.98 + index * 0.42
            add_cube(
                f"Louvre_{suffix}_Dormer_{index:02d}",
                (wing_x + side * 0.18, dormer_y, 0.65),
                (0.105, 0.12, 0.14),
                material,
                root,
            )
        add_cube(f"Louvre_{suffix}_Pavilion", (wing_x, 13.02, 0.34), (0.86, 0.86, 0.68), material, root)
        pavilion_roof = add_cone(
            f"Louvre_{suffix}_Pavilion_Roof",
            (wing_x, 13.02, 0.82),
            0.62,
            0.08,
            0.34,
            roof_material,
            root,
            4,
        )
        pavilion_roof.rotation_euler[2] = math.pi / 4
        add_louvre_window_row(root, f"Louvre_{suffix}_Pavilion_Window", "x", 12.585, wing_x - 0.24, wing_x + 0.24, 3, 0.34, window_material)

    add_cube("Louvre_Central_Pavilion", (x, river_side_y, 0.39), (0.92, 0.88, 0.78), material, root)
    central_roof = add_cone(
        "Louvre_Central_Pavilion_Roof",
        (x, river_side_y, 0.94),
        0.66,
        0.08,
        0.4,
        roof_material,
        root,
        4,
    )
    central_roof.rotation_euler[2] = math.pi / 4
    add_cone("Louvre_Central_Finial", (x, river_side_y, 1.22), 0.045, 0.0, 0.24, roof_material, root, 8)
    add_cube("Louvre_Central_Portal", (x, river_side_y - 0.455, 0.16), (0.22, 0.028, 0.3), window_material, root)
    for side in (-1.0, 1.0):
        add_cube(
            f"Louvre_Central_Portal_Column_{int(side)}",
            (x + side * 0.15, river_side_y - 0.47, 0.21),
            (0.055, 0.055, 0.42),
            material,
            root,
        )
    for index, chimney_x in enumerate((x - 1.25, x - 0.72, x + 0.72, x + 1.25)):
        add_cube(
            f"Louvre_Chimney_{index:02d}",
            (chimney_x, river_side_y + 0.08, 0.78),
            (0.075, 0.075, 0.24),
            material,
            root,
        )
    animate_layer(root, PHASE_FRAMES[2] + 80, duration=280)


def build_arc(material, recess_material):
    x, y = -40.2, 23.2
    assert_landmark_on_land("Arc de Triomphe", x, y, 0.62, 0.48)
    root = new_landmark_root("Landmark_Arc_de_Triomphe", (x, y, 0.0))
    add_cube("Arc_Base", (0.0, 0.0, 0.06), (0.92, 0.68, 0.12), material, root)
    add_cube("Arc_Left_Pier", (-0.29, 0.0, 0.48), (0.25, 0.52, 0.84), material, root)
    add_cube("Arc_Right_Pier", (0.29, 0.0, 0.48), (0.25, 0.52, 0.84), material, root)
    add_cube("Arc_Opening_Shadow", (0.0, -0.271, 0.37), (0.31, 0.025, 0.5), recess_material, root)
    add_arch_ring(
        "Arc_Main_Arch_Ring",
        (0.0, -0.287, 0.56),
        0.148,
        0.252,
        0.08,
        material,
        root,
        segments=32,
    )
    add_cube("Arc_Spandrel", (0.0, 0.0, 0.83), (0.82, 0.52, 0.3), material, root)
    add_cube("Arc_Lower_Cornice", (0.0, 0.0, 0.94), (0.93, 0.62, 0.08), material, root)
    add_cube("Arc_Attic", (0.0, 0.0, 1.08), (0.82, 0.52, 0.24), material, root)
    add_cube("Arc_Upper_Cornice", (0.0, 0.0, 1.22), (0.94, 0.62, 0.08), material, root)
    for face_side, face_suffix in ((-1.0, "Front"), (1.0, "Back")):
        face_y = face_side * 0.275
        for index, column_x in enumerate((-0.39, -0.2, 0.2, 0.39)):
            add_cylinder(
                f"Arc_{face_suffix}_Column_{index:02d}",
                (column_x, face_y, 0.48),
                0.04,
                0.72,
                material,
                root,
                12,
            )
        for index, panel_x in enumerate((-0.29, 0.29)):
            add_cube(
                f"Arc_{face_suffix}_Relief_{index:02d}",
                (panel_x, face_y + face_side * 0.012, 0.56),
                (0.15, 0.025, 0.26),
                recess_material,
                root,
            )
        add_cube(
            f"Arc_{face_suffix}_Inscription",
            (0.0, face_y + face_side * 0.014, 1.08),
            (0.56, 0.025, 0.075),
            recess_material,
            root,
        )
    add_cube("Arc_Keystone", (0.0, -0.31, 0.78), (0.09, 0.07, 0.14), material, root)
    animate_layer(root, PHASE_FRAMES[3] + 60, duration=240)
    return root


def populate_eiffel(root, iron_material, detail_material=None):
    detail_material = detail_material or iron_material
    corner_signs = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
    level_specs = [
        (0.05, 0.84),
        (0.42, 0.78),
        (0.82, 0.69),
        (1.28, 0.56),
        (1.72, 0.45),
        (2.56, 0.3),
        (3.35, 0.23),
        (4.25, 0.17),
        (5.2, 0.115),
        (6.15, 0.068),
    ]
    level_points = [
        [(sx * half_width, sy * half_width, z) for sx, sy in corner_signs]
        for z, half_width in level_specs
    ]
    face_pairs = ((0, 1), (1, 2), (2, 3), (3, 0))
    for level_index, points in enumerate(level_points):
        radius = max(0.009, 0.027 - level_index * 0.002)
        for face_index, (first, second) in enumerate(face_pairs):
            add_beam(
                f"Eiffel_Level_{level_index:02d}_Rail_{face_index:02d}",
                points[first],
                points[second],
                radius,
                iron_material,
                root,
            )
    for bay_index, (lower_points, upper_points) in enumerate(zip(level_points, level_points[1:])):
        leg_radius = max(0.019, 0.055 - bay_index * 0.0042)
        secondary_radius = max(0.011, leg_radius * 0.56)
        lower_half_width = level_specs[bay_index][1]
        upper_half_width = level_specs[bay_index + 1][1]
        lower_inset = min(0.075, lower_half_width * 0.14)
        upper_inset = min(0.075, upper_half_width * 0.14)
        for corner_index in range(4):
            sx, sy = corner_signs[corner_index]
            add_beam(
                f"Eiffel_Bay_{bay_index:02d}_Leg_{corner_index:02d}",
                lower_points[corner_index],
                upper_points[corner_index],
                leg_radius,
                iron_material,
                root,
            )
            add_beam(
                f"Eiffel_Bay_{bay_index:02d}_Leg_XRail_{corner_index:02d}",
                (sx * lower_half_width, sy * (lower_half_width - lower_inset), level_specs[bay_index][0]),
                (sx * upper_half_width, sy * (upper_half_width - upper_inset), level_specs[bay_index + 1][0]),
                secondary_radius,
                iron_material,
                root,
            )
            add_beam(
                f"Eiffel_Bay_{bay_index:02d}_Leg_YRail_{corner_index:02d}",
                (sx * (lower_half_width - lower_inset), sy * lower_half_width, level_specs[bay_index][0]),
                (sx * (upper_half_width - upper_inset), sy * upper_half_width, level_specs[bay_index + 1][0]),
                secondary_radius,
                iron_material,
                root,
            )
        if level_specs[bay_index + 1][0] > 1.28:
            brace_radius = max(0.006, 0.013 - bay_index * 0.0008)
            for face_index, (first, second) in enumerate(face_pairs):
                add_beam(
                    f"Eiffel_Bay_{bay_index:02d}_Brace_A_{face_index:02d}",
                    lower_points[first],
                    upper_points[second],
                    brace_radius,
                    detail_material,
                    root,
                )
                add_beam(
                    f"Eiffel_Bay_{bay_index:02d}_Brace_B_{face_index:02d}",
                    lower_points[second],
                    upper_points[first],
                    brace_radius,
                    detail_material,
                    root,
                )

    base_points = level_points[0]
    for face_index, (first, second) in enumerate(face_pairs):
        first_point = base_points[first]
        second_point = base_points[second]
        arch_points = []
        for segment_index in range(17):
            amount = segment_index / 16.0
            arch_points.append(
                (
                    first_point[0] + (second_point[0] - first_point[0]) * amount,
                    first_point[1] + (second_point[1] - first_point[1]) * amount,
                    0.22 + 0.96 * (1.0 - (2.0 * amount - 1.0) ** 2),
                )
            )
        for segment_index, (start, end) in enumerate(zip(arch_points, arch_points[1:])):
            add_beam(
                f"Eiffel_Base_Arch_{face_index:02d}_{segment_index:02d}",
                start,
                end,
                0.036,
                detail_material,
                root,
            )

    platforms = ((1.3, 1.34, 0.034), (2.58, 0.66, 0.025), (6.12, 0.21, 0.014))
    for platform_index, (z, width, deck_radius) in enumerate(platforms):
        deck_corners = [
            (-width * 0.5, -width * 0.5, z),
            (width * 0.5, -width * 0.5, z),
            (width * 0.5, width * 0.5, z),
            (-width * 0.5, width * 0.5, z),
        ]
        for rail_index, (first, second) in enumerate(face_pairs):
            add_beam(
                f"Eiffel_Platform_{platform_index:02d}_Deck_{rail_index:02d}",
                deck_corners[first],
                deck_corners[second],
                deck_radius,
                iron_material,
                root,
            )
        railing_z = z + 0.075
        railing_corners = [
            (-width * 0.5, -width * 0.5, railing_z),
            (width * 0.5, -width * 0.5, railing_z),
            (width * 0.5, width * 0.5, railing_z),
            (-width * 0.5, width * 0.5, railing_z),
        ]
        for rail_index, (first, second) in enumerate(face_pairs):
            add_beam(
                f"Eiffel_Platform_{platform_index:02d}_Railing_{rail_index:02d}",
                railing_corners[first],
                railing_corners[second],
                0.012,
                detail_material,
                root,
            )
    add_cube("Eiffel_Observation_Cabin", (0.0, 0.0, 6.25), (0.22, 0.22, 0.2), iron_material, root)
    add_cylinder("Eiffel_Antenna", (0.0, 0.0, 6.78), 0.024, 0.94, iron_material, root, 10)
    add_cone("Eiffel_Antenna_Tip", (0.0, 0.0, 7.31), 0.032, 0.0, 0.16, detail_material, root, 10)


def build_eiffel(iron_material, detail_material=None):
    x, y = -40.6, 6.0
    assert_landmark_on_land("Eiffel Tower", x, y, 1.0, 0.82)
    root = new_landmark_root("Landmark_Eiffel_Tower", (x, y, 0.0))
    populate_eiffel(root, iron_material, detail_material)
    animate_layer(root, PHASE_FRAMES[4] + 80, duration=300)
    return root


def build_champ_de_mars(path_material, tree_materials):
    root = new_landmark_root("Landmark_Champ_de_Mars", (-40.6, 6.0, 0.0))
    add_cube("Champ_Central_Axis", (0.0, -2.55, 0.066), (0.16, 6.9, 0.018), path_material, root)
    for side, suffix in ((-1.0, "West"), (1.0, "East")):
        add_cube(
            f"Champ_{suffix}_Promenade",
            (side * 1.72, -2.55, 0.066),
            (0.14, 6.9, 0.018),
            path_material,
            root,
        )
    for index, cross_y in enumerate((-5.65, -4.1, -2.55, -1.0, 0.7)):
        add_cube(
            f"Champ_Cross_Path_{index:02d}",
            (0.0, cross_y, 0.067),
            (3.65, 0.13, 0.02),
            path_material,
            root,
        )
    plaza = add_torus(
        "Champ_Eiffel_Plaza",
        (0.0, 0.0, 0.073),
        1.12,
        0.095,
        (1.0, 0.78, 0.18),
        path_material,
        root,
        major_segments=48,
        minor_segments=8,
    )
    plaza.rotation_euler[2] = 0.0

    vertices = []
    faces = []
    material_ids = []
    rng = random.Random(1889)
    for row_index, row_x in enumerate((-1.95, -1.48, 1.48, 1.95)):
        for tree_index in range(13):
            tree_y = -5.95 + tree_index * 0.52
            if math.hypot(row_x, tree_y) < 1.2:
                continue
            add_tree_geometry(
                vertices,
                faces,
                material_ids,
                row_x + rng.uniform(-0.055, 0.055),
                tree_y + rng.uniform(-0.04, 0.04),
                rng.uniform(0.14, 0.22),
                rng.uniform(0.55, 0.86),
                0 if (row_index + tree_index) % 3 else 1,
                variant="poplar",
            )
    tree_rows = mesh_object("Champ_Formal_Tree_Rows", vertices, faces, material_ids, tree_materials)
    tree_rows.parent = root
    animate_layer(root, PHASE_FRAMES[4] - 60, duration=240)
    return root


def build_la_defense(material, glass_material, window_material):
    x, y = -45.0, 28.5
    assert_landmark_on_land("La Defense", x, y, 2.6, 1.85)
    root = new_landmark_root("Landmark_La_Defense", (x, y, 0.0))
    add_cube("Defense_Plaza", (0.0, 0.0, 0.055), (5.0, 3.35, 0.08), material, root)

    add_cube("Defense_Grande_Arche_Left", (-0.82, 0.0, 1.36), (0.42, 0.78, 2.58), material, root)
    add_cube("Defense_Grande_Arche_Right", (0.82, 0.0, 1.36), (0.42, 0.78, 2.58), material, root)
    add_cube("Defense_Grande_Arche_Top", (0.0, 0.0, 2.58), (2.06, 0.78, 0.42), material, root)
    add_cube("Defense_Grande_Arche_Inner_Roof", (0.0, 0.0, 2.34), (1.22, 0.66, 0.08), glass_material, root)
    for side, suffix in ((-1.0, "Left"), (1.0, "Right")):
        inner_x = side * 0.595
        for index in range(8):
            stripe_z = 0.3 + index * 0.27
            add_cube(
                f"Defense_Grande_Arche_{suffix}_Window_{index:02d}",
                (inner_x, -0.405, stripe_z),
                (0.025, 0.025, 0.14),
                window_material,
                root,
            )

    tower_specs = [
        (-2.0, -0.85, 0.58, 0.52, 2.05, 0.12),
        (-1.65, 0.92, 0.48, 0.62, 2.65, -0.08),
        (-0.75, -1.08, 0.5, 0.5, 1.72, 0.04),
        (0.82, 1.02, 0.54, 0.58, 2.35, -0.06),
        (1.65, -0.92, 0.62, 0.48, 2.82, 0.1),
        (2.08, 0.72, 0.5, 0.54, 1.95, -0.1),
    ]
    for index, (tower_x, tower_y, width, depth, height, rotation) in enumerate(tower_specs):
        tower = add_cube(
            f"Defense_Tower_{index:02d}",
            (tower_x, tower_y, height * 0.5),
            (width, depth, height),
            glass_material if index % 2 else material,
            root,
        )
        tower.rotation_euler[2] = rotation
        add_cube(
            f"Defense_Tower_{index:02d}_Cap",
            (tower_x, tower_y, height + 0.055),
            (width * 1.08, depth * 1.08, 0.11),
            material,
            root,
        ).rotation_euler[2] = rotation
        for stripe_index in range(4):
            stripe_x = tower_x + (-0.3 + stripe_index * 0.2) * width
            stripe = add_cube(
                f"Defense_Tower_{index:02d}_Stripe_{stripe_index:02d}",
                (stripe_x, tower_y - depth * 0.51, height * 0.5),
                (0.035, 0.02, height * 0.86),
                window_material,
                root,
            )
            stripe.rotation_euler[2] = rotation
    animate_layer(root, PHASE_FRAMES[4] + 180, duration=260)
    return root


def assert_modern_railways_on_land():
    for station in MODERN_STATIONS:
        station_name = station["name"]
        station_x, station_y = station["location"]
        station_length, station_width = station["size"]
        track_start, track_next = station["track"][:2]
        track_angle = math.atan2(track_next[1] - track_start[1], track_next[0] - track_start[0])
        facade_rotation = track_angle + math.pi / 2
        assert_landmark_on_land(
            station_name,
            station_x,
            station_y,
            station_length * 0.5 + 0.18,
            station_width * 0.5 + 0.18,
            facade_rotation,
        )

        for start, end in zip(station["track"], station["track"][1:]):
            segment_length = math.hypot(end[0] - start[0], end[1] - start[1])
            sample_count = max(1, math.ceil(segment_length / 0.18))
            for sample_index in range(sample_count + 1):
                amount = sample_index / sample_count
                sample_x = start[0] + (end[0] - start[0]) * amount
                sample_y = start[1] + (end[1] - start[1]) * amount
                if is_water(sample_x, sample_y, margin=0.68):
                    raise RuntimeError(
                        f"{station_name} railway corridor enters the river at "
                        f"({sample_x:.3f}, {sample_y:.3f})"
                    )


def build_modern_railways(rail_material, sleeper_material, ballast_material, station_material, roof_material, glass_material):
    assert_modern_railways_on_land()
    rail_start = PHASE_FRAMES[4] - ROAD_LEAD_FRAMES[4] + 18
    buckets = geometry_buckets(220)

    def add_track_piece(bucket, center_x, center_y, length, width, angle, z, material_id):
        vertex_start = len(bucket["vertices"])
        add_rect_geometry(
            bucket["vertices"],
            bucket["faces"],
            bucket["material_ids"],
            center_x,
            center_y,
            length,
            width,
            angle,
            z,
            material_id,
        )
        bucket.setdefault("road_ranges", []).append(vertex_start)

    for station_index, station in enumerate(MODERN_STATIONS):
        points = station["track"]
        segment_lengths = [
            math.hypot(end[0] - start[0], end[1] - start[1])
            for start, end in zip(points, points[1:])
        ]
        total_length = max(0.001, sum(segment_lengths))
        distance_before = 0.0
        for segment_index, (start, end) in enumerate(zip(points, points[1:])):
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            segment_length = segment_lengths[segment_index]
            angle = math.atan2(dy, dx)
            normal_x = -math.sin(angle)
            normal_y = math.cos(angle)
            piece_count = max(1, math.ceil(segment_length / 0.48))
            for piece_index in range(piece_count):
                amount_start = piece_index / piece_count
                amount_end = (piece_index + 1) / piece_count
                local_center = (amount_start + amount_end) * 0.5
                center_x = start[0] + dx * local_center
                center_y = start[1] + dy * local_center
                piece_length = segment_length / piece_count * 1.04
                route_progress = (distance_before + segment_length * local_center) / total_length
                timing_progress = min(0.999, station_index * 0.055 + route_progress * 0.76)
                bucket = buckets[min(len(buckets) - 1, int(timing_progress * len(buckets)))]

                for track_offset in (-0.31, 0.0, 0.31):
                    track_x = center_x + normal_x * track_offset
                    track_y = center_y + normal_y * track_offset
                    add_track_piece(bucket, track_x, track_y, piece_length, 0.22, angle, 0.052, 2)
                    for rail_offset in (-0.055, 0.055):
                        add_track_piece(
                            bucket,
                            track_x + normal_x * rail_offset,
                            track_y + normal_y * rail_offset,
                            piece_length,
                            0.022,
                            angle,
                            0.078,
                            0,
                        )
                    if piece_index % 2 == 0:
                        add_track_piece(
                            bucket,
                            track_x,
                            track_y,
                            0.18,
                            0.26,
                            angle + math.pi / 2,
                            0.067,
                            1,
                        )
            distance_before += segment_length

    rail_root = finalize_chunked_layer(
        "Modern_Railways",
        buckets,
        [rail_material, sleeper_material, ballast_material],
        rail_start,
        390,
        24,
        road=True,
        seed=11840,
    )

    stations_root = new_landmark_root("Modern_Stations")
    for station_index, station in enumerate(MODERN_STATIONS):
        station_name = station["name"]
        station_x, station_y = station["location"]
        station_length, station_width = station["size"]
        track_start, track_next = station["track"][:2]
        track_angle = math.atan2(track_next[1] - track_start[1], track_next[0] - track_start[0])
        facade_rotation = track_angle + math.pi / 2
        along = Vector((math.cos(track_angle), math.sin(track_angle)))
        across = Vector((-math.sin(track_angle), math.cos(track_angle)))
        station_root = bpy.data.objects.new(station_name, None)
        station_root.empty_display_type = "PLAIN_AXES"
        bpy.context.collection.objects.link(station_root)
        station_root.parent = stations_root

        platform_start = rail_start + 95 + station_index * 28
        for platform_index, platform_offset in enumerate((-0.42, 0.0, 0.42)):
            platform_center = Vector((station_x, station_y)) + along * 1.65 + across * platform_offset
            platform = add_cube(
                f"{station_name}_Platform_{platform_index:02d}",
                (platform_center.x, platform_center.y, 0.09),
                (3.7, 0.16, 0.09),
                sleeper_material,
                station_root,
            )
            platform.rotation_euler[2] = track_angle
            animate_axis_growth(platform, platform_start + platform_index * 9, 72, axis="X")

        hall_start = PHASE_FRAMES[4] + 52 + station_index * 34
        hall = add_cube(
            f"{station_name}_Hall",
            (station_x, station_y, 0.34),
            (station_length, station_width, 0.56),
            station_material,
            station_root,
        )
        hall.rotation_euler[2] = facade_rotation
        animate_layer(hall, hall_start, duration=118 + station_index * 9)

        roof = add_gable_roof(
            f"{station_name}_Train_Shed",
            (station_x, station_y, 0.62),
            station_length * 0.94,
            station_width * 0.9,
            0.32,
            glass_material,
            station_root,
            rotation=facade_rotation,
        )
        animate_layer(roof, hall_start + 72, duration=92 + station_index * 7)

        for wing_index, wing_side in enumerate((-1.0, 1.0)):
            wing_center = Vector((station_x, station_y)) + across * station_length * 0.48 * wing_side
            wing = add_cube(
                f"{station_name}_Wing_{wing_index:02d}",
                (wing_center.x, wing_center.y, 0.27),
                (0.68, station_width * 1.08, 0.42),
                station_material,
                station_root,
            )
            wing.rotation_euler[2] = facade_rotation
            animate_layer(wing, hall_start + 28 + wing_index * 18, duration=96)

        clock_center = Vector((station_x, station_y)) - along * station_width * 0.56 + across * station_length * 0.37
        clock_tower = add_cube(
            f"{station_name}_Clock_Tower",
            (clock_center.x, clock_center.y, 0.58),
            (0.5, 0.5, 1.02),
            station_material,
            station_root,
        )
        clock_tower.rotation_euler[2] = facade_rotation
        animate_layer(clock_tower, hall_start + 96, duration=112)
        clock_roof = add_gable_roof(
            f"{station_name}_Clock_Roof",
            (clock_center.x, clock_center.y, 1.09),
            0.62,
            0.62,
            0.31,
            roof_material,
            station_root,
            rotation=facade_rotation,
        )
        animate_layer(clock_roof, hall_start + 138, duration=78)

    return rail_root, stations_root


def polygon_y_center_at_x(polygon, x):
    intersections = []
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        min_x = min(start[0], end[0])
        max_x = max(start[0], end[0])
        if x < min_x or x > max_x:
            continue
        span = end[0] - start[0]
        if abs(span) < 1e-6:
            intersections.extend((start[1], end[1]))
            continue
        amount = (x - start[0]) / span
        if 0.0 <= amount <= 1.0:
            intersections.append(start[1] + (end[1] - start[1]) * amount)
    if len(intersections) >= 2:
        return (min(intersections) + max(intersections)) * 0.5
    return sum(point[1] for point in polygon) / len(polygon)


def ray_polygon_exit_distance(origin, direction, polygon):
    best_distance = None
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        edge_x = end[0] - start[0]
        edge_y = end[1] - start[1]
        denominator = direction.x * edge_y - direction.y * edge_x
        if abs(denominator) < 1e-7:
            continue
        offset_x = start[0] - origin.x
        offset_y = start[1] - origin.y
        distance = (offset_x * edge_y - offset_y * edge_x) / denominator
        edge_amount = (offset_x * direction.y - offset_y * direction.x) / denominator
        if distance > 1e-5 and 0.0 <= edge_amount <= 1.0:
            if best_distance is None or distance < best_distance:
                best_distance = distance
    return best_distance


def build_bridges(deck_material, stone_material):
    root = new_landmark_root("Bridges")
    roman_road_start = PHASE_FRAMES[0] - ROAD_LEAD_FRAMES[0]
    medieval_road_start = PHASE_FRAMES[1] - ROAD_LEAD_FRAMES[1]
    royal_road_start = PHASE_FRAMES[2] - ROAD_LEAD_FRAMES[2]
    bridge_specs = [
        ("ile_de_la_cite", -5.4, -1.0, roman_road_start + 45),
        ("ile_de_la_cite", -2.0, 1.0, roman_road_start + 90),
        ("ile_de_la_cite", 0.7, -1.0, medieval_road_start + 55),
        ("ile_de_la_cite", 1.0, 1.0, medieval_road_start + 105),
        ("ile_saint_louis", 3.4, -1.0, royal_road_start + 60),
        ("ile_saint_louis", 5.7, 1.0, royal_road_start + 115),
    ]
    islands = load_geodata()["islands"]
    for island_key, x, side, start_frame in bridge_specs:
        polygon = islands[island_key]
        river_y = river_center(x)
        dx = 0.08
        slope = (river_center(x + dx) - river_center(x - dx)) / (2 * dx)
        normal = Vector((-slope, 1.0)).normalized()
        island_origin = Vector((x, polygon_y_center_at_x(polygon, x)))
        river_origin = Vector((x, river_y))
        direction = normal * side
        shore_distance = ray_polygon_exit_distance(island_origin, direction, polygon)
        if shore_distance is None:
            continue
        island_edge = island_origin + direction * shore_distance
        bank_edge = river_origin + direction * (river_half_width(x) + 0.3)
        bridge_vector = bank_edge - island_edge
        if bridge_vector.dot(direction) < 0.28:
            continue
        bridge_length = bridge_vector.length
        bridge_center = (island_edge + bank_edge) * 0.5
        bridge_angle = math.atan2(bridge_vector.y, bridge_vector.x)
        bridge_rotation = bridge_angle - math.pi / 2
        segment_name = f"Bridge_{island_key}_{x}_{int(side)}"
        segment_root = bpy.data.objects.new(segment_name, None)
        segment_root.empty_display_type = "PLAIN_AXES"
        bpy.context.collection.objects.link(segment_root)
        segment_root.parent = root

        deck_width = 0.25
        side_axis = Vector((math.cos(bridge_rotation), math.sin(bridge_rotation)))
        pier_count = max(1, min(3, round(bridge_length / 1.25)))
        for pier_index in range(1, pier_count + 1):
            amount = pier_index / (pier_count + 1)
            pier_center = island_edge + bridge_vector * amount
            pier = add_cylinder(
                f"{segment_name}_Pier_{pier_index:02d}",
                (pier_center.x, pier_center.y, -0.01),
                0.16,
                0.3,
                stone_material,
                segment_root,
                vertices=8,
            )
            pier_start = start_frame + (pier_index - 1) * 12
            animate_layer(pier, pier_start, duration=42 + pier_index * 5)
            pier_cap = add_cube(
                f"{segment_name}_PierCap_{pier_index:02d}",
                (pier_center.x, pier_center.y, 0.105),
                (0.42, 0.16, 0.075),
                stone_material,
                segment_root,
            )
            pier_cap.rotation_euler[2] = bridge_rotation
            animate_layer(pier_cap, pier_start + 22, duration=28 + pier_index * 4)

        deck_segment_count = max(6, math.ceil(bridge_length / 0.32))
        deck_start = start_frame + 34
        for deck_index in range(deck_segment_count):
            amount_start = deck_index / deck_segment_count
            amount_end = (deck_index + 1) / deck_segment_count
            piece_start = island_edge + bridge_vector * amount_start
            piece_end = island_edge + bridge_vector * amount_end
            piece_center = (piece_start + piece_end) * 0.5
            piece_length = (piece_end - piece_start).length
            piece_frame = deck_start + round(deck_index * 70 / max(1, deck_segment_count - 1))
            deck = add_cube(
                f"{segment_name}_Deck_{deck_index:02d}",
                (piece_center.x, piece_center.y, 0.13),
                (deck_width, piece_length + 0.045, 0.065),
                deck_material,
                segment_root,
            )
            deck.rotation_euler[2] = bridge_rotation
            animate_axis_growth(deck, piece_frame, 30 + deck_index % 4 * 4, axis="Y")

            for rail_side in (-1.0, 1.0):
                rail_center = piece_center + side_axis * (deck_width * 0.43 * rail_side)
                rail = add_cube(
                    f"{segment_name}_Rail_{deck_index:02d}_{int(rail_side)}",
                    (rail_center.x, rail_center.y, 0.18),
                    (0.028, piece_length + 0.04, 0.04),
                    stone_material,
                    segment_root,
                )
                rail.rotation_euler[2] = bridge_rotation
                animate_axis_growth(rail, piece_frame + 14, 24 + deck_index % 3 * 4, axis="Y")
    return root


def setup_camera():
    camera_data = bpy.data.cameras.new("Cartographic_Camera")
    camera = bpy.data.objects.new("Cartographic_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera_data.type = "ORTHO"

    keyframes = [
        (1, (-104.0, -136.0, 194.0), (-8.0, 8.0, 0.0), 118.0),
        (36, (-94.0, -124.0, 180.0), (-6.8, 7.4, 0.0), 105.0),
        (72, (-76.0, -101.0, 148.0), (-4.2, 5.1, 0.0), 78.0),
        (102, (-57.0, -76.0, 114.0), (-1.8, 2.4, 0.0), 43.0),
        (120, (-44.0, -60.0, 90.0), (0.0, 0.0, 0.0), 25.0),
        (270, (-40.0, -55.0, 84.0), (0.4, -0.2, 0.0), 22.0),
        (510, (-42.0, -57.0, 87.0), (-0.3, 0.5, 0.0), 24.0),
        (750, (-45.0, -62.0, 92.0), (0.2, 0.0, 0.0), 29.0),
        (825, (-46.0, -64.0, 94.0), (0.0, 0.3, 0.0), 32.0),
        (1500, (-53.0, -74.0, 105.0), (-1.5, 2.0, 0.0), 58.0),
        (2175, (-58.0, -82.0, 114.0), (-2.5, 3.0, 0.0), 82.0),
        (2850, (-63.0, -89.0, 124.0), (-3.5, 4.0, 0.0), 104.0),
        (3600, (-68.0, -96.0, 134.0), (-4.0, 4.5, 0.0), 122.0),
    ]
    for frame, location, target, scale in keyframes:
        camera.location = location
        direction = Vector(target) - camera.location
        camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        camera.keyframe_insert(data_path="location", frame=frame)
        camera.keyframe_insert(data_path="rotation_euler", frame=frame)
        camera_data.ortho_scale = scale
        camera_data.keyframe_insert(data_path="ortho_scale", frame=frame)
    for animated in (camera, camera_data):
        if not animated.animation_data or not animated.animation_data.action:
            continue
        for fcurve in animated.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "BEZIER"
                keyframe.handle_left_type = "AUTO_CLAMPED"
                keyframe.handle_right_type = "AUTO_CLAMPED"
    bpy.context.scene.camera = camera


def setup_lighting():
    world = bpy.context.scene.world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.085, 0.105, 0.06, 1.0)
    background.inputs["Strength"].default_value = 0.58

    sun_data = bpy.data.lights.new(name="Sun", type="SUN")
    sun_data.energy = 3.35
    sun_data.angle = math.radians(2.2)
    sun = bpy.data.objects.new(name="Sun", object_data=sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(38), math.radians(-18), math.radians(28))

    area_data = bpy.data.lights.new(name="Sky_Fill", type="AREA")
    area_data.energy = 430
    area_data.shape = "DISK"
    area_data.size = 70
    area = bpy.data.objects.new(name="Sky_Fill", object_data=area_data)
    bpy.context.collection.objects.link(area)
    area.location = (0, -5, 45)


def configure_scene():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = 32
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 2.4
    scene.eevee.gtao_quality = 1.0
    scene.eevee.use_shadows = True
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.use_motion_blur = True
    scene.render.motion_blur_position = "CENTER"
    scene.render.motion_blur_shutter = 0.22
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.16
    scene.render.image_settings.compression = 18


def build_scene():
    BUILDING_FOOTPRINTS.clear()
    BUILDING_FOOTPRINT_GRID.clear()
    ALL_ERA_FOOTPRINTS.clear()
    clear_scene()
    configure_scene()

    land_mat = make_material("Land_Material", (0.245, 0.315, 0.155), roughness=0.8, ior_level=0.36)
    water_mat = make_water_material()
    riverbank_mat = make_material("Riverbank_Silt", (0.54, 0.49, 0.29), roughness=0.88, ior_level=0.34)
    road_mat = make_material("Road_Material", (0.6, 0.555, 0.4), roughness=0.7, ior_level=0.42)
    bridge_stone_mat = make_material("Bridge_Stone", (0.68, 0.61, 0.45), roughness=0.62, ior_level=0.48)
    wall_a = make_material("Wall_Warm", (0.64, 0.51, 0.36), roughness=0.48, ior_level=0.56, coat_weight=0.08)
    wall_b = make_material("Wall_Pale", (0.76, 0.67, 0.51), roughness=0.46, ior_level=0.58, coat_weight=0.1)
    wall_c = make_material("Wall_Stone", (0.53, 0.49, 0.39), roughness=0.52, ior_level=0.52, coat_weight=0.06)
    wall_brick = make_material("Wall_Brick", (0.5, 0.22, 0.105), roughness=0.54, ior_level=0.52, coat_weight=0.06)
    wall_ochre = make_material("Wall_Ochre", (0.7, 0.4, 0.19), roughness=0.5, ior_level=0.54, coat_weight=0.08)
    roof_red = make_material("Roof_Terracotta", (0.43, 0.075, 0.024), roughness=0.18, ior_level=0.72, coat_weight=0.36)
    roof_slate = make_material("Roof_Slate", (0.14, 0.165, 0.16), roughness=0.22, ior_level=0.68, coat_weight=0.26)
    roof_zinc = make_material("Roof_Zinc", (0.5, 0.48, 0.42), metallic=0.1, roughness=0.2, ior_level=0.7, coat_weight=0.28)
    roof_weathered = make_material("Roof_Weathered", (0.35, 0.17, 0.075), roughness=0.28, ior_level=0.64, coat_weight=0.16)
    landmark_mat = make_material("Landmark_Stone", (0.82, 0.73, 0.53), roughness=0.32, ior_level=0.66, coat_weight=0.22)
    landmark_window_mat = make_material("Landmark_Window", (0.035, 0.065, 0.06), roughness=0.24, ior_level=0.72, coat_weight=0.18)
    building_window_dark = make_material("Building_Window_Dark", (0.018, 0.045, 0.052), roughness=0.16, ior_level=0.78, coat_weight=0.32)
    building_window_warm = make_material("Building_Window_Warm", (0.72, 0.34, 0.075), roughness=0.19, ior_level=0.72, coat_weight=0.28)
    warm_window_bsdf = building_window_warm.node_tree.nodes.get("Principled BSDF") or next(
        (
            node
            for node in building_window_warm.node_tree.nodes
            if node.type == "BSDF_PRINCIPLED"
        ),
        None,
    )
    if warm_window_bsdf and "Emission Color" in warm_window_bsdf.inputs:
        warm_window_bsdf.inputs["Emission Color"].default_value = (0.72, 0.25, 0.035, 1.0)
    if warm_window_bsdf and "Emission Strength" in warm_window_bsdf.inputs:
        warm_window_bsdf.inputs["Emission Strength"].default_value = 0.42
    building_door_mat = make_material("Building_Door", (0.12, 0.048, 0.018), roughness=0.42, ior_level=0.56, coat_weight=0.08)
    building_trim_mat = make_material("Building_Trim", (0.82, 0.73, 0.57), roughness=0.4, ior_level=0.62, coat_weight=0.12)
    roman_arena_mat = make_material("Roman_Arena_Sand", (0.66, 0.49, 0.27), roughness=0.86, ior_level=0.36)
    eiffel_iron_mat = make_material("Eiffel_Iron", (0.27, 0.085, 0.022), metallic=0.42, roughness=0.3, ior_level=0.66, coat_weight=0.2)
    eiffel_detail_mat = make_material("Eiffel_Iron_Highlight", (0.48, 0.19, 0.052), metallic=0.32, roughness=0.34, ior_level=0.62, coat_weight=0.15)
    glass_mat = make_material("Modern_Glass", (0.13, 0.28, 0.29), metallic=0.16, roughness=0.22, ior_level=0.7, coat_weight=0.22)
    forest_dark = make_material("Forest_Dark", (0.052, 0.14, 0.04), roughness=0.76, ior_level=0.42)
    forest_light = make_material("Forest_Light", (0.095, 0.215, 0.065), roughness=0.72, ior_level=0.44)
    forest_trunk = make_material("Forest_Trunk", (0.17, 0.115, 0.065), roughness=0.88, ior_level=0.32)
    forest_olive = make_material("Forest_Olive", (0.15, 0.23, 0.075), roughness=0.74, ior_level=0.43)
    forest_deep = make_material("Forest_Deep", (0.027, 0.095, 0.032), roughness=0.79, ior_level=0.39)
    rail_steel_mat = make_material("Rail_Steel", (0.085, 0.09, 0.085), metallic=0.72, roughness=0.27, ior_level=0.64)
    rail_sleeper_mat = make_material("Rail_Sleeper", (0.18, 0.105, 0.052), roughness=0.78, ior_level=0.38)
    rail_ballast_mat = make_material("Rail_Ballast", (0.28, 0.27, 0.23), roughness=0.9, ior_level=0.3)
    building_materials = [
        wall_a,
        wall_b,
        wall_c,
        roof_red,
        roof_slate,
        roof_zinc,
        wall_brick,
        wall_ochre,
        roof_weathered,
        building_window_dark,
        building_window_warm,
        building_door_mat,
        building_trim_mat,
    ]
    islands = load_geodata()["islands"]

    create_land(land_mat)
    create_riverbank(riverbank_mat)
    create_river(water_mat)
    create_island_margin(riverbank_mat, "Ile_de_la_Cite_Margin", islands["ile_de_la_cite"])
    create_island_margin(riverbank_mat, "Ile_Saint_Louis_Margin", islands["ile_saint_louis"])
    create_island(land_mat, "Ile_de_la_Cite", islands["ile_de_la_cite"])
    create_island(land_mat, "Ile_Saint_Louis", islands["ile_saint_louis"])
    build_bridges(road_mat, bridge_stone_mat)

    layer_specs = [
        ("Buildings_Roman_State", 0, 1800, 101, "roman"),
        ("Buildings_Medieval_State", 1, 4800, 202, "medieval"),
        ("Buildings_1700_State", 2, 7600, 303, "royal"),
        ("Buildings_1850_State", 3, 10500, 404, "haussmann"),
        ("Buildings_Modern_State", 4, 13500, 505, "modern"),
    ]
    island_counts = [
        (240, 75),
        (350, 180),
        (420, 230),
        (450, 260),
        (470, 280),
    ]
    island_styles = ["roman", "medieval", "royal", "haussmann", "haussmann"]
    building_states = []
    road_roots = []
    for index, spec in enumerate(layer_specs):
        begin_era_footprints(index)
        road_roots.append(create_road_layer(
            f"Roads_{index}",
            index,
            road_mat,
            max(1, PHASE_FRAMES[index] - ROAD_LEAD_FRAMES[index]),
            ROAD_REVEAL_FRAMES[index],
            chunk_count=180 + index * 28,
        ))
        state_roots = [create_building_layer(
            *spec,
            building_materials,
            PHASE_FRAMES[index],
            PHASE_REVEAL_FRAMES[index],
            BUILDING_CHUNKS[index],
            BUILDING_GROW_FRAMES[index],
        )]
        cite_count, saint_louis_count = island_counts[index]
        state_roots.append(create_island_building_layer(
            f"Island_Cite_{index}_State",
            "ile_de_la_cite",
            index,
            islands["ile_de_la_cite"],
            cite_count,
            606 + index * 101,
            island_styles[index],
            building_materials,
            PHASE_FRAMES[index] + 4,
            PHASE_REVEAL_FRAMES[index],
            cite_count,
            BUILDING_GROW_FRAMES[index],
        ))
        state_roots.append(create_island_building_layer(
            f"Island_Saint_Louis_{index}_State",
            "ile_saint_louis",
            index,
            islands["ile_saint_louis"],
            saint_louis_count,
            808 + index * 103,
            island_styles[index],
            building_materials,
            PHASE_FRAMES[index] + 10,
            max(48, PHASE_REVEAL_FRAMES[index] - 6),
            saint_louis_count,
            BUILDING_GROW_FRAMES[index],
        ))
        if audit_footprint_overlaps() != 0:
            raise RuntimeError(f"Building footprint audit failed for era {index}")
        archive_era_footprints()
        building_states.append(state_roots)

    for index, state_roots in enumerate(building_states[:-1]):
        transition_start = PHASE_FRAMES[index + 1] - 6
        transition_reveal = max(120, PHASE_REVEAL_FRAMES[index + 1] - 18)
        for root in state_roots:
            animate_progressive_removal(
                root,
                transition_start,
                spread_frames=transition_reveal,
                duration=8,
            )
    animate_progressive_removal(
        road_roots[0],
        PHASE_FRAMES[1] + 42,
        spread_frames=360,
        duration=78,
        road=True,
    )

    build_roman_theatre(landmark_mat, roof_red, roman_arena_mat, landmark_window_mat)
    build_roman_forum(landmark_mat, roof_red, road_mat, landmark_window_mat)
    build_medieval_island_wall(landmark_mat, roof_red, islands["ile_de_la_cite"])
    build_notre_dame(landmark_mat, roof_slate, landmark_window_mat)
    build_louvre(landmark_mat, roof_slate, road_mat, landmark_window_mat)
    build_arc(landmark_mat, landmark_window_mat)
    build_champ_de_mars(road_mat, [forest_dark, forest_light, forest_trunk])
    build_eiffel(eiffel_iron_mat, eiffel_detail_mat)
    build_la_defense(landmark_mat, glass_mat, landmark_window_mat)
    build_modern_railways(
        rail_steel_mat,
        rail_sleeper_mat,
        rail_ballast_mat,
        landmark_mat,
        roof_slate,
        glass_mat,
    )

    restore_tree_exclusion_footprints()
    create_forest_layers([forest_dark, forest_light, forest_trunk, forest_olive, forest_deep])

    setup_camera()
    setup_lighting()
    scene = bpy.context.scene
    scene.frame_set(1)
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))


def render_stills():
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_percentage = 50
    frames = [
        (1, "00_opening_high.png"),
        (90, "01_helicopter_descent.png"),
        (120, "02_island_focus.png"),
        (240, "03_roman_road_growth.png"),
        (540, "04_roman_building_growth.png"),
        (900, "05_medieval_growth.png"),
        (1575, "06_royal_growth.png"),
        (2250, "07_haussmann_growth.png"),
        (3000, "08_modern_rail_growth.png"),
        (3375, "09_modern_city_growth.png"),
        (3598, "08_final.png"),
    ]
    for frame, filename in frames:
        scene.frame_set(frame)
        scene.render.filepath = str(STILLS_DIR / filename)
        bpy.ops.render.render(write_still=True)


def render_animation():
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.video_bitrate = 12000
    scene.render.filepath = str(RENDERS_DIR / "paris_five_eras_blender_2min_v2.mp4")
    bpy.ops.render.render(animation=True)


def render_opening_preview():
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 1200
    scene.render.resolution_percentage = 35
    scene.eevee.taa_render_samples = 16
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.filepath = str(PREVIEWS_DIR / "opening_motion_v2.mp4")
    bpy.ops.render.render(animation=True)


def render_timing_preview():
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.render.resolution_percentage = 25
    scene.eevee.taa_render_samples = 8
    scene.render.use_motion_blur = False
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.filepath = str(PREVIEWS_DIR / "paris_five_eras_timing_v2.mp4")
    bpy.ops.render.render(animation=True)


def main():
    args = parse_args()
    if args.mode == "setup":
        build_scene()
    else:
        if not BLEND_PATH.exists():
            build_scene()
        else:
            bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))
        if args.mode == "stills":
            render_stills()
        elif args.mode == "opening":
            render_opening_preview()
        elif args.mode == "preview":
            render_timing_preview()
        elif args.mode == "render":
            render_animation()


if __name__ == "__main__":
    main()
