import json, sys
OUT = sys.argv[1]
BEATS = [(0.0,2.5),(2.5,5.4),(5.4,7.0),(7.0,9.7),(9.7,11.2),(11.2,13.9),(13.9,15.2),(15.2,17.2),(17.2,19.2),(19.2,21.0),
 (21.0,23.1),(23.1,26.3),(26.3,28.2),(28.2,31.9),(31.9,33.9),(33.9,35.3),(35.3,37.2),(37.2,39.9),(39.9,41.1),(41.1,44.0),
 (44.0,46.0),(46.0,48.2),(48.2,50.7),(50.7,52.1),(52.1,53.8),(53.8,56.5),(56.5,57.5),(57.5,59.8),(59.8,62.9)]
LINES = ["He bent the roller coaster's loop out of shape.","You see, it's the first ride ever to go upside down,","and it cost him everything.",
 "So of course, his rival copies it bolt for bolt.","But the night before opening,","his test dummy comes back crushed like a soda can,",
 "but he can't miss the opening,","so he grabs a hammer and beats the bottom","into a long, lazy curve.","Does he know what he's doing? Not really.",
 "His rival laughs, then sneaks in,","and cranks the sides together until the loop is tall and skinny.","So the first cart will snap like a twig.",
 "The next morning, the town lines up at the rival's perfect circle,","and the rival climbs in front to show off.","The owner climbs into his,",
 "and as his cart tips over the first hill,","he finally sees the tall, skinny loop ahead.","But it's too late.",
 "You see, a car can creep around a hairpin turn at five,","but take it at 60, and it flips.","A cart is fastest at the bottom of a loop,",
 "and a perfect circle puts a hairpin right there,","which is what crushed the dummy.","But his hammer made the bottom gentle,",
 "and the rival's squeeze moved the hairpin up top,","where the cart is crawling.","So he floats over without a scratch.",
 "Just as the rival's cart hits the bottom of that perfect circle."]
def A(a, off=None): d={"anchor":a}; (d.update(offset=off) if off else None); return d
def F(who, off): return {"follow":who,"offset":off}
def cam(pos, look, lens=35, pos2=None, look2=None, lens2=None, ease="inout", roll=0):
    c={"pos":pos,"look":look,"lens":lens,"ease":ease,"roll":roll}
    if pos2: c["pos2"]=pos2
    if look2: c["look2"]=look2
    if lens2: c["lens2"]=lens2
    return c
def ch(a, **kw): d={"anchor":a}; d.update(kw); return d
def pr(a, **kw): d={"anchor":a}; d.update(kw); return d
NIGHT, DAY = "night_workshop", "morning_fair"
WS_LOOP = {"loop_owner": pr("ws.track_stand")}
HAM = {"hammer": pr("ws.bench_hammer", rot_deg=90)}
CARTD = {"cart_owner": pr("ws.cart_spot"), "dummy": pr("ws.dummy_in_cart")}
S = {}  # beat index -> (set, mood, stage, cam, extra)
def shot(i, st, mood, stage, c, **extra): S[i]=dict(set=st, mood=mood, stage=stage, cam=c, **extra)
shot(1,"workshop_night",NIGHT,{"props":{**WS_LOOP,"hammer":pr("ws.bench_hammer",rot_deg=90)},"chars":{"builder":ch("ws.builder_work")}},cam([-1,-17,4.2],[-1,0,3.0],32,[-1,-15.5,3.8],[-0.5,0,2.8]))
shot(2,"workshop_night",NIGHT,{"props":{**WS_LOOP,**HAM},"chars":{"builder":ch("ws.builder_work")}},cam([-5,-15,3.2],[-1.5,0,3.0],40,[-1.5,-12.5,4.0],[0.5,0,3.6]))
shot(3,"workshop_night",NIGHT,{"props":{**WS_LOOP},"chars":{"builder":ch("ws.builder_idle")}},cam([-4.2,-9.5,2.7],[-4.2,-1.8,2.5],50,[-4.2,-8.0,2.8],[-4.2,-1.8,2.6]))
shot(4,"fairground_dawn",DAY,{"props":{"loop_rival":pr("fg.rival_loop")},"chars":{"rival":ch("fg.rival_front")}},cam([-12,-17,4],[-7,3,3.5],35,[-10,-15.5,3.6],[-8,3,3.5]))
shot(5,"workshop_night",NIGHT,{"props":{**WS_LOOP,**CARTD},"chars":{"builder":ch("ws.builder_bench")}},cam([-2,-20,5],[-2,0,3.6],28,[-3.5,-17.5,4.2],[-4,0,3.0]))
shot(6,"workshop_night",NIGHT,{"props":{**CARTD},"chars":{"builder":ch("ws.builder_bench",offset=[1.4,0,0])}},cam([-6.2,-12,2.4],[-6.2,-0.8,1.8],40,[-6.0,-10.5,2.2],[-6.0,-0.8,1.5]))
shot(7,"workshop_night",NIGHT,{"props":{**WS_LOOP,**CARTD},"chars":{"builder":ch("ws.builder_idle")}},cam([-4.2,-12,2.8],[-4.2,-1.8,2.4],45,[-4.2,-10.5,2.7],[-4.2,-1.8,2.6]))
shot(8,"workshop_night",NIGHT,{"props":{**WS_LOOP,**HAM},"chars":{"builder":ch("ws.builder_work")}},cam([0,-15,3.2],[0,0,2.2],35,[0.3,-14,3.0],[0.3,0,1.8]))
shot(9,"workshop_night",NIGHT,{"props":{**WS_LOOP,**HAM},"chars":{"builder":ch("ws.builder_work")}},cam([0,-9.5,1.8],[0.3,0,1.0],45,[0.5,-8.5,1.5],[0.4,0,0.8]))
shot(10,"workshop_night",NIGHT,{"props":{**WS_LOOP,**HAM},"chars":{"builder":ch("ws.builder_work")}},cam([-3,-11,2.8],[-2.6,-1.6,2.4],45,[-2.0,-10,2.6],[-2.2,-1.6,2.4]))
TB={"turnbuckle":pr("ws.crank")}
shot(11,"workshop_night",NIGHT,{"props":{**WS_LOOP,**TB},"chars":{"rival":ch("ws.rival_door",face=-1,move={"to":"ws.rival_mid","t0":22.0,"t1":23.0,"hop":0.12})}},cam([6,-15,3.6],[7,0,2.8],35,[5,-14,3.4],[5.5,0,2.8]))
shot(12,"workshop_night",NIGHT,{"props":{**WS_LOOP,**TB},"chars":{"rival":ch("ws.rival_crank",face=-1)}},cam([3,-14,3.2],[3,0,2.4],35,[3.5,-12,3.4],[3.5,0,2.6]))
shot(13,"workshop_night",NIGHT,{"props":{**WS_LOOP,**TB,"cart_owner":pr("ws.cart_spot")},"chars":{"rival":ch("ws.rival_crank",face=-1)}},cam([0,-17,3],[1.5,0,3],30,[0,-17.5,5],[1.5,0,5.5]))
shot(14,"fairground_dawn",DAY,{"props":{"loop_rival":pr("fg.rival_loop"),"loop_owner":pr("fg.owner_loop")},"chars":{"rival":ch("fg.rival_front")}},cam([-24,-22,6],[-12,3,4],28,[-8,-22,6],[-6,3,4]))
RS=dict(scale=0.7)
shot(15,"fairground_dawn",DAY,{"props":{"loop_rival":pr("fg.rival_loop"),"cart_rival":{"track":"loop_rival"}},"chars":{"rival":ch("fg.rival_stairs",**RS)}},cam([-20,-12,6],[-18.3,3,4.5],40,[-18.5,-11,5.8],[-18.3,3,4.6]))
shot(16,"fairground_dawn",DAY,{"props":{"loop_owner":pr("fg.owner_loop"),"cart_owner":{"track":"loop_owner"}},"chars":{"builder":ch("fg.owner_gate",**RS)}},cam([2,-14,5.5],[-0.3,7,4.5],40,[1,-13,5.4],[-0.4,7,4.6]))
CCO={"props":{"loop_owner":pr("cc.owner_loop"),"cart_owner":{"track":"loop_owner"}},"chars":{"builder":ch("cc.owner_bottom",**RS)}}
shot(17,"coaster_climax",DAY,CCO,cam(F("cart_owner",[-3,-9,1.5]),F("cart_owner",[1.5,0,0.3]),40))
shot(18,"coaster_climax",DAY,CCO,cam(F("cart_owner",[-3,-11,1.0]),F("cart_owner",[6,0,-1.0]),38))
shot(19,"coaster_climax",DAY,CCO,cam(F("cart_owner",[0.5,-6,1.0]),F("cart_owner",[0.5,0,0.7]),45,F("cart_owner",[0.5,-5,0.9]),F("cart_owner",[0.5,0,0.7])))
CD=lambda lp:{"props":{"loop_owner":pr("cc.owner_loop"),"cart_demo":{"track":"loop_owner"}}}
shot(20,"coaster_climax",DAY,CD(0),cam(F("cart_demo",[0,-9,0.5]),F("cart_demo",[0,0,0]),42))
shot(21,"coaster_climax",DAY,CD(0),cam(F("cart_demo",[-1,-8,0.5]),F("cart_demo",[1,0,0]),40))
shot(22,"coaster_climax",DAY,{"props":{"loop_rival":pr("cc.rival_loop"),"cart_demo":{"track":"loop_rival"}}},cam(A("cc.rival_loop",[2,-16,3.5]),A("cc.rival_loop",[2,0,3]),30))
shot(23,"coaster_climax",DAY,{"props":{"loop_rival":pr("cc.rival_loop"),"cart_demo":{"track":"loop_rival"}}},cam(A("cc.rival_loop",[1.5,-9,0.8]),A("cc.rival_loop",[1.5,0,1.0]),40,A("cc.rival_loop",[1.2,-8.2,0.8]),A("cc.rival_loop",[1.2,0,1.0])))
shot(24,"workshop_night",NIGHT,{"props":{**CARTD}},cam([-5,-9.5,2.2],[-5,-0.8,1.4],45,[-5,-8.5,2.0],[-5,-0.8,1.3]))
shot(25,"coaster_climax",DAY,CCO,cam(A("cc.owner_loop",[3,-12,1.5]),A("cc.owner_loop",[3,0,1.0]),35))
shot(26,"coaster_climax",DAY,CCO,cam(A("cc.owner_loop",[2.5,-16,2]),A("cc.owner_loop",[2.5,0,2.5]),28,A("cc.owner_loop",[2.5,-19,5]),A("cc.owner_loop",[2.5,0,6.0])))
shot(27,"coaster_climax",DAY,CCO,cam(F("cart_owner",[0,-10.5,-0.5]),F("cart_owner",[0,0,-0.5]),36))
shot(28,"coaster_climax",DAY,CCO,cam(F("cart_owner",[-3,-11,0]),F("cart_owner",[0.5,0,0]),38,F("cart_owner",[-2,-9,-0.5]),F("cart_owner",[1.5,0,-1.0])))
shot(29,"coaster_climax",DAY,{"props":{"loop_rival":pr("cc.rival_loop"),"cart_rival":{"track":"loop_rival"}},"chars":{"rival":ch("cc.rival_bottom",**RS)}},cam(A("cc.rival_loop",[2,-13,1.5]),A("cc.rival_loop",[1,0,1.2]),35,A("cc.rival_loop",[1.5,-9,1.2]),A("cc.rival_loop",[1.2,0,1.0])))

# ---- 9:16 portrait cameras (sensor_fit HORIZONTAL, 22-35 mm): high-angle tilt-downs on the workshop floor,
#      worm's-eye tilt-ups through the loops, tall stacked compositions.  Min 2.5 m to every foreground occluder.
RL=lambda o: A("cc.rival_loop",o); OL=lambda o: A("cc.owner_loop",o)
CAMS={
 1:cam([-1,-8,10],[-1,0,5.5],26,[-1,-9,8],[-1,-1.5,1.0]),
 2:cam([-2,-10.5,6.5],[-1.5,0,3.5],30,[-1,-8.5,5],[0,0,3.8]),
 3:cam([-4.2,-7,3.0],[-4.2,-1.8,2.5],40,[-4.2,-6.2,3.2],[-4.2,-1.8,2.6]),
 4:cam([-12,-11,3.5],[-9,3,4.5],28,[-11,-10,3.2],[-9,3,5.0]),
 5:cam([-2,-14,9],[-2,0,2.5],24,[-3,-12,7.5],[-4,0,2.2]),
 6:cam([-6.2,-9,6.5],[-6.2,-0.8,1.2],30,[-6.0,-8,5.5],[-6.0,-0.8,1.0]),
 7:cam([-4.2,-9,5],[-4.2,-1.8,2.0],35,[-4.2,-7.5,4],[-4.2,-1.8,2.2]),
 8:cam([0.5,-8,0.7],[1.5,0,3.2],28,[1.5,-7.5,0.7],[2.0,0,3.4]),
 9:cam([0.2,-8,7],[0.3,0,0.4],35,[0.2,-7.5,5.5],[0.4,0,0.2]),
 10:cam([-2.6,-8,5],[-2.6,-1.6,2.2],35,[-2.2,-7,4.2],[-2.4,-1.6,2.2]),
 11:cam([9,-10,5.5],[9.5,0,2],28,[8,-9,4.5],[8.5,0,2.2]),
 12:cam([3.5,-8.5,4],[3.5,0,2.2],28,[4,-8,3],[4,0,2.4]),
 13:cam([1,-8,0.6],[2.5,0,4.5],24,[1,-8,0.6],[2.5,0,6.8]),
 14:cam([-24,-16,9],[-21,0,3],24,[-12,-16,8],[-9,3,4]),
 15:cam([-19,-9,5.5],[-18.3,3,4.2],28,[-18.5,-8,5.0],[-18.3,3,4.3]),
 16:cam([1.5,-9,6],[-0.3,7,4],28,[1,-8.5,5.5],[-0.4,7,4.2]),
 17:cam(F("cart_owner",[-3,-9,1.5]),F("cart_owner",[1.5,0,0.3]),28),
 18:cam(F("cart_owner",[-3,-10,3]),F("cart_owner",[5,0,-2]),24),
 19:cam(F("cart_owner",[0.5,-8,1.2]),F("cart_owner",[0.5,0,0.7]),36,F("cart_owner",[0.5,-7.2,1.0]),F("cart_owner",[0.5,0,0.7])),
 20:cam(F("cart_demo",[0,-8,-1.5]),F("cart_demo",[0,0,1.5]),28),
 21:cam(F("cart_demo",[-1,-8,-1.5]),F("cart_demo",[1,0,1.5]),26),
 22:cam(RL([0,-8,0.5]),RL([0,0,3.2]),24,RL([0,-7,0.5]),RL([0,0,4.0])),
 23:cam(RL([0.8,-6,0.6]),RL([0.8,0,1.5]),28,RL([0.8,-5.5,0.6]),RL([0.8,0,1.3])),
 24:cam([-5,-8,6.5],[-5,-0.8,1.0],32,[-5,-7,5.5],[-5,-0.8,1.0]),
 25:cam(OL([3,-9,0.6]),OL([3,0,2.2]),26),
 26:cam(OL([2.5,-9,0.5]),OL([2.5,0,2.0]),22,OL([2.5,-9,0.5]),OL([2.7,0,7.0])),
 27:cam(F("cart_owner",[0,-10,-0.5]),F("cart_owner",[0,0,-0.5]),28),
 28:cam(F("cart_owner",[-3,-10,0]),F("cart_owner",[0.5,0,0]),26,F("cart_owner",[-2,-9,-0.5]),F("cart_owner",[1.5,0,-1.0])),
 29:cam(RL([1.5,-8,0.6]),RL([1.0,0,1.5]),24,RL([1.2,-6.5,0.6]),RL([1.0,0,1.3])),
}
for k,v in CAMS.items(): S[k]["cam"]=v
shots=[]
for i,(t0,t1) in enumerate(BEATS,1):
    d=S[i]; shots.append({"id":"shot_%02d"%i,"beat":i,"line":LINES[i-1],"t0":t0,"t1":t1,"f0":round(t0*30),"f1":round(t1*30),
        "set":d["set"],"mood":d["mood"],"stage":d["stage"],"cam":d["cam"]})
json.dump({"fps":30,"total_frames":1887,"render":{"res":[1080,1920],"sensor_fit":"HORIZONTAL","min_occluder_clearance_m":2.5},"shots":shots},open(OUT+"/shots.json","w"),indent=1)

# ---------------------------------------------------------------- acting
ev=[]
def E(verb, **kw): ev.append(dict(verb=verb, **kw))
def hold(actor,t0,t1,hands=None,root=None,verb="hold",**kw):
    d=dict(actor=actor,t0=t0,t1=t1,**kw)
    if hands: d["hands"]=hands
    if root: d["root"]=root
    E(verb,**d)
HAMH={"R":["hammer","grip_main"],"L":["hammer","grip_twohand"]}
BAR={"R":["%s","bar"],"L":["%s","bar"]}
# ---- builder with hammer: teaser (beats 1-2) + the real beating (beats 8-10)
hold("builder",0.1,5.4,HAMH,id="teaser_grip")
for T,first in ((1.1,True),(2.0,False)):
    keys=[[T-0.75,0.0],[T-0.35,0.25]] if first else []
    keys+=[[T-0.12,0.25],[T,1.0,"in"],[T+0.35,0.25,"out"]]
    E("operate",id="teaser_swing_%.1f"%T,actor="builder",prop="hammer",channel="swing_stroke",keys=keys)
E("operate",id="teaser_lower",actor="builder",prop="hammer",channel="swing_stroke",keys=[[2.6,0.25],[3.2,0.0]])
E("operate",id="teaser_bend1",actor="builder",via="hammer",prop="loop_owner",channel="bend_bottom",keys=[[1.1,None],[1.22,0.25,"out"]])
E("operate",id="teaser_bend2",actor="builder",via="hammer",prop="loop_owner",channel="bend_bottom",keys=[[2.0,None],[2.12,0.5,"out"]])
E("operate",id="cut_reset_loop",prop="loop_owner",channel="bend_bottom",keys=[[7.0,0.0]])
hold("builder",15.3,21.0,HAMH,id="hammer_grip")
STR=[16.25,17.05,17.80,18.45,19.00]
for n,T in enumerate(STR):
    keys=[[T-0.75,0.0],[T-0.35,0.25]] if n==0 else []
    keys+=[[T-0.12,0.25],[T,1.0,"in"],[T+0.35,0.25,"out"]]
    E("operate",id="swing_%d"%n,actor="builder",prop="hammer",channel="swing_stroke",keys=keys)
    E("operate",id="bend_%d"%n,actor="builder",via="hammer",prop="loop_owner",channel="bend_bottom",keys=[[T,None],[T+0.12,0.2*(n+1),"out"]])
    E("impact",id="strike_%d"%n,actor="builder",t=T,at=["loop_owner","strike_spot"],kinds=["sparks"],strength=1.0,shake=0.12)
for T in (1.1,2.0): E("impact",id="teaser_hit_%.1f"%T,actor="builder",t=T,at=["loop_owner","strike_spot"],kinds=["sparks"],strength=1.0,shake=0.10)
E("operate",id="hammer_lower",actor="builder",prop="hammer",channel="swing_stroke",keys=[[19.55,0.25],[20.2,0.0]])
# ---- dummy
E("operate",id="dummy_crush",prop="dummy",channel="crush_progress",keys=[[11.9,0.0],[12.35,1.0,"in"]])
E("impact",id="dummy_dust",t=12.35,at=["dummy","seat_hip"],kinds=["dust"],strength=1.0,shake=0.12)
E("operate",id="dummy_crush_replay",prop="dummy",channel="crush_progress",keys=[[50.7,0.0],[51.2,1.0,"in"]])
E("impact",id="dummy_dust2",t=51.2,at=["dummy","seat_hip"],kinds=["dust","sparks"],strength=1.0,shake=0.12)
# ---- rival cranks the turnbuckle (loop squeeze is derived from crank_angle)
hold("rival",23.2,26.3,{"R":["turnbuckle","grip_handle"],"L":["turnbuckle","grip_hub"]},id="crank_grip",verb="clasp")
E("operate",id="crank_turns",actor="rival",prop="turnbuckle",channel="crank_angle",keys=[[23.4,0.0],[26.0,1080.0]])
E("impact",id="twig_snap",t=27.7,at=["cart_owner","seat"],kinds=["dust","sparks"],strength=0.8,shake=0.15)
# ---- hands clasped / wringing (poses)
hold("rival",7.0,9.7,{"R":{"local":[0.30,1.55]},"L":{"local":[0.30,1.55]}},verb="clasp",id="rival_smug_clasp")
hold("builder",13.9,15.1,{"R":{"local":[0.25,1.55]},"L":{"local":[0.25,1.55]}},verb="clasp",id="builder_wring")
# ---- riders
def ride(actor,cart,t0,t1,blend):
    hold(actor,t0,t1,root=[cart,"seat"],id=actor+"_mount",blend=blend)
    hold(actor,t0,t1,{"R":[cart,"bar"],"L":[cart,"bar"]},verb="clasp",id=actor+"_bar",blend=blend+0.2)
ride("rival","cart_rival",31.9,63.6,0.6)
ride("builder","cart_owner",34.0,63.6,0.6)
# ---- cart physics (screen-time ride); markers resolve against the bound track's current shape
E("operate",id="rival_cart_a",prop="cart_rival",channel="track_progress",keys=[[31.9,"@lift_start"],[35.3,"@lift_start"],[37.0,"@crest"],[41.0,"@pre_loop","in"]])
E("operate",id="rival_cart_b",prop="cart_rival",channel="track_progress",keys=[[59.6,"@pre_loop"],[61.2,"@loop_in","in"],[62.9,"@loop_q1","out"]])
E("operate",id="owner_cart_a",prop="cart_owner",channel="track_progress",keys=[[33.9,"@lift_start"],[35.3,"@lift_start"],[37.0,"@crest"],[41.0,"@pre_loop","in"]])
E("operate",id="owner_cart_b",prop="cart_owner",channel="track_progress",keys=[[52.1,"@pre_loop"],[53.8,"@loop_q1"],[56.5,"@top_in","out"],[57.5,"@top_out"],[59.8,"@loop_out","in"],[62.9,"@exit"]])
E("operate",id="demo_a",prop="cart_demo",channel="track_progress",keys=[[41.1,"@top_in"],[44.0,"@top_out"]])
E("operate",id="demo_b",prop="cart_demo",channel="track_progress",keys=[[44.0,"@loop_q1"],[45.3,"@top_in","in"]])
E("operate",id="demo_c",prop="cart_demo",channel="track_progress",keys=[[46.0,"@pre_loop"],[47.6,"@loop_in","in"],[48.2,"@loop_q1"]])
E("operate",id="demo_d",prop="cart_demo",channel="track_progress",keys=[[48.2,"@pre_loop"],[49.6,"@loop_in","in"],[50.7,"@loop_q1"]])
E("impact",id="flip",t=45.3,at=["cart_demo","seat"],kinds=["dust","sparks"],strength=1.2,shake=0.2)
E("impact",id="perfect_circle_bottom",t=49.6,at=["loop_rival","bottom"],kinds=["dust"],strength=1.0,shake=0.10)
E("impact",id="finale_crash",t=61.2,at=["loop_rival","bottom"],kinds=["sparks","dust"],strength=1.7,shake=0.35)
# ---- emotions
for a,lst in {"builder":[(0,"determined"),(2.6,"proud"),(5.4,"sad"),(9.7,"neutral"),(12.0,"shocked"),(13.9,"worried"),(14.7,"determined"),(19.4,"worried"),(34.0,"worried"),(37.3,"shocked"),(40.0,"panic"),(52.0,"determined"),(53.2,"proud"),(56.6,"shocked"),(58.2,"laugh")],
              "rival":[(7.0,"smug"),(21.0,"laugh"),(22.2,"smug"),(25.8,"laugh"),(28.3,"proud"),(31.9,"smug"),(60.2,"panic")]}.items():
    for t,e in lst: E("emotion",id="%s_%s_%.1f"%(a,e,t),actor=a,t0=float(t),emotion=e,blend=0.25)
ev.sort(key=lambda e:e.get("t0",e.get("t",0)))
acting={"fps":30,"cast":{"props":{
  "loop_owner":{"type":"loop_track","opts":{"rail":[0.80,0.17,0.14]}},"loop_rival":{"type":"loop_track","opts":{"rail":[0.20,0.45,0.80]}},
  "hammer":{"type":"sledgehammer"},"dummy":{"type":"test_dummy"},"turnbuckle":{"type":"turnbuckle_crank"},
  "cart_owner":{"type":"coaster_cart","opts":{"color":[0.15,0.62,0.66]}},"cart_rival":{"type":"coaster_cart","opts":{"color":[0.95,0.72,0.18]}},
  "cart_demo":{"type":"coaster_cart","opts":{"color":[0.62,0.62,0.66]}}},
  "chars":{"builder":{"style":"builder"},"rival":{"style":"rival"}},
  "links":{"turnbuckle":{"loop":"loop_owner","turns":3.0}}},
  "verbs":["hold","operate","clasp","emotion","impact"],"events":ev}
json.dump(acting,open(OUT+"/acting.json","w"),indent=1)
print(len(shots),"shots",len(ev),"events")
