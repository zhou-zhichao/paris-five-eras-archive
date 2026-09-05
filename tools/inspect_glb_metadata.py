import argparse
import json
import struct
from pathlib import Path


def read_glb_json(path):
    with path.open("rb") as handle:
        magic, version, total_length = struct.unpack("<4sII", handle.read(12))
        if magic != b"glTF":
            raise ValueError(f"{path} is not a GLB file")
        chunk_length, chunk_type = struct.unpack("<II", handle.read(8))
        if chunk_type != 0x4E4F534A:
            raise ValueError(f"{path} does not start with a JSON chunk")
        document = json.loads(handle.read(chunk_length).decode("utf-8").rstrip(" \t\r\n\x00"))
    return version, total_length, document


def primitive_triangle_count(primitive, accessors):
    mode = primitive.get("mode", 4)
    accessor_index = primitive.get("indices")
    if accessor_index is None:
        position_index = primitive.get("attributes", {}).get("POSITION")
        count = accessors[position_index].get("count", 0) if position_index is not None else 0
    else:
        count = accessors[accessor_index].get("count", 0)
    if mode == 4:
        return count // 3
    if mode in (5, 6):
        return max(0, count - 2)
    return 0


def inspect(path):
    version, declared_size, document = read_glb_json(path)
    accessors = document.get("accessors", [])
    meshes = document.get("meshes", [])
    primitives = [primitive for mesh in meshes for primitive in mesh.get("primitives", [])]
    position_accessors = {
        primitive.get("attributes", {}).get("POSITION")
        for primitive in primitives
        if primitive.get("attributes", {}).get("POSITION") is not None
    }
    vertices = sum(accessors[index].get("count", 0) for index in position_accessors)
    triangles = sum(primitive_triangle_count(primitive, accessors) for primitive in primitives)
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "glb_version": version,
        "declared_bytes": declared_size,
        "nodes": len(document.get("nodes", [])),
        "meshes": len(meshes),
        "primitives": len(primitives),
        "vertices": vertices,
        "triangles": triangles,
        "materials": len(document.get("materials", [])),
        "textures": len(document.get("textures", [])),
        "images": len(document.get("images", [])),
        "animations": len(document.get("animations", [])),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = [inspect(path) for path in args.paths]
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
