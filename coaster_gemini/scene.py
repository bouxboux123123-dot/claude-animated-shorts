import bpy
import json
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import lib.look
import lib.props
import lib.sets
import lib.chars

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

class StoryDirector:
    def __init__(self):
        # Reset factory
        bpy.ops.wm.read_factory_settings(use_empty=True)
        
        self.shots = load_json(os.path.join(HERE, 'shots.json'))
        self.acting = load_json(os.path.join(HERE, 'acting.json'))
        
        # Look Init
        lib.look.setup_eevee_next()
        
        # Set & Lighting Init
        self.set_reg = lib.sets.SetRegistry()
        self.set_reg.build_workshop_night()
        self.set_reg.build_fairground_dawn()
        self.set_reg.build_coaster_climax()
        self.current_set = None
        
        # Prop Init
        self.props = {
            'loop_track': lib.props.LoopTrackProp("LoopTrack"),
            'sledgehammer': lib.props.SledgehammerProp("SledgeHammer"),
            'test_dummy': lib.props.TestDummyProp("TestDummy"),
            'turnbuckle': lib.props.TurnbuckleCrankProp("Turnbuckle"),
            'coaster_cart': lib.props.CoasterCartProp("BuilderCart"),
            'coaster_cart_rival': lib.props.CoasterCartProp("RivalCart")
        }
        
        # Char Init
        self.chars = {
            'builder': lib.chars.CardCharacter('Builder'),
            'rival': lib.chars.CardCharacter('Rival')
        }
        
        # Camera
        cam_data = bpy.data.cameras.new('Camera')
        cam_data.sensor_fit = 'HORIZONTAL'
        self.camera = bpy.data.objects.new('Camera', cam_data)
        bpy.context.scene.collection.objects.link(self.camera)
        bpy.context.scene.camera = self.camera
        
        # Render resolution (9:16 portrait)
        bpy.context.scene.render.resolution_x = 720
        bpy.context.scene.render.resolution_y = 1280
        bpy.context.scene.render.resolution_percentage = 100
        bpy.context.scene.render.fps = 30
        bpy.context.scene.render.use_compositing = False

    def get_shot_for_frame(self, f):
        for shot in self.shots:
            if shot['start'] <= f < shot['end']:
                return shot
        return self.shots[-1]

    def apply_frame_actions(self, f):
        # 1. Shot / Camera / Set / Lighting context
        shot = self.get_shot_for_frame(f)
        self.camera.location = shot['cam_pos']
        self.camera.rotation_euler = shot['cam_rot']
        
        if self.current_set != shot['set']:
            if 'workshop' in shot['set']:
                self.set_reg.build_workshop_night()
                lib.look.setup_sky_dome('night_workshop')
                lib.look.setup_lighting('night_workshop')
            elif 'dawn' in shot['set'] or 'fairground' in shot['set']:
                self.set_reg.build_fairground_dawn()
                lib.look.setup_sky_dome('morning_fair')
                lib.look.setup_lighting('morning_fair')
            else:
                self.set_reg.build_coaster_climax()
                lib.look.setup_sky_dome('morning_fair')
                lib.look.setup_lighting('morning_fair')
            self.current_set = shot['set']
            
        # 2. Rebuild Prop Transforms deterministically based on action timeline
        active_actions = [a for a in self.acting if a['frame'] <= f]
        
        for act in active_actions:
            target_prop = self.props.get(act.get('target'))
            char = self.chars.get(act.get('char'))
            
            if target_prop and 'channel' in act:
                target_prop.channels[act['channel']] = act['value']
                
            if char and target_prop and 'socket' in act:
                socket = target_prop.sockets.get(act['socket'])
                char.set_ik_target('R', socket)
                
        # 3. Flush updates to geometries/modifiers
        for prop in self.props.values():
            prop.update()

    def render_slice(self, out_dir, start_f, end_f, samples=4):
        os.makedirs(out_dir, exist_ok=True)
        bpy.context.scene.render.filepath = os.path.join(out_dir, "f")
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        
        print(f"=====================================================")
        print(f"[Gemini] Rendering frames {start_f} to {end_f}")
        print(f"=====================================================")
        
        for f in range(start_f, end_f):
            bpy.context.scene.frame_set(f)
            self.apply_frame_actions(f)
            
            out_file = os.path.join(out_dir, f"{f:04d}.png")
            bpy.context.scene.render.filepath = out_file
            bpy.ops.render.render(write_still=True)
            print(f"[Gemini] Rendered frame {f:04d} -> {out_file}")

if __name__ == "__main__":
    director = StoryDirector()
    
    # CLI argument parsing
    if '--' in sys.argv:
        args = sys.argv[sys.argv.index('--') + 1:]
        if len(args) >= 4 and args[0] == 'frames':
            out_dir = os.path.abspath(args[1])
            start_f = int(args[2])
            end_f = int(args[3])
            samples = int(args[4]) if len(args) > 4 else 4
            director.render_slice(out_dir, start_f, end_f, samples)
        else:
            director.render_slice(os.path.abspath("out_frames"), 0, 10, 4)
    else:
        director.render_slice(os.path.abspath("out_frames"), 0, 10, 4)
