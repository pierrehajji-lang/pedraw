# T-shirt oversize pour le mockup 3D — à lancer avec Blender (sans interface) :
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P mockup/blender/tshirt.py -- mockup/tshirt.glb [apercu.png]
# Méthode (skills blender-skills : reference-image-match + cloth-sim) :
#   1. Forme de départ mesurée sur la photo de référence (coupe boxy, épaules tombantes, manches larges).
#   2. Simulation de tissu (coton) posée sur un mannequin invisible : les manches et le bas tombent pour de vrai.
#   3. Col bord-côte, épaisseur du tissu, ombres des plis cuites dans les couleurs de sommet, export .glb.
import bpy, bmesh, math, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else '/tmp/tshirt.glb'
PREVIEW = argv[1] if len(argv) > 1 else None

S = 0.55          # 1 unité de dessin = largeur de poitrine = 55 cm (oversize M)
VOXEL = 0.008     # finesse du maillage du tissu (8 mm)
FRAMES = 60       # durée de la simulation (images)

def P(x, y, z):   # repère du dessin (y en haut, z vers l'avant) → repère Blender (z en haut, -y vers l'avant), en mètres
    return Vector((x * S, -z * S, y * S))

def sstep(e0, e1, x):
    t = min(1, max(0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)

def lerp(a, b, t): return a + (b - a) * t

def curve(keys, t):   # Catmull-Rom à travers les sections clés
    n = len(keys) - 1; f = t * n; i = min(n - 1, int(f)); u = f - i
    p0, p1, p2, p3 = keys[max(0, i - 1)], keys[i], keys[i + 1], keys[min(n, i + 2)]
    return [.5 * (2*b + (-a + c)*u + (2*a - 5*b + 4*c - d)*u*u + (-a + 3*b - 3*c + d)*u*u*u) for a, b, c, d in zip(p0, p1, p2, p3)]

# ---------- Mesures prises sur la photo (unités de dessin) ----------
HEM, TOP = -.80, .625
# [hauteur, demi-largeur, demi-épaisseur, rondeur]
TK = [[-.80,.490,.215,2.9],[-.55,.493,.222,2.9],[-.20,.497,.230,2.9],[.10,.500,.236,2.8],[.32,.510,.236,2.7],[.44,.520,.232,2.6],
      [.50,.505,.222,2.5],[.55,.440,.205,2.4],[.59,.340,.180,2.2],[.613,.258,.156,2.05],[TOP,.215,.138,2]]
NECK_A, NECK_B = .215, .138
def dip(s, y): return .065 * max(0, s) ** 2.5 * sstep(.45, TOP, y)   # encolure plus basse devant

def torso_ring(v, n, kx=1, kz=1):
    y0, a, b, p = curve(TK, v); e = 2 / p; pts = []
    for j in range(n):
        th = j / n * 2 * math.pi; c, s = math.cos(th), math.sin(th)
        x = a * kx * math.copysign(abs(c) ** e, c); z = b * kz * math.copysign(abs(s) ** e, s)
        pts.append(P(x, y0 - dip(s, y0), z))
    return pts

# Manche : de l'anneau planté dans le corps (épaule tombante) jusqu'au bas de manche
SL = dict(rc=(.44, .225), rn=(1, .08), rA=.255, rB=.15, cc=(.70, -.005), cn=(.86, -.5), cA=.135, cB=.095)
def sleeve_frame(v, sgn, ext=0):
    n = Vector((lerp(SL['rn'][0], SL['cn'][0], v), lerp(SL['rn'][1], SL['cn'][1], v), 0)).normalized()
    c = Vector((sgn * lerp(SL['rc'][0], SL['cc'][0], v), lerp(SL['rc'][1], SL['cc'][1], v), 0))
    return c, Vector((-n.y * sgn, n.x, 0)), lerp(SL['rA'], SL['cA'], v), lerp(SL['rB'], SL['cB'], v), Vector((n.x * sgn, n.y, 0))
def sleeve_ring(v, sgn, n, k=1):
    c, e1, A, B, _ = sleeve_frame(v, sgn)
    return [P(*(c + e1 * (A * k * math.cos(t)) + Vector((0, 0, B * k * math.sin(t))))) for t in (j / n * 2 * math.pi for j in range(n))]

def solid(name, rings):   # anneaux → volume fermé (quads + bouchons)
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in r] for r in rings]; n = len(rings[0])
    for i in range(len(vs) - 1):
        for j in range(n): bm.faces.new((vs[i][j], vs[i][(j+1) % n], vs[i+1][(j+1) % n], vs[i+1][j]))
    bm.faces.new(list(reversed(vs[0]))); bm.faces.new(vs[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob

def apply_all(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        with bpy.context.temp_override(object=ob, active_object=ob): bpy.ops.object.modifier_apply(modifier=m.name)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- 1. Forme de départ : torse + manches, fusionnés puis remaillés régulièrement ----------
tee = solid('Tshirt', [torso_ring(i / 90, 96) for i in range(91)])
for sgn in (1, -1):
    sl = solid(f'Manche{sgn}', [sleeve_ring(i / 30, sgn, 64) for i in range(31)])
    mod = tee.modifiers.new('Union', 'BOOLEAN'); mod.operation = 'UNION'; mod.solver = 'EXACT'; mod.object = sl
    apply_all(tee); bpy.data.objects.remove(sl)
tee.data.remesh_voxel_size = VOXEL
with bpy.context.temp_override(object=tee, active_object=tee): bpy.ops.object.voxel_remesh()

# Ouvertures : bas, encolure, bas de manches (on enlève les bouchons, on recale les bords)
bm = bmesh.new(); bm.from_mesh(tee.data); bm.faces.ensure_lookup_table()
hem_z = HEM * S
neck_back_z = TOP * S
cuffs = []
for sgn in (1, -1):
    c, e1, A, B, n = sleeve_frame(1, sgn)
    cuffs.append((P(*c), P(*n) - P(0, 0, 0)))
def is_cap(f):
    m, nr = f.calc_center_median(), f.normal
    if nr.z < -.6 and m.z < hem_z + .02: return True
    if nr.z > .45 and m.z > (TOP - .12) * S and (m.x / (NECK_A * S)) ** 2 + (m.y / (NECK_B * S)) ** 2 < 1.02: return True
    for cc, cn in cuffs:
        nn = cn.normalized(); d = (m - cc).dot(nn)
        if nr.dot(nn) > .6 and d > -.012 and (m - cc - nn * d).length < SL['cA'] * S * 1.4: return True   # seulement le bout de la manche, pas le flanc
    return False
bmesh.ops.delete(bm, geom=[f for f in bm.faces if is_cap(f)], context='FACES')
# garde le plus gros morceau (enlève les miettes éventuelles)
bm.verts.ensure_lookup_table()
seen, best = set(), []
for v0 in bm.verts:
    if v0 in seen: continue
    comp, stack = [], [v0]; seen.add(v0)
    while stack:
        v = stack.pop(); comp.append(v)
        for e in v.link_edges:
            o = e.other_vert(v)
            if o not in seen: seen.add(o); stack.append(o)
    if len(comp) > len(best): best = comp
keep = set(best); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v not in keep], context='VERTS')
# bords nets : on lisse les bords (sinon dents de scie du remaillage), puis on aplatit l'ourlet et les bas de manches
def smooth_boundary(bm, it):
    for _ in range(it):
        new = {}
        for v in bm.verts:
            if not v.is_boundary: continue
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) == 2: new[v] = (v.co * 2 + nb[0].co + nb[1].co) / 4
        for v, co in new.items(): v.co = co
smooth_boundary(bm, 25)
for v in bm.verts:
    if not v.is_boundary: continue
    if v.co.z < hem_z + .03: v.co.z = hem_z
    for cc, cn in cuffs:
        nn = cn.normalized(); d = (v.co - cc).dot(nn)
        if abs(d) < .03 and (v.co - cc).length < .12: v.co -= nn * d
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(tee.data); bm.free()

# ---------- 2. Mannequin invisible (le tissu se pose dessus) ----------
def body_ring(v, n):
    y0 = curve(TK, v)[0]
    kx = lerp(.985, .97, sstep(-.3, .45, y0)); kz = lerp(.9, .9, sstep(-.3, .45, y0))   # un peu plus étroit en bas : le t-shirt tombe droit, avec quelques plis
    return torso_ring(v, n, kx, kz)
body = solid('Mannequin', [body_ring(i / 60, 64) for i in range(int(.985 * 60) + 1)])
arms = []
for sgn in (1, -1):
    rings = [sleeve_ring(i / 24, sgn, 32, .88) for i in range(25)]   # bras presque aussi large que la manche : elle garde son volume
    # le bras continue un peu au-delà de la manche
    c, e1, A, B, n = sleeve_frame(1, sgn)
    rings.append([p + (P(*n) - P(0, 0, 0)) * .12 for p in rings[-1]])
    arms.append(solid(f'Bras{sgn}', rings))
for ob in [body] + arms:
    ob.modifiers.new('Collision', 'COLLISION'); ob.collision.thickness_outer = .004; ob.collision.cloth_friction = 8
    ob.hide_render = True

# ---------- Simulation du tissu (préréglage coton) ----------
cl = tee.modifiers.new('Cloth', 'CLOTH'); st = cl.settings
st.quality = 8; st.mass = .3; st.air_damping = 1
st.tension_stiffness = st.compression_stiffness = 15; st.shear_stiffness = 15; st.bending_stiffness = .5
st.tension_damping = st.compression_damping = st.shear_damping = 5
cl.collision_settings.distance_min = .004; cl.collision_settings.use_self_collision = False
cl.point_cache.frame_start, cl.point_cache.frame_end = 1, FRAMES
scene.frame_start, scene.frame_end = 1, FRAMES
for f in range(1, FRAMES + 1): scene.frame_set(f)
apply_all(tee)
bm = bmesh.new(); bm.from_mesh(tee.data); smooth_boundary(bm, 8); bm.to_mesh(tee.data); bm.free()   # re-lisse les bords après la chute
print('simulation ok', len(tee.data.vertices), 'sommets')

# ---------- 3. Col bord-côte, le long du bord de l'encolure ----------
bm = bmesh.new(); bm.from_mesh(tee.data)
bnd_edges = [e for e in bm.edges if e.is_boundary]
# boucles de bord : on prend celle qui est la plus haute = l'encolure
loops, used = [], set()
for e0 in bnd_edges:
    if e0 in used: continue
    loop = [e0.verts[0]]; v = e0.verts[1]; used.add(e0); prev = e0
    while v != loop[0]:
        loop.append(v)
        nxt = [e for e in v.link_edges if e.is_boundary and e is not prev and e not in used]
        if not nxt: break
        prev = nxt[0]; used.add(prev); v = prev.other_vert(v)
    loops.append([x.co.copy() for x in loop])
neck = max(loops, key=lambda L: sum(p.z for p in L) / len(L))
bm.free()
# rééchantillonne la boucle régulièrement
def resample(L, n):
    seg = [(L[i], L[(i+1) % len(L)]) for i in range(len(L))]; lens = [(b - a).length for a, b in seg]; tot = sum(lens); out = []; k = 0; acc = 0
    for i in range(n):
        t = i / n * tot
        while acc + lens[k] < t: acc += lens[k]; k += 1
        a, b = seg[k]; out.append(a.lerp(b, (t - acc) / lens[k]))
    return out
neck = resample(neck, 200)
if sum((neck[i].x * neck[(i+1) % 200].y - neck[(i+1) % 200].x * neck[i].y) for i in range(200)) < 0: neck.reverse()
ctr = sum(neck, Vector()) / len(neck)
PROF = [(-.003,-.012),(-.005,.016),(-.004,.04),(0,.047),(.006,.045),(.009,.028),(.01,.004),(.005,-.014)]   # profil arrondi, unités de dessin
def prof(t):   # Catmull-Rom fermé
    n = len(PROF); f = t * n; i = int(f) % n; u = f - int(f)
    p0, p1, p2, p3 = PROF[(i-1) % n], PROF[i], PROF[(i+1) % n], PROF[(i+2) % n]
    return [.5 * (2*b + (-a + c)*u + (2*a - 5*b + 4*c - d)*u*u + (-a + 3*b - 3*c + d)*u*u*u) for a, b, c, d in zip(p0, p1, p2, p3)]
me = bpy.data.meshes.new('Col'); bm = bmesh.new(); R = 24
grid = []
for i in range(R):
    q = prof(i / R); row = []
    for j, p in enumerate(neck):
        out = Vector((p.x - ctr.x, p.y - ctr.y, 0)).normalized()
        front = max(0, -out.y) ** 2   # devant, le col se couche sur la poitrine
        lean = -.12 + .45 * front   # derrière et sur les côtés la bande monte droit et serre un peu ; devant elle se couche
        row.append(bm.verts.new(p + out * (q[0] + q[1] * lean) * S + Vector((0, 0, q[1] * math.sqrt(1 - lean * lean * .5) * S))))
    grid.append(row)
uvl = bm.loops.layers.uv.new('UVMap'); N = len(neck)
for i in range(R):
    for j in range(N):
        f = bm.faces.new((grid[i][j], grid[i][(j+1) % N], grid[(i+1) % R][(j+1) % N], grid[(i+1) % R][j]))
        for lp, (a, b) in zip(f.loops, ((j, i), (j+1, i), (j+1, i+1), (j, i+1))): lp[uvl].uv = (a / N, b / R)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
col = bpy.data.objects.new('Col', me); scene.collection.objects.link(col)

# ---------- Finitions : UV, épaisseur du tissu, lissage ----------
bpy.context.view_layer.objects.active = tee
for ob in bpy.context.view_layer.objects: ob.select_set(False)
tee.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=.003); bpy.ops.object.mode_set(mode='OBJECT')
sm = tee.modifiers.new('Lissage', 'CORRECTIVE_SMOOTH'); sm.iterations = 3; sm.use_only_smooth = True
so = tee.modifiers.new('Epaisseur', 'SOLIDIFY'); so.thickness = .0025; so.offset = -1; so.use_rim = True
apply_all(tee)
for ob in (tee, col):
    for p in ob.data.polygons: p.use_smooth = True

# ---------- Ombres des plis (occlusion ambiante) cuites dans les couleurs de sommet ----------
scene.render.engine = 'CYCLES'; scene.cycles.samples = 48; scene.cycles.device = 'CPU'
if scene.world is None: scene.world = bpy.data.worlds.new('Monde')
scene.world.light_settings.distance = .12
for ob in (tee, col):
    ob.data.materials.append(bpy.data.materials.new('Tissu'))
    a = ob.data.color_attributes.new('AO', 'BYTE_COLOR', 'POINT'); ob.data.color_attributes.active_color = a
for ob in bpy.context.view_layer.objects: ob.select_set(ob in (tee, col))
bpy.context.view_layer.objects.active = tee
scene.render.bake.target = 'VERTEX_COLORS'
bpy.ops.object.bake(type='AO')
for ob in (tee, col):   # adoucit : 0,35 → 1 (le tissu clair diffuse beaucoup la lumière)
    a = ob.data.color_attributes['AO']
    for d in a.data:
        k = .35 + .65 * d.color[0]; d.color = (k, k, k, 1)

# ---------- Export .glb (le mannequin reste dans Blender) ----------
for ob in bpy.context.view_layer.objects: ob.select_set(ob in (tee, col))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                          export_materials='NONE', export_vertex_color='ACTIVE', export_normals=True, export_texcoords=True)
print('export ok', OUT)

# ---------- Aperçu de face pour comparer avec la photo ----------
if PREVIEW:
    for ob in (body, *arms): ob.hide_render = True
    m = bpy.data.materials.new('Ecru'); m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']; bsdf.inputs['Base Color'].default_value = (.86, .82, .74, 1); bsdf.inputs['Roughness'].default_value = .9
    vc = m.node_tree.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'AO'
    mix = m.node_tree.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1
    m.node_tree.links.new(vc.outputs['Color'], mix.inputs['A']); mix.inputs['B'].default_value = (.86, .82, .74, 1)
    m.node_tree.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
    for ob in (tee, col): ob.data.materials[0] = m
    scene.world.use_nodes = True; scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.5, .5, .5, 1)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
    cam.data.lens = 85; cam.location = (0, -3.2, .25); cam.rotation_euler = (math.radians(86), 0, 0)
    sun = bpy.data.objects.new('Soleil', bpy.data.lights.new('Soleil', 'SUN')); sun.data.energy = 2.5; sun.rotation_euler = (math.radians(50), math.radians(-20), math.radians(-25)); scene.collection.objects.link(sun)
    scene.render.resolution_x, scene.render.resolution_y = 700, 640; scene.cycles.samples = 64
    scene.render.filepath = PREVIEW; bpy.ops.render.render(write_still=True)
    print('apercu ok', PREVIEW)
