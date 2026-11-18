# Prépare le t-shirt « T Shirt » de Garry Smiths (Sketchfab, CC BY 4.0) pour le mockup web :
#   /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P mockup/blender/prepare_tshirt.py -- scene.gltf mockup/tshirt.glb [apercu.png]
# Source : https://sketchfab.com/3d-models/t-shirt-0c2da077451f46c789ebd023cebd6c4e (exporté de CLO3D, 1 million de triangles)
# 1. On regroupe les pièces : Tissu (corps + manches + bandes d'ourlet), Col (bord-côte), Coutures (fils des surpiqûres).
# 2. On allège (décimation) pour passer d'1 million à ~120 000 triangles.
# 3. Ombres des plis cuites dans les couleurs de sommet, recentrage (ourlet à -0,44 m), export .glb compressé (Draco).
import bpy, sys
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = args[0], args[1]
PREVIEW = args[2] if len(args) > 2 else None
HEM_Z = -.44   # même repère que le reste de l'outil : 1 unité three.js = 55 cm, ourlet à -0,8 unité

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == 'MESH']
for o in scene.objects: o.select_set(o in meshes)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')   # garde l'échelle des objets parents du fichier (cm → m)

def group(name, objs, ratio):
    for o in scene.objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = ob.data.name = name
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    while ob.data.materials: ob.data.materials.pop()
    if ratio < 1:
        d = ob.modifiers.new('Allege', 'DECIMATE'); d.ratio = ratio; d.use_collapse_triangulate = True
        with bpy.context.temp_override(object=ob, active_object=ob): bpy.ops.object.modifier_apply(modifier=d.name)
    for p in ob.data.polygons: p.use_smooth = True
    print(name, sum(len(p.vertices) - 2 for p in ob.data.polygons), 'triangles')
    return ob

# les pièces 71 et 29 sont le bord-côte du col ; les « StitchMatShape » sont les fils de couture
stitches = [o for o in meshes if o.name.startswith('StitchMatShape')]
collar = [o for o in meshes if o.name.startswith(('71_', '29_'))]
fabric = [o for o in meshes if o not in stitches and o not in collar]
tissu = group('Tissu', fabric, .3)
col = group('Col', collar, .5)
cout = group('Coutures', stitches, .06)
parts = (tissu, col, cout)

# Recentrage : centre gauche-droite et avant-arrière sur 0, ourlet à HEM_Z
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for v in tissu.data.vertices: mn = Vector(map(min, mn, v.co)); mx = Vector(map(max, mx, v.co))
shift = Vector((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, HEM_Z - mn.z))
for ob in parts: ob.data.transform(__import__('mathutils').Matrix.Translation(shift))
for ob in parts: ob.data.update()
print('taille (m) :', tuple(round(x, 3) for x in (mx - mn)), 'décalage', tuple(round(x, 3) for x in shift))

# Ombres des plis (occlusion ambiante) cuites dans les couleurs de sommet
scene.render.engine = 'CYCLES'; scene.cycles.samples = 48; scene.cycles.device = 'CPU'
if scene.world is None: scene.world = bpy.data.worlds.new('Monde')
scene.world.light_settings.distance = .1
for ob in parts:
    ob.data.materials.append(bpy.data.materials.new(ob.name))
    a = ob.data.color_attributes.new('AO', 'BYTE_COLOR', 'POINT'); ob.data.color_attributes.active_color = a
for o in scene.objects: o.select_set(o in parts)
bpy.context.view_layer.objects.active = tissu
scene.render.bake.target = 'VERTEX_COLORS'
bpy.ops.object.bake(type='AO')
for ob in parts:   # adoucit : 0,4 → 1 (tissu clair, beaucoup de lumière diffuse)
    for d in ob.data.color_attributes['AO'].data:
        k = .4 + .6 * d.color[0]; d.color = (k, k, k, 1)

for o in scene.objects: o.select_set(o in parts)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_yup=True, export_materials='NONE',
                          export_vertex_color='ACTIVE', export_normals=True, export_texcoords=True,
                          export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7,
                          export_draco_position_quantization=14, export_draco_normal_quantization=10, export_draco_texcoord_quantization=12)
print('export ok', OUT)

if PREVIEW:
    import math
    m = bpy.data.materials.new('Ecru'); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']; bsdf.inputs['Roughness'].default_value = .9
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'AO'
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1
    nt.links.new(vc.outputs['Color'], mix.inputs['A']); mix.inputs['B'].default_value = (.86, .82, .74, 1); nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
    for ob in parts: ob.data.materials[0] = m
    scene.world.use_nodes = True; scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.5, .5, .5, 1)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
    cam.data.lens = 85; cam.location = (0, -3, -.05); cam.rotation_euler = (math.radians(88), 0, 0)
    sun = bpy.data.objects.new('Soleil', bpy.data.lights.new('Soleil', 'SUN')); sun.data.energy = 2.5
    sun.rotation_euler = (math.radians(50), math.radians(-20), math.radians(-25)); scene.collection.objects.link(sun)
    scene.render.resolution_x, scene.render.resolution_y = 700, 640; scene.cycles.samples = 64
    scene.render.filepath = PREVIEW; bpy.ops.render.render(write_still=True); print('apercu ok')
