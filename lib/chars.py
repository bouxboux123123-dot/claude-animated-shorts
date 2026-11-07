"""2D-in-3D cartoon card characters with concrete costume geometry and IK sockets."""
import bpy
from mathutils import Vector

from .look import toon_mat, anchor_empty, ink_hull
from .meshlib import box, cylinder, tube_between


class CardRig:
    """Flat silhouette card plus layered costume pieces and hand targets."""

    def __init__(self, name):
        self.name = name
        self._obj = None
        self._ik_sockets = {}
        self.collection = None

    @property
    def obj(self):
        return self._obj

    def create(self, collection):
        self.collection = collection
        self._obj = bpy.data.objects.new(self.name, None)
        collection.objects.link(self._obj)
        return self._obj

    def add(self, obj, location=(0, 0, 0), parent=None):
        if obj.name not in self.collection.objects:
            self.collection.objects.link(obj)
        obj.location = location
        obj.parent = parent or self._obj
        return obj

    def ik_socket(self, name, location=(0, 0, 0)):
        sock = anchor_empty(self.collection, f'{self.name}_{name}_ik', location, self._obj)
        sock.empty_display_type = 'SPHERE'
        sock.empty_display_size = 0.10
        self._ik_sockets[name] = sock
        return sock

    def _card(self, material, size=(1.35, 0.10, 2.6)):
        card = box(f'{self.name}_ink_card', size, material, outline=True)
        self.add(card, (0, 0, 1.55))
        return card

    def create_face(self, skin, hair, hat=None):
        head = cylinder(f'{self.name}_head', 0.48, 0.12, 20, skin)
        head.rotation_euler.x = 1.5708
        self.add(head, (0, -0.09, 2.8))
        hair_obj = cylinder(f'{self.name}_hair', 0.52, 0.10, 20, hair)
        hair_obj.rotation_euler.x = 1.5708
        self.add(hair_obj, (0, -0.14, 3.04))
        if hat:
            self.add(box(f'{self.name}_hat_brim', (0.92, 0.16, 0.14), hat), (0, -0.18, 3.38))
            self.add(cylinder(f'{self.name}_hat_crown', 0.34, 0.30, 16, hat), (0, -0.18, 3.55))
        # Ink-dot eyes read through the flat, painted silhouette.
        eye = toon_mat(f'{self.name}_eye', (0.015, 0.012, 0.025))
        for x in (-0.16, 0.16):
            e = cylinder(f'{self.name}_eye_{x:+.2f}', 0.055, 0.05, 12, eye)
            e.rotation_euler.x = 1.5708
            self.add(e, (x, -0.24, 2.86))

    def set_face_camera(self):
        if not self._obj or bpy.context.scene.camera is None:
            return
        direction = bpy.context.scene.camera.location - self._obj.matrix_world.translation
        self._obj.rotation_euler = direction.to_track_quat('Y', 'Z').to_euler()


class Builder(CardRig):
    """Builder with leather apron, flat cap, articulated hammer hands."""

    def __init__(self):
        super().__init__('builder')

    def create(self, collection):
        super().create(collection)
        skin = toon_mat('builder_skin', (0.92, 0.55, 0.35))
        hair = toon_mat('builder_hair', (0.12, 0.055, 0.025))
        cap = toon_mat('builder_cap', (0.12, 0.18, 0.28))
        apron = toon_mat('builder_apron', (0.50, 0.25, 0.10))
        shirt = toon_mat('builder_shirt', (0.78, 0.78, 0.70))
        self._card(apron, (1.45, 0.10, 2.6))
        self.create_face(skin, hair, cap)
        self.add(box('builder_shirt', (1.22, 0.12, 0.65), shirt), (0, -0.12, 2.05))
        self.add(box('builder_apron_panel', (0.92, 0.14, 1.25), apron), (0, -0.18, 1.48))
        for x in (-0.42, 0.42):
            self.add(tube_between(f'builder_arm_{x:+.2f}', (x, -0.20, 2.0),
                                  (x * 1.65, -0.26, 1.25), 0.11, 8, shirt), (0, 0, 0))
        self.ik_socket('hand_r', (0.70, -0.30, 1.28))
        self.ik_socket('hand_l', (-0.70, -0.30, 1.28))
        self.ik_socket('clav_r', (0.40, -0.20, 2.0))
        self.ik_socket('clav_l', (-0.40, -0.20, 2.0))
        return self._obj


class Rival(CardRig):
    """Rival with sharp suit, bowler, tie, and articulated crank hands."""

    def __init__(self):
        super().__init__('rival')

    def create(self, collection):
        super().create(collection)
        skin = toon_mat('rival_skin', (0.78, 0.38, 0.25))
        hair = toon_mat('rival_hair', (0.035, 0.025, 0.02))
        bowler = toon_mat('rival_bowler', (0.035, 0.045, 0.07))
        suit = toon_mat('rival_suit', (0.07, 0.09, 0.16))
        tie = toon_mat('rival_tie', (0.70, 0.10, 0.10))
        self._card(suit, (1.45, 0.10, 2.6))
        self.create_face(skin, hair, bowler)
        self.add(box('rival_shirt', (0.85, 0.13, 0.55), toon_mat('rival_shirt', (0.88, 0.88, 0.82))), (0, -0.15, 2.05))
        self.add(box('rival_tie', (0.12, 0.16, 0.60), tie), (0, -0.24, 1.85))
        for x in (-0.42, 0.42):
            self.add(tube_between(f'rival_arm_{x:+.2f}', (x, -0.20, 2.0),
                                  (x * 1.65, -0.26, 1.25), 0.11, 8, suit), (0, 0, 0))
        self.ik_socket('hand_r', (0.70, -0.30, 1.28))
        self.ik_socket('hand_l', (-0.70, -0.30, 1.28))
        self.ik_socket('clav_r', (0.40, -0.20, 2.0))
        self.ik_socket('clav_l', (-0.40, -0.20, 2.0))
        return self._obj
