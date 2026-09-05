"""Original, instancing-friendly miniature architecture and landmark components."""
import bpy
import math
import random

MATERIALS=[]

def srgb(hexcode):
    v=[int(hexcode[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v)

def material(name, color, rough=.72, metal=0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*srgb(color),1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=m.diffuse_color
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metal
    MATERIALS.append(m)
    return len(MATERIALS)-1

def palette():
    ids={}
    for name,color in [
        ('limestone','#D7CDB5'),('warm_plaster','#E3CCAA'),('ivory','#E7DEC8'),
        ('grey_plaster','#BCB9A9'),('ochre_plaster','#C7AE84'),('pink_plaster','#C8B3A2'),
        ('terracotta','#C56F51'),('clay','#B45D43'),('rose_tile','#D58970'),
        ('slate','#A3A7A1'),('zinc','#BEC1B5'),('charcoal_roof','#8A9291'),
        ('window','#626559'),('timber','#635044'),('brick','#94604E'),
        ('cornice','#E3D8C2'),('sand','#BEB493'),('path','#B4B49B'),
        ('green_0','#3C512B'),('green_1','#4B5F33'),('green_2','#5A6D40'),
        ('green_3','#334B2C'),('green_4','#647244'),('trunk','#63543C'),
        ('lawn','#596C38'),('garden','#63833F'),('asphalt','#797B68'),
        ('copper','#579484'),('gold','#C8A65A'),('concrete','#B9B9AC')]:
        ids[name]=material(name,color,.45 if name=='copper' else .79,.18 if name in ['copper','gold'] else 0)
    return ids

class Mesh:
    def __init__(self):
        self.v=[];self.f=[];self.m=[];self.birth=[]
    def face(self,points,mat,born=-100):
        start=len(self.v)
        self.v.extend(points)
        self.f.append(tuple(range(start,len(self.v))))
        self.m.append(mat)
        self.birth.extend([born]*len(points))
    def box(self,x,y,z,w,d,h,mat):
        x0,x1=x-w/2,x+w/2;y0,y1=y-d/2,y+d/2
        vs=[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z),(x0,y0,z+h),(x1,y0,z+h),(x1,y1,z+h),(x0,y1,z+h)]
        for ix in [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]:
            self.face([vs[i] for i in ix],mat)
    def roof(self,w,d,z,rise,mat,hip=True):
        x=w/2;y=d/2
        a=(-x,-y,z);b=(x,-y,z);c=(x,y,z);e=(-x,y,z)
        inset=min(w*.27,d*.36) if hip else 0
        u=(-x+inset,0,z+rise);v=(x-inset,0,z+rise)
        for poly in [(a,b,v,u),(e,u,v,c),(a,u,e),(b,c,v)]:self.face(poly,mat)
    def frustum(self,x,y,z,rx,ry,h,topx,topy,mat,sides=12,phase=0):
        bottom=[(x+rx*math.cos(i*2*math.pi/sides+phase),y+ry*math.sin(i*2*math.pi/sides+phase),z) for i in range(sides)]
        top=[(x+topx*math.cos(i*2*math.pi/sides+phase),y+topy*math.sin(i*2*math.pi/sides+phase),z+h) for i in range(sides)]
        self.face(list(reversed(bottom)),mat)
        self.face(top,mat)
        for i in range(sides):self.face([bottom[i],bottom[(i+1)%sides],top[(i+1)%sides],top[i]],mat)
    def dome(self,x,y,z,r,h,mat,sides=18,rings=7):
        for k in range(rings):
            a=k/rings*math.pi/2;b=(k+1)/rings*math.pi/2
            self.frustum(x,y,z+math.sin(a)*h,math.cos(a)*r,math.cos(a)*r,(math.sin(b)-math.sin(a))*h,math.cos(b)*r,math.cos(b)*r,mat,sides)
    def object(self,name,collection=None):
        mesh=bpy.data.meshes.new(name)
        mesh.from_pydata(self.v,[],self.f)
        mesh.materials.clear()
        for m in MATERIALS:mesh.materials.append(m)
        for p,mid in zip(mesh.polygons,self.m):p.material_index=mid
        mesh.update()
        ob=bpy.data.objects.new(name,mesh)
        (collection or bpy.context.scene.collection).objects.link(ob)
        if self.birth:
            attr=mesh.attributes.new('born','FLOAT','POINT')
            attr.data.foreach_set('value',self.birth)
        return ob

def house(kind,variant,ids):
    """Model roofs, actual cornices/chimneys/dormers and recessed-looking window planes."""
    m=Mesh();r=random.Random(kind*971+variant*47)
    wall=ids[['limestone','warm_plaster','ivory','grey_plaster','ochre_plaster','pink_plaster'][variant%6]]
    roof=ids[['terracotta','clay','rose_tile'][variant%3]] if kind<2 else ids[['slate','zinc','charcoal_roof'][variant%3] if variant!=11 else 'rose_tile']
    body=.71 if kind<2 else .79
    m.box(0,0,0,1,1,body,wall)
    m.box(0,0,.025,1.018,1.012,.026,ids['sand'])
    m.box(0,0,body-.035,1.045,1.045,.04,ids['cornice'])
    if kind==3:
        # Four-sided mansard: steep lower slope, shallow zinc upper roof.
        z=body+.17
        corners=[(-.53,-.53,body),(.53,-.53,body),(.53,.53,body),(-.53,.53,body)]
        top=[(-.41,-.35,z),(.41,-.35,z),(.41,.35,z),(-.41,.35,z)]
        for i in range(4):m.face([corners[i],corners[(i+1)%4],top[(i+1)%4],top[i]],roof)
        for poly in [[top[0],top[1],(.25,0,1.04),(-.25,0,1.04)],[top[3],(-.25,0,1.04),(.25,0,1.04),top[2]],[top[0],(-.25,0,1.04),top[3]],[top[1],top[2],(.25,0,1.04)]]:m.face(poly,ids['zinc'])
    elif kind==5:
        m.box(0,0,body,1.035,1.035,.045,roof)
        m.box(.1,.08,body+.05,.3,.3,.1,ids['concrete'])
    else:
        m.roof(1.07,1.07,body,.29 if kind!=1 else .40,roof,hip=(kind!=1 or variant%3==0))
    floors=[1,2,3,4,2,5][kind]
    bays=2+variant%3
    for sy in [-1,1]:
        for floor in range(floors):
            z=.11+floor*(body-.12)/floors
            for bay in range(bays):
                x=-.36+bay*.72/max(1,bays-1)
                ww=.105 if bays<4 else .08
                hh=(body-.19)/floors*.48
                y=sy*.501
                m.face([(x-ww/2,y,z),(x+ww/2,y,z),(x+ww/2,y,z+hh),(x-ww/2,y,z+hh)],ids['window'])
        if kind in [2,3]:
            for floor in range(1,floors):
                m.box(0,sy*.505,.10+floor*(body-.12)/floors,1.022,.018,.012,ids['cornice'])
        if kind in [1,2,3]:
            for x in [-.25,.25]:
                m.box(x,sy*.39,body+.025,.115,.16,.125,wall)
                # Dark dormer opening contrasts with its light cheek wall.
                yy=sy*.477
                m.face([(x-.031,yy,body+.055),(x+.031,yy,body+.055),(x+.031,yy,body+.13),(x-.031,yy,body+.13)],ids['window'])
                m.face([(x-.08,sy*.49,body+.15),(x+.08,sy*.49,body+.15),(x,sy*.37,body+.23)],roof)
    if kind==1 and variant%3==0:
        for sy in [-1,1]:
            m.box(0,sy*.504,body*.48,1.01,.02,.026,ids['timber'])
            for x in [-.43,0,.43]:m.box(x,sy*.508,0,.019,.021,body,ids['timber'])
    if kind!=5:
        for x in ([-.32,.30] if kind>1 else [.29]):
            m.box(x,.10,.90,.09,.11,.22,ids['brick'])
            m.box(x,.10,1.105,.12,.13,.028,ids['sand'])
    return m

def tree(variant,ids):
    m=Mesh()
    m.frustum(0,0,0,.035,.035,.42,.022,.022,ids['trunk'],5)
    leaf=ids['green_'+str(variant%5)]
    if variant in [5,6]:
        for z,r,h in [(.20,.34,.45),(.40,.29,.4),(.62,.20,.36)]:m.frustum(0,0,z,r,r,h,0,0,leaf,7,variant*.7)
    else:
        widths=[.08,.29,.40,.39,.27,.035]
        zs=[.26,.36,.55,.76,.92,1.03]
        if variant==4:widths=[v*.7 for v in widths];zs=[z*1.12 for z in zs]
        for i in range(5):m.frustum(0,0,zs[i],widths[i],widths[i]*.87,zs[i+1]-zs[i],widths[i+1],widths[i+1]*.87,leaf,7,variant*.8)
    return m

def landmark(kind,size,ids):
    """Hand-built architectural silhouettes, kept independent of ordinary house assets."""
    m=Mesh();stone=ids['limestone'];slate=ids['charcoal_roof'];s=size
    if kind=='rail_station':
        m.box(0,-s*.55,0,s*1.1,s*.20,s*.17,stone)
        m.box(0,-s*.55,s*.17,s*1.12,s*.23,s*.045,slate)
        for shed in range(4):
            cx=(shed-1.5)*s*.25
            for i in range(12):
                a=i/12*math.pi;b=(i+1)/12*math.pi
                m.face([(cx+math.cos(a)*s*.115,-s*.45,s*.10+math.sin(a)*s*.11),(cx+math.cos(b)*s*.115,-s*.45,s*.10+math.sin(b)*s*.11),(cx+math.cos(b)*s*.115,s*.80,s*.10+math.sin(b)*s*.11),(cx+math.cos(a)*s*.115,s*.80,s*.10+math.sin(a)*s*.11)],ids['zinc'])
            for x in [cx-s*.116,cx+s*.116]:m.box(x,s*.15,0,.025*s,1.3*s,.1*s,stone)
        return m
    if kind=='forum':
        for x in [-s*.41,s*.41]:
            m.box(x,0,0,.18*s,s,.04*s,stone)
            for j in range(10):m.frustum(x,(-.45+j*.1)*s,.04*s,.022*s,.022*s,.24*s,.021*s,.021*s,stone,8)
            m.box(x,0,.28*s,.2*s,s,.035*s,stone)
        m.box(0,s*.35,0,.40*s,.38*s,.08*s,stone)
        m.box(0,s*.35,.08*s,.30*s,.31*s,.28*s,stone)
        m.box(0,s*.35,.36*s,.46*s,.44*s,.04*s,ids['terracotta'])
        for x in [-.16*s,-.06*s,.06*s,.16*s]:m.frustum(x,.12*s,.08*s,.02*s,.02*s,.28*s,.02*s,.02*s,stone,8)
        return m
    if kind=='palace':
        for x,y,w,d in [(-s*.42,0,s*.18,s),(s*.42,0,s*.18,s),(0,s*.43,s,.14*s)]:m.box(x,y,0,w,d,s*.18,stone)
        for x in [-s*.42,s*.42]:m.box(x,0,s*.18,s*.20,s*1.02,s*.07,slate)
        m.box(0,s*.43,s*.18,s,.17*s,s*.07,slate)
        for x in [-s*.42,0,s*.42]:
            m.box(x,s*.43,0,s*.2,s*.23,s*.28,stone)
            m.frustum(x,s*.43,s*.28,s*.16,s*.16,s*.14,0,0,slate,4,math.pi/4)
        for x in [-s*.42,s*.42]:
            for y in [(-.38+i*.1)*s for i in range(8)]:m.box(x+s*.1,y,s*.08,.03*s,.042*s,.07*s,ids['window'])
    elif kind in ['dome','basilica','church']:
        m.box(0,0,0,s*.55,s,.32*s,stone)
        m.box(0,-s*.35,0,s*.75,s*.15,s*.4,stone)
        m.box(0,0,s*.32,s*.58,s*.97,s*.07,slate)
        if kind=='church':
            for x in [-s*.24,s*.24]:
                m.box(x,-s*.4,0,s*.17,s*.18,s*.58,stone)
                m.frustum(x,-s*.4,s*.58,s*.14,s*.14,s*.3,0,0,slate,4,math.pi/4)
        else:
            m.frustum(0,0,s*.33,s*.22,s*.22,s*.17,s*.22,s*.22,stone,18)
            m.dome(0,0,s*.5,s*.24,s*.28,ids['gold'] if kind=='dome' else stone)
            m.frustum(0,0,s*.78,s*.032,s*.032,s*.16,0,0,stone,8)
            for x in [-.28*s,.28*s]:
                m.frustum(x,-.25*s,0,s*.10,s*.10,s*.49,s*.1,s*.1,stone,10)
                m.dome(x,-.25*s,.49*s,.12*s,.16*s,stone)
        for x in [-.21*s,-.07*s,.07*s,.21*s]:m.frustum(x,-s*.455,0,s*.025,s*.025,s*.30,s*.025,s*.025,stone,8)
    elif kind=='arch':
        for x in [-.3*s,.3*s]:m.box(x,0,0,.28*s,.39*s,s*.63,stone)
        m.box(0,0,s*.52,s,.44*s,s*.27,stone)
        m.box(0,0,s*.78,s*1.05,.48*s,s*.06,ids['cornice'])
        # Stepped voussoirs retain an open arch instead of a solid cube.
        for i in range(10):
            a=math.pi*i/10;b=math.pi*(i+1)/10
            for y in [-.205*s,.205*s]:m.face([(math.cos(a)*.23*s,y,.45*s+math.sin(a)*.23*s),(math.cos(b)*.23*s,y,.45*s+math.sin(b)*.23*s),(math.cos(b)*.29*s,y,.45*s+math.sin(b)*.29*s),(math.cos(a)*.29*s,y,.45*s+math.sin(a)*.29*s)],ids['sand'])
    elif kind=='keep':
        m.box(0,0,0,.5*s,.6*s,.55*s,stone)
        for x in [-.3*s,.3*s]:
            for y in [-.3*s,.3*s]:
                m.frustum(x,y,0,.13*s,.13*s,.63*s,.13*s,.13*s,stone,10)
                m.frustum(x,y,.63*s,.17*s,.17*s,.22*s,0,0,slate,10)
    elif kind=='arena':
        for i in range(52):
            a=i/52*math.tau;b=(i+1)/52*math.tau
            for j in range(3):
                r0=.33+j*.055;r1=r0+.055;z=(j+1)*s*.035
                m.face([(math.cos(a)*r0*s,math.sin(a)*r0*s*.76,z),(math.cos(b)*r0*s,math.sin(b)*r0*s*.76,z),(math.cos(b)*r1*s,math.sin(b)*r1*s*.76,z),(math.cos(a)*r1*s,math.sin(a)*r1*s*.76,z)],stone)
            m.face([(math.cos(a)*.5*s,math.sin(a)*.5*s*.76,0),(math.cos(b)*.5*s,math.sin(b)*.5*s*.76,0),(math.cos(b)*.5*s,math.sin(b)*.5*s*.76,s*.14),(math.cos(a)*.5*s,math.sin(a)*.5*s*.76,s*.14)],stone)
    return m
