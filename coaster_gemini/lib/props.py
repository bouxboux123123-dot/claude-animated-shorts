import bpy
import math

class PropSpec:
    def __init__(self, name):
        self.name = name
        self.obj = None
        self.sockets = {}
        self.channels = {}
        self.build()
        
    def build(self):
        pass
        
    def add_socket(self, s_name, loc):
        empty = bpy.data.objects.new(f"{self.name}_{s_name}", None)
        empty.empty_display_type = 'SPHERE'
        empty.empty_display_size = 0.2
        empty.location = loc
        empty.parent = self.obj
        bpy.context.scene.collection.objects.link(empty)
        self.sockets[s_name] = empty

class LoopTrackProp(PropSpec):
    def build(self):
        bpy.ops.mesh.primitive_torus_add(major_radius=5, minor_radius=0.5, location=(0,0,5), rotation=(1.57, 0, 0))
        self.obj = bpy.context.active_object
        self.obj.name = self.name
        self.channels = {'bend_bottom': 0.0, 'squeeze_sides': 0.0}
        
    def update(self):
        # Bend morphs the circular scale into clothoid via simple scale mapping
        self.obj.scale[2] = 1.0 + (self.channels['bend_bottom'] * 0.5)
        self.obj.scale[0] = 1.0 - (self.channels['squeeze_sides'] * 0.4)

class SledgehammerProp(PropSpec):
    def build(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2)
        self.obj = bpy.context.active_object
        self.obj.name = self.name
        self.add_socket('grip_main', (0, 0, -0.8))
        self.add_socket('grip_twohand', (0, 0, -0.2))
        self.channels = {'swing_stroke': 0.0}
        
    def update(self):
        self.obj.rotation_euler[0] = self.channels['swing_stroke'] * 3.14

class TestDummyProp(PropSpec):
    def build(self):
        bpy.ops.mesh.primitive_monkey_add(size=1)
        self.obj = bpy.context.active_object
        self.obj.name = self.name
        self.channels = {'crush_progress': 0.0}
        
    def update(self):
        self.obj.scale[2] = 1.0 - (self.channels['crush_progress'] * 0.9)

class TurnbuckleCrankProp(PropSpec):
    def build(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1)
        self.obj = bpy.context.active_object
        self.obj.name = self.name
        self.add_socket('handle', (0.5, 0, 0))
        self.channels = {'crank_angle': 0.0}
        
    def update(self):
        self.obj.rotation_euler[2] = self.channels['crank_angle']

class CoasterCartProp(PropSpec):
    def build(self):
        bpy.ops.mesh.primitive_cube_add(size=1.5)
        self.obj = bpy.context.active_object
        self.obj.name = self.name
        self.channels = {'track_progress': 0.0}
        
    def update(self):
        # Maps 0..1 to circle translation (mock track progress)
        p = self.channels['track_progress'] * math.pi * 2
        self.obj.location = (math.sin(p)*5, 0, 5 - math.cos(p)*5)
