---
name: cartoon-3d-short
description: Make a ~55-70 s vertical cartoon story short in the "2D characters in a colourful 3D world" style (flat bean-head cartoon cards with ink outlines, painted 3D town/world with black ink lines, saturated sky, depth-of-field backgrounds, gliding cameras, voice narration, synthesized SFX + march-style music), rendered with three.js inside Remotion. Proven on "The Bridge That Fell for a Song" (2026-10-31). Use when the user asks for another video "like the bridge video", "like the soldiers/bridge short", "in that cartoon 3D style", a history/science story short with cartoon characters in 3D, or says "use the cartoon short skill".
---

# Cartoon 3D story short (three.js + Remotion)

Proven example: **The Bridge That Fell for a Song**. It is an original 67 s short about the 1831 Broughton bridge and 74 soldiers marching in step.
- Core Reusable Engine: `src/engine/` (universal textures, modular 3.5 HH characters, architectural room & prop sets, camera director, post-processing stack).
- Video compositions: `src/videos/<name>/`.
- Reference study: `references/` (STYLE_BIBLE.md, reports/*.md, frames/, sheets/).

The style reference is a channel studied privately (`references/`: STYLE_BIBLE.md, reports/*.md, frames/).
- Those videos are private study material. Never upload, publish or send them.
- Never copy their scripts, characters or shots. Story, characters and voice are always OUR OWN.
- Never say the channel's name in a voice-over or description.

User rules that apply:
- Subtitles: Word-by-word kinetic pop locked to y = 0.67 H (white fill, 6px black stroke, 3-frame scale punch).
- English only.
- Voice: one steady tone (~3.7 words/s).
- Jokes are researched real facts.
- Standard mix: music +3 dB, SFX -6 dB, voice unchanged (-14 LUFS integrated).
- Final export 2K vertical: 1440x2560, `--scale 1.3333` (or distributed 20-runner GitHub Actions).

---

## 1. Dual Construction Architecture

To prevent "shortage of materials" or accidental fallback to crude untextured boxes, all shorts follow this two-tier system:

### Tier 1: The Shared Engine (`src/engine/`)
Always import from `src/engine/` for battle-tested, pixel-accurate rendering:
- **`src/engine/textures.ts`**: Procedural Canvas2D materials (`planks()`, `beam()`, `brick()`, `stone()`, `metalPlates()`, `paper()`, `tiles()`, `glass()`, `grass()`) with built-in 3–5 px line width, HSL color jitter, and Lab $L^* \ge 72$.
- **`src/engine/characters.ts`**: Universal $3.5\text{ HH}$ character rig with superellipse heads, modular hair, tailored outfits (vests with buttons, suits, overalls, coats), 14 expressions, and contact shadow blobs.
- **`src/engine/environments.ts`**: High-level set builders (`buildRoom()`, `buildWorkbench()`, `buildShelves()`, `buildIntaglioPress()`, volumetric window sunbeams).
- **`src/engine/camera.ts`**: Camera director enforcing strict distance constraints (min 2.0m for CU, 2.8m for MS) and continuous creeping push-ins.
- **`src/engine/post.ts` / `ink.ts` / `lensblur.ts` / `grade.ts`**: Multi-pass postprocessing (silhouette & crease ink, autofocus depth of field, bloom, neutral tone mapping, color grading).

### Tier 2: The Pixel-Level Style Protocol (For Authoring Novel Assets)
When a short requires novel 3D geometry (e.g. a steam train, a roller coaster track, a hydraulic press, an easel), you MUST follow these exact measured rules from `references/reports/`:

1. **Surfaces & Textures (`reports/textures.md`):**
   - **Never use bare flat hex colors:** Flat `THREE.MeshStandardMaterial({ color })` without a procedural texture is strictly prohibited.
   - **Seam & Mortar Line Width:** All painted joints, board cuts, or mortar lines must measure **3–5 px at 1080p** (FWHM), with a 1–2 px ramp.
   - **Lightness Jitter (`jit()`):** Every board, brick, or tile must apply $\pm 8-10\%$ HSL lightness jitter so surfaces look organically hand-painted.
   - **Luminance & Saturation:** Lit surfaces must have CIE Lab $L^* \ge 72$ (day) and Chroma $C^* \ge 50$. Never muddy, never plastic.

2. **Characters & Anatomy (`reports/characters.md`):**
   - **Head Contour:** Dual-exponent superellipse ($n_{top} = 1.70$, $n_{bot} = 2.26$, egg chin $-0.125$, gaze asymmetry $+0.10$).
   - **Plum Outline:** Ink `#241726`, weighted $\times 3$ thicker on the shadow side ($5.0\% W$ width).
   - **Proportions:** Exactly $3.5\text{ HH}$ total height ($1000\text{ units} = 2.16\text{m}$). Legs $1.4\text{ HH}$, stick limbs $w=12$, ink-dot hands ($r=12$).
   - **Costume Detail:** Characters must have hair (comb-over, curls, sideburns, beards), headwear (caps, bowler hats), collars, buttons (`#d9dde0`), pocket seams, or ties. Monolithic single-color rectangles are forbidden.
   - **Grounding:** Characters MUST cast a multiply contact shadow blob (`CARD_K` blob material) on the ground under their feet.

3. **Cinematic Camera Grammar (`reports/motion.md` & `depth.md`):**
   - **Strict Distance Bounds:**
     - Close-Up (CU): Distance $2.0\text{m} - 2.4\text{m}$ (FOV $35^\circ$). Forehead crown must maintain $\ge 120\text{ px}$ frame margin.
     - Medium Shot (MS): Distance $2.8\text{m} - 3.8\text{m}$.
     - Wide Shot (WS): Distance $4.2\text{m} - 6.5\text{m}$.
     - *Hard Rule:* Camera distance $< 1.8\text{m}$ is strictly forbidden.
   - **Kinematics:**
     - Ease-out impulse bursts for cuts and glides (peak speed frame 1, decaying over 8–10 frames).
     - Every hold MUST push in at $0.20\%/\text{f}$ to prevent frozen frame alerts.
     - Dramatic $4.0^\circ - 4.6^\circ$ Dutch roll on tension beats.
   - **Subtitle Safe Zone:** Subtitles pop at $y = 0.67 H$. The camera target must be elevated ($y \approx 1.25\text{m} - 1.45\text{m}$) so faces and props are never blocked.

---

## 2. Production Pipeline

1. **Topic and facts:** Pick one surprising physical true story with cause-and-effect and a simple everyday analogy.
2. **Script (~3.7 words/s, 55-70 s):** Hook -> Setting -> Escalation -> Snap -> Deadpan double line -> Explanation -> Consequence -> Callback twist.
3. **Voice & Timings:** Generate `voice.wav` and `words.json` (word-by-word timestamps). Master mix to -14 LUFS.
4. **Shot Plan (`story.ts`):** Define camera shots using `src/engine/camera.ts` with strict distance bounds and creeping holds.
5. **Set & World (`world.ts`):** Build rooms and scenes using `src/engine/environments.ts` and `src/engine/textures.ts`. Add window light shafts, shelves with props, and machinery.
6. **Cast & Characters:** Spawn actors using `src/engine/characters.ts` with tailored costumes, hair, expressions, and contact shadow blobs.
7. **Render & QA:** Render stills (`scripts/bridge-stills.mjs`), verify against reference contact sheets, then render the final vertical video (locally or via 20-runner GitHub Actions).
