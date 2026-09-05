"""Triangulate the traced river with interior vertices and shoreline distances."""
from pathlib import Path
import json
import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
from scipy.spatial import Delaunay

ROOT=Path(__file__).resolve().parents[1]
city=json.loads((ROOT/'data/city.json').read_text())
river=unary_union([Polygon(p) for p in city['water_outer']])
islands=unary_union([Polygon(p) for p in city['islands']])
water=river.difference(islands)
shore=water.boundary
chunks=[]
polys=list(water.geoms) if hasattr(water,'geoms') else [water]
for poly in polys:
    minx,miny,maxx,maxy=poly.bounds
    xx,yy=np.meshgrid(np.arange(minx,maxx,2),np.arange(miny,maxy,2))
    grid=np.column_stack([xx.ravel(),yy.ravel()])
    grid=grid[shapely.contains_xy(poly,grid[:,0],grid[:,1])]
    edges=np.array(list(poly.exterior.coords)+[p for ring in poly.interiors for p in ring.coords])
    xy=np.unique(np.vstack([grid,edges]),axis=0)
    faces=Delaunay(xy).simplices
    centers=xy[faces].mean(axis=1)
    faces=faces[shapely.contains_xy(poly,centers[:,0],centers[:,1])]
    distances=shapely.distance(shapely.points(xy),shore)
    chunks.append({'vertices':np.round(xy,4).tolist(),'triangles':faces.tolist(),'bank_distance':np.round(distances,4).tolist()})
(ROOT/'data/water_surface.json').write_text(json.dumps(chunks,separators=(',',':')))
print(json.dumps({'water_vertices':sum(len(p['vertices']) for p in chunks),'water_triangles':sum(len(p['triangles']) for p in chunks)}))
