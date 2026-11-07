import bpy

class CardCharacter:
    def __init__(self, name):
        self.name = name
        self.armature = None
        self.mesh = None
        self.build()
        
    def build(self):
        # Build Flat Plane
        bpy.ops.mesh.primitive_plane_add(size=2)
        self.mesh = bpy.context.active_object
        self.mesh.name = f"{self.name}_mesh"
        self.mesh.rotation_euler[0] = 1.57 # Stand upright
        
        # Build Armature for IK
        bpy.ops.object.armature_add(enter_editmode=True, location=(0,0,0))
        self.armature = bpy.context.active_object
        self.armature.name = f"{self.name}_rig"
        
        amt = self.armature.data
        root = amt.edit_bones.new("Root")
        root.head = (0, 0, 0)
        root.tail = (0, 0, 1)
        
        hand_l = amt.edit_bones.new("Hand.L")
        hand_l.head = (-0.5, 0, 1)
        hand_l.tail = (-0.5, 0, 0.5)
        hand_l.parent = root
        
        hand_r = amt.edit_bones.new("Hand.R")
        hand_r.head = (0.5, 0, 1)
        hand_r.tail = (0.5, 0, 0.5)
        hand_r.parent = root
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # IK targets (Empties)
        self.ik_l = self.create_target(f"{self.name}_IK_L", (-0.5, 0.2, 0.5))
        self.ik_r = self.create_target(f"{self.name}_IK_R", (0.5, 0.2, 0.5))

    def create_target(self, name, loc):
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = 'CUBE'
        empty.empty_display_size = 0.2
        empty.location = loc
        bpy.context.scene.collection.objects.link(empty)
        return empty
        
    def set_ik_target(self, side, prop_socket):
        # Connect character hand to prop socket dynamically
        target = self.ik_l if side == 'L' else self.ik_r
        if prop_socket:
            target.location = prop_socket.matrix_world.translation
