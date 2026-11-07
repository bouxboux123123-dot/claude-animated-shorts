import bpy

class SetRegistry:
    def __init__(self):
        self.anchors = {}
        self.set_objects = {}
        
    def build_workshop_night(self):
        if 'workshop' not in self.set_objects:
            bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,0))
            floor = bpy.context.active_object
            floor.name = "WorkshopFloor"
            self.set_objects['workshop'] = [floor]
            self.anchors['workshop_center'] = (0,0,0)
            self.anchors['track_mount'] = (0,0,0)
        self._set_vis('workshop', True)
        self._set_vis('fairground', False)
        self._set_vis('climax', False)

    def build_fairground_dawn(self):
        if 'fairground' not in self.set_objects:
            bpy.ops.mesh.primitive_plane_add(size=50, location=(0,0,0))
            floor = bpy.context.active_object
            floor.name = "FairgroundFloor"
            self.set_objects['fairground'] = [floor]
            self.anchors['fairground_center'] = (0,0,0)
        self._set_vis('workshop', False)
        self._set_vis('fairground', True)
        self._set_vis('climax', False)

    def build_coaster_climax(self):
        if 'climax' not in self.set_objects:
            bpy.ops.mesh.primitive_plane_add(size=100, location=(0,0,0))
            floor = bpy.context.active_object
            floor.name = "CoasterPlaza"
            self.set_objects['climax'] = [floor]
            self.anchors['climax_cam_anchor'] = (0,-10,2)
        self._set_vis('workshop', False)
        self._set_vis('fairground', False)
        self._set_vis('climax', True)

    def _set_vis(self, key, vis):
        for o in self.set_objects.get(key, []):
            o.hide_render = not vis
            o.hide_viewport = not vis

    def clear(self):
        pass
