"""Pure-stdlib validation for the story data and module contracts (no bpy needed)."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    shots_doc = json.loads((ROOT / 'shots.json').read_text(encoding='utf-8'))
    acting_doc = json.loads((ROOT / 'acting.json').read_text(encoding='utf-8'))
    shots = shots_doc['shots']
    events = acting_doc['events']

    assert len(shots) == 29, f'expected 29 shots, got {len(shots)}'
    assert shots[0]['start_frame'] == 1
    assert shots[-1]['end_frame'] == 1887
    for previous, current in zip(shots, shots[1:]):
        assert previous['end_frame'] + 1 == current['start_frame'], 'shot timeline has a gap or overlap'
    total_frames = sum(s['end_frame'] - s['start_frame'] + 1 for s in shots)
    assert total_frames == 1887, total_frames
    assert shots_doc['fps'] == 30
    assert shots_doc['resolution'] == [1080, 1920]

    verbs = {e['verb'] for e in events}
    assert verbs == {'hold', 'clasp', 'operate', 'emotion', 'impact'}, verbs
    valid_props = {'hero_loop', 'rival_loop', 'sledgehammer', 'test_dummy', 'turnbuckle', 'builder_cart', 'rival_cart'}
    valid_actors = {'builder', 'rival'}
    for event in events:
        assert event['actor'] in valid_actors, event
        assert 1 <= event['start_frame'] <= event['end_frame'] <= 1887, event
        if event['verb'] in {'hold', 'clasp', 'operate', 'impact'}:
            assert event['prop'] in valid_props, event
        if event['verb'] in {'hold', 'clasp'}:
            assert event['hand'] in {'L', 'R'} and event.get('socket'), event
        if event['verb'] == 'operate':
            assert event.get('channel') and 'from' in event and 'to' in event, event

    props_ast = ast.parse((ROOT / 'lib' / 'props.py').read_text(encoding='utf-8'))
    classes = {n.name: n for n in props_ast.body if isinstance(n, ast.ClassDef)}
    assert 'PropSpec' in classes
    required = {
        'LoopTrackProp': {'bend_bottom', 'squeeze_sides'},
        'SledgehammerProp': {'swing_stroke'},
        'TestDummyProp': {'crush_progress'},
        'TurnbuckleCrankProp': {'crank_angle'},
        'CoasterCartProp': {'track_progress'},
    }
    for cls_name, channels in required.items():
        cls = classes[cls_name]
        assert any(isinstance(base, ast.Name) and base.id == 'PropSpec' for base in cls.bases), cls_name
        source = ast.get_source_segment((ROOT / 'lib' / 'props.py').read_text(encoding='utf-8'), cls)
        for channel in channels:
            assert channel in source, (cls_name, channel)

    scene_text = (ROOT / 'scene.py').read_text(encoding='utf-8')
    assert 'def apply_frame_actions(f):' in scene_text
    assert 'scene.render.use_compositing = False' in scene_text
    assert "scene.render.engine = 'BLENDER_EEVEE'" in scene_text

    look_text = (ROOT / 'lib' / 'look.py').read_text(encoding='utf-8')
    assert "light_data.energy = max(40.0" in look_text
    assert "500.0" in look_text and "60.0" in look_text and "15.0" in look_text

    print('Project validation passed.')
    print(f'- {len(shots)} contiguous camera beats / {total_frames} frames @ {shots_doc["fps"]} fps')
    print(f'- {len(events)} acting events / verbs: {", ".join(sorted(verbs))}')
    print('- all five hero props inherit PropSpec and declare required channels')
    print('- deterministic frame evaluator, EEVEE 5.x engine id and compositing-off contract present')


if __name__ == '__main__':
    main()
