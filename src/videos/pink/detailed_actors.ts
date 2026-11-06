import * as THREE from "three";
import { ctex } from "../../engine";

const INK = "#241726";
const WHITE = "#ffffff";
const MOUTH = "#5a1e28";

/**
 * Guard actively painting with roller (Scene 1 & Scene 3)
 */
export function getPaintingGuardTexture(): THREE.CanvasTexture {
  return ctex("tex_actor_guard_painting", 600, 1000, (g) => {
    // 1. Legs (Navy pants)
    g.strokeStyle = INK;
    g.lineWidth = 14;
    g.lineCap = "round";
    // Left leg
    g.beginPath(); g.moveTo(260, 680); g.lineTo(255, 960); g.stroke();
    // Right leg
    g.beginPath(); g.moveTo(340, 680); g.lineTo(345, 960); g.stroke();
    // Shoes
    g.fillStyle = INK;
    g.beginPath(); g.ellipse(250, 965, 18, 10, 0, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.ellipse(350, 965, 18, 10, 0, 0, Math.PI * 2); g.fill();

    // 2. Torso (Navy Guard Uniform)
    g.fillStyle = "#3b5170";
    g.strokeStyle = INK;
    g.lineWidth = 12;
    g.beginPath();
    g.moveTo(230, 410); g.lineTo(370, 410);
    g.lineTo(380, 680); g.lineTo(220, 680);
    g.closePath();
    g.fill(); g.stroke();

    // Gold badge on chest
    g.fillStyle = "#eab308";
    g.beginPath();
    g.moveTo(260, 460); g.lineTo(275, 450); g.lineTo(290, 460);
    g.lineTo(285, 485); g.lineTo(275, 495); g.lineTo(265, 485);
    g.closePath();
    g.fill();

    // Black utility belt with gold buckle
    g.fillStyle = "#181a20";
    g.fillRect(220, 640, 160, 35);
    g.fillStyle = "#eab308";
    g.fillRect(285, 640, 30, 35);

    // 3. Head (Paper-white with plum ink outline)
    g.fillStyle = "#ffffff";
    g.strokeStyle = INK;
    g.lineWidth = 12;
    g.beginPath();
    g.ellipse(300, 280, 110, 100, 0, 0, Math.PI * 2);
    g.fill(); g.stroke();

    // 4. Peaked Guard Cap
    // Visor
    g.fillStyle = "#181a20";
    g.fillRect(160, 240, 280, 24);
    // Dome
    g.fillStyle = "#3b5170";
    g.beginPath();
    g.moveTo(185, 240); g.lineTo(205, 150);
    g.lineTo(395, 150); g.lineTo(415, 240);
    g.closePath();
    g.fill(); g.stroke();
    // Gold cap badge
    g.fillStyle = "#eab308";
    g.beginPath();
    g.moveTo(285, 185); g.lineTo(300, 170); g.lineTo(315, 185);
    g.lineTo(310, 210); g.lineTo(300, 220); g.lineTo(290, 210);
    g.closePath();
    g.fill();

    // 5. Face: Angry gritted teeth & mustache
    const eyeY = 280;
    // Angled exertion brows
    g.strokeStyle = INK;
    g.lineWidth = 8;
    g.beginPath(); g.moveTo(245, eyeY - 20); g.lineTo(285, eyeY - 8); g.stroke();
    g.beginPath(); g.moveTo(315, eyeY - 8); g.lineTo(355, eyeY - 20); g.stroke();
    // Eyes
    g.fillStyle = "#ffffff";
    g.beginPath(); g.arc(265, eyeY, 14, 0, Math.PI * 2); g.fill(); g.stroke();
    g.beginPath(); g.arc(335, eyeY, 14, 0, Math.PI * 2); g.fill(); g.stroke();
    g.fillStyle = INK;
    g.beginPath(); g.arc(265, eyeY, 5, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.arc(335, eyeY, 5, 0, Math.PI * 2); g.fill();

    // Bushy Black Mustache
    g.fillStyle = INK;
    g.beginPath();
    g.moveTo(260, 318);
    g.quadraticCurveTo(300, 310, 340, 318);
    g.quadraticCurveTo(300, 332, 260, 318);
    g.fill();

    // Clenched Teeth Grid
    const mouthY = 338;
    g.fillStyle = "#ffffff";
    g.strokeStyle = INK;
    g.lineWidth = 6;
    g.fillRect(278, mouthY - 8, 44, 20);
    g.strokeRect(278, mouthY - 8, 44, 20);
    g.lineWidth = 3;
    g.beginPath(); g.moveTo(278, mouthY + 2); g.lineTo(322, mouthY + 2); g.stroke();
    for (let tx = 286; tx <= 316; tx += 9) {
      g.beginPath(); g.moveTo(tx, mouthY - 7); g.lineTo(tx, mouthY + 11); g.stroke();
    }

    // 6. Arms holding long paint roller pole upward
    g.strokeStyle = "#3b5170";
    g.lineWidth = 14;
    g.beginPath(); g.moveTo(230, 430); g.lineTo(270, 520); g.stroke(); // Left arm
    g.beginPath(); g.moveTo(370, 430); g.lineTo(390, 460); g.lineTo(330, 420); g.stroke(); // Right arm

    // Hands
    g.fillStyle = "#ffffff";
    g.beginPath(); g.arc(270, 520, 12, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.arc(330, 420, 12, 0, Math.PI * 2); g.fill();

    // Telescoping roller pole reaching diagonally up-left
    g.strokeStyle = "#64748b";
    g.lineWidth = 8;
    g.beginPath(); g.moveTo(250, 560); g.lineTo(440, 140); g.stroke();

    // Fluffy pink paint roller head at top of pole
    g.fillStyle = "#f472b6";
    g.strokeStyle = INK;
    g.lineWidth = 5;
    g.fillRect(415, 120, 75, 28);
    g.strokeRect(415, 120, 75, 28);
  });
}

/**
 * Scientist at Mix Bench holding measuring beaker (Scene 2)
 */
export function getScientistWorkshopTexture(): THREE.CanvasTexture {
  return ctex("tex_actor_sci_workshop", 600, 1000, (g) => {
    // Legs
    g.strokeStyle = INK;
    g.lineWidth = 14;
    g.beginPath(); g.moveTo(260, 680); g.lineTo(255, 960); g.stroke();
    g.beginPath(); g.moveTo(340, 680); g.lineTo(345, 960); g.stroke();

    // Torso (White Shirt & Brown Striped Tie)
    g.fillStyle = "#ffffff";
    g.strokeStyle = INK;
    g.lineWidth = 12;
    g.beginPath();
    g.moveTo(235, 400); g.lineTo(365, 400);
    g.lineTo(370, 680); g.lineTo(230, 680);
    g.closePath();
    g.fill(); g.stroke();

    // Brown striped tie
    g.fillStyle = "#78350f";
    g.beginPath();
    g.moveTo(292, 410); g.lineTo(308, 410);
    g.lineTo(315, 590); g.lineTo(300, 620); g.lineTo(285, 590);
    g.closePath();
    g.fill();
    // Gold diagonal stripes
    g.strokeStyle = "#eab308";
    g.lineWidth = 4;
    for (const ty of [440, 480, 520, 560]) {
      g.beginPath(); g.moveTo(290, ty); g.lineTo(310, ty + 15); g.stroke();
    }

    // Head (Paper-white card)
    g.fillStyle = "#ffffff";
    g.strokeStyle = INK;
    g.lineWidth = 12;
    g.beginPath();
    g.ellipse(300, 280, 110, 100, 0, 0, Math.PI * 2);
    g.fill(); g.stroke();

    // Hair (Brown side-parted comb-over)
    g.fillStyle = "#451a03";
    g.beginPath();
    g.moveTo(195, 270);
    g.lineTo(210, 200); g.lineTo(260, 180);
    g.lineTo(340, 185); g.lineTo(390, 220);
    g.lineTo(395, 270); g.lineTo(380, 240);
    g.lineTo(320, 210); g.lineTo(240, 220);
    g.closePath();
    g.fill(); g.stroke();

    // Face: Skeptical deadpan brows & eyes
    const eyeY = 280;
    g.strokeStyle = INK;
    g.lineWidth = 7;
    // Arched skeptical left brow
    g.beginPath(); g.moveTo(250, eyeY - 20); g.lineTo(285, eyeY - 14); g.stroke();
    // Flat deadpan right brow
    g.beginPath(); g.moveTo(315, eyeY - 15); g.lineTo(350, eyeY - 15); g.stroke();
    // Lidded deadpan eyes
    g.fillStyle = INK;
    g.beginPath(); g.arc(268, eyeY, 8, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.arc(332, eyeY, 8, 0, Math.PI * 2); g.fill();

    // Subtle small mouth
    g.lineWidth = 5;
    g.beginPath(); g.moveTo(290, 325); g.lineTo(310, 325); g.stroke();

    // Left arm down
    g.strokeStyle = "#ffffff";
    g.lineWidth = 12;
    g.beginPath(); g.moveTo(235, 420); g.lineTo(220, 560); g.stroke();
    g.fillStyle = "#ffffff";
    g.beginPath(); g.arc(220, 565, 12, 0, Math.PI * 2); g.fill();

    // Right arm holding measuring beaker up
    g.strokeStyle = "#ffffff";
    g.lineWidth = 12;
    g.beginPath(); g.moveTo(365, 420); g.lineTo(440, 440); g.lineTo(420, 350); g.stroke();
    g.beginPath(); g.arc(420, 350, 12, 0, Math.PI * 2); g.fill();

    // Measuring beaker in right hand
    g.fillStyle = "rgba(224,242,254,0.3)";
    g.strokeStyle = INK;
    g.lineWidth = 3;
    g.fillRect(405, 280, 45, 65);
    g.strokeRect(405, 280, 45, 65);
    // Red liquid inside
    g.fillStyle = "#dc2626";
    g.fillRect(407, 305, 41, 38);
    // Beaker tick lines
    g.strokeStyle = "#ffffff";
    g.lineWidth = 2;
    for (let by = 290; by <= 335; by += 12) {
      g.beginPath(); g.moveTo(407, by); g.lineTo(418, by); g.stroke();
    }
  });
}

/**
 * Scientist holding Pantone Swatch Card "P-618" (Scene 3)
 */
export function getScientistSwatchTexture(): THREE.CanvasTexture {
  return ctex("tex_actor_sci_swatch", 600, 1000, (g) => {
    // Torso (White shirt & brown tie)
    g.fillStyle = "#ffffff";
    g.strokeStyle = INK;
    g.lineWidth = 12;
    g.beginPath();
    g.moveTo(235, 400); g.lineTo(365, 400);
    g.lineTo(370, 680); g.lineTo(230, 680);
    g.closePath();
    g.fill(); g.stroke();

    // Tie
    g.fillStyle = "#78350f";
    g.beginPath();
    g.moveTo(292, 410); g.lineTo(308, 410);
    g.lineTo(315, 590); g.lineTo(300, 620); g.lineTo(285, 590);
    g.closePath();
    g.fill();

    // Head
    g.fillStyle = "#ffffff";
    g.strokeStyle = INK;
    g.lineWidth = 12;
    g.beginPath();
    g.ellipse(300, 280, 110, 100, 0, 0, Math.PI * 2);
    g.fill(); g.stroke();

    // Hair
    g.fillStyle = "#451a03";
    g.beginPath();
    g.moveTo(195, 270); g.lineTo(210, 200); g.lineTo(260, 180);
    g.lineTo(340, 185); g.lineTo(390, 220); g.lineTo(395, 270);
    g.closePath();
    g.fill(); g.stroke();

    // Skeptical brows
    const eyeY = 280;
    g.strokeStyle = INK;
    g.lineWidth = 7;
    g.beginPath(); g.moveTo(250, eyeY - 20); g.lineTo(285, eyeY - 14); g.stroke();
    g.beginPath(); g.moveTo(315, eyeY - 15); g.lineTo(350, eyeY - 15); g.stroke();
    g.fillStyle = INK;
    g.beginPath(); g.arc(268, eyeY, 8, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.arc(332, eyeY, 8, 0, Math.PI * 2); g.fill();

    // Right arm raised holding Pantone card next to head
    g.strokeStyle = "#ffffff";
    g.lineWidth = 12;
    g.beginPath(); g.moveTo(235, 420); g.lineTo(160, 380); g.lineTo(170, 260); g.stroke();
    g.fillStyle = "#ffffff";
    g.beginPath(); g.arc(170, 260, 12, 0, Math.PI * 2); g.fill();

    // Pantone Card "P-618" held in hand
    g.fillStyle = "#ffffff";
    g.strokeStyle = INK;
    g.lineWidth = 6;
    g.fillRect(30, 100, 150, 180);
    g.strokeRect(30, 100, 150, 180);

    // Pink sample square on card
    g.fillStyle = "#f472b6";
    g.fillRect(40, 110, 130, 120);

    // Printed Text "P-618"
    g.fillStyle = "#0f172a";
    g.font = "bold 32px sans-serif";
    g.textAlign = "center";
    g.fillText("P-618", 105, 265);
  });
}

/**
 * The 300lb Inmate Landing & Laughing (Scene 7)
 */
export function getInmate300LandingTexture(): THREE.CanvasTexture {
  return ctex("tex_actor_inmate_300_landing", 600, 1000, (g) => {
    // Stick legs
    g.strokeStyle = INK;
    g.lineWidth = 16;
    g.beginPath(); g.moveTo(250, 660); g.lineTo(240, 960); g.stroke();
    g.beginPath(); g.moveTo(350, 660); g.lineTo(360, 960); g.stroke();

    // Stout pear-shaped torso
    g.fillStyle = "#f1f5f9"; // White tank top
    g.strokeStyle = INK;
    g.lineWidth = 16;
    g.beginPath();
    g.moveTo(210, 420); g.lineTo(390, 420);
    g.lineTo(440, 580); g.lineTo(420, 670);
    g.lineTo(180, 670); g.lineTo(160, 580);
    g.closePath();
    g.fill(); g.stroke();

    // Vertical ribbing lines
    g.strokeStyle = "rgba(148,163,184,0.4)";
    g.lineWidth = 3;
    for (let rx = 220; rx <= 380; rx += 14) {
      g.beginPath(); g.moveTo(rx, 440); g.lineTo(rx, 600); g.stroke();
    }

    // Blue boxer waistband
    g.fillStyle = "#2563eb";
    g.fillRect(175, 600, 250, 70);
    g.strokeStyle = INK;
    g.lineWidth = 12;
    g.strokeRect(175, 600, 250, 70);

    // Bald Round Head
    g.fillStyle = "#ffffff";
    g.strokeStyle = INK;
    g.lineWidth = 14;
    g.beginPath();
    g.ellipse(300, 260, 130, 120, 0, 0, Math.PI * 2);
    g.fill(); g.stroke();

    // Cocky arched eyebrows
    g.strokeStyle = INK;
    g.lineWidth = 9;
    g.beginPath(); g.moveTo(230, 240); g.lineTo(270, 230); g.stroke();
    g.beginPath(); g.moveTo(330, 230); g.lineTo(370, 240); g.stroke();

    // Laughing grin with teeth grid
    g.fillStyle = "#ffffff";
    g.strokeStyle = INK;
    g.lineWidth = 7;
    g.beginPath();
    g.ellipse(300, 310, 36, 18, 0, 0, Math.PI);
    g.closePath();
    g.fill(); g.stroke();
    // Teeth line
    g.lineWidth = 3;
    g.beginPath(); g.moveTo(270, 316); g.lineTo(330, 316); g.stroke();

    // Eyes
    g.fillStyle = INK;
    g.beginPath(); g.arc(255, 255, 8, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.arc(345, 255, 8, 0, Math.PI * 2); g.fill();

    // Arms flexing upward in laughter
    g.strokeStyle = INK;
    g.lineWidth = 14;
    g.lineCap = "round";
    // Left arm curved up
    g.beginPath(); g.moveTo(170, 440); g.lineTo(120, 480); g.lineTo(130, 400); g.stroke();
    // Right arm curved up
    g.beginPath(); g.moveTo(430, 440); g.lineTo(480, 480); g.lineTo(470, 400); g.stroke();

    // Anchor tattoo on left shoulder
    g.strokeStyle = "#1d4ed8";
    g.lineWidth = 4;
    g.beginPath(); g.moveTo(200, 440); g.lineTo(200, 475); g.stroke();
    g.beginPath(); g.arc(200, 436, 7, 0, Math.PI * 2); g.stroke();
    g.beginPath(); g.moveTo(190, 450); g.lineTo(210, 450); g.stroke();
    g.beginPath(); g.moveTo(188, 468); g.lineTo(200, 475); g.lineTo(212, 468); g.stroke();
  });
}

/**
 * The 300lb Inmate Docile & Knitting Scarf (Scene 15)
 */
export function getInmate300KnittingTexture(): THREE.CanvasTexture {
  return ctex("tex_actor_inmate_300_knitting", 600, 1000, (g) => {
    // Dangling sitting legs
    g.strokeStyle = INK;
    g.lineWidth = 14;
    g.beginPath(); g.moveTo(260, 670); g.lineTo(250, 850); g.lineTo(240, 940); g.stroke();
    g.beginPath(); g.moveTo(340, 670); g.lineTo(350, 850); g.lineTo(360, 940); g.stroke();

    // Stout pear body
    g.fillStyle = "#f1f5f9";
    g.strokeStyle = INK;
    g.lineWidth = 16;
    g.beginPath();
    g.moveTo(210, 420); g.lineTo(390, 420);
    g.lineTo(440, 580); g.lineTo(420, 670);
    g.lineTo(180, 670); g.lineTo(160, 580);
    g.closePath();
    g.fill(); g.stroke();

    // Blue boxer waistband
    g.fillStyle = "#2563eb";
    g.fillRect(175, 600, 250, 70);
    g.strokeStyle = INK;
    g.lineWidth = 12;
    g.strokeRect(175, 600, 250, 70);

    // Bald Round Head
    g.fillStyle = "#ffffff";
    g.strokeStyle = INK;
    g.lineWidth = 14;
    g.beginPath();
    g.ellipse(300, 260, 130, 120, 0, 0, Math.PI * 2);
    g.fill(); g.stroke();

    // Angelic blush curved eyes (^ ^)
    g.strokeStyle = INK;
    g.lineWidth = 8;
    g.beginPath(); g.arc(255, 260, 14, Math.PI, 0); g.stroke();
    g.beginPath(); g.arc(345, 260, 14, Math.PI, 0); g.stroke();

    // Rosy pink blush circles
    g.fillStyle = "rgba(244,114,182,0.7)";
    g.beginPath(); g.arc(235, 285, 18, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.arc(365, 285, 18, 0, Math.PI * 2); g.fill();

    // Sweet gentle smile
    g.beginPath(); g.arc(300, 295, 16, 0, Math.PI); g.stroke();

    // Arms holding knitting needles in front
    g.strokeStyle = INK;
    g.lineWidth = 12;
    g.beginPath(); g.moveTo(170, 450); g.lineTo(240, 490); g.stroke();
    g.beginPath(); g.moveTo(430, 450); g.lineTo(360, 490); g.stroke();

    // Two yellow knitting needles
    g.strokeStyle = "#facc15";
    g.lineWidth = 8;
    g.beginPath(); g.moveTo(180, 520); g.lineTo(340, 460); g.stroke();
    g.beginPath(); g.moveTo(420, 520); g.lineTo(260, 460); g.stroke();
    // Pink ball stoppers on needle ends
    g.fillStyle = "#ec4899";
    g.beginPath(); g.arc(175, 522, 12, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.arc(425, 522, 12, 0, Math.PI * 2); g.fill();
  });
}

/**
 * The 300lb Inmate Berserk Rage & Snapped Needles (Scene 17 Finale)
 */
export function getInmate300RageTexture(): THREE.CanvasTexture {
  return ctex("tex_actor_inmate_300_rage", 600, 1000, (g) => {
    // Standing legs
    g.strokeStyle = INK;
    g.lineWidth = 16;
    g.beginPath(); g.moveTo(250, 660); g.lineTo(240, 960); g.stroke();
    g.beginPath(); g.moveTo(350, 660); g.lineTo(360, 960); g.stroke();

    // Stout pear body
    g.fillStyle = "#f1f5f9";
    g.strokeStyle = INK;
    g.lineWidth = 16;
    g.beginPath();
    g.moveTo(210, 420); g.lineTo(390, 420);
    g.lineTo(440, 580); g.lineTo(420, 670);
    g.lineTo(180, 670); g.lineTo(160, 580);
    g.closePath();
    g.fill(); g.stroke();

    // Blue boxers
    g.fillStyle = "#2563eb";
    g.fillRect(175, 600, 250, 70);
    g.strokeStyle = INK;
    g.lineWidth = 12;
    g.strokeRect(175, 600, 250, 70);

    // Bald Round Head
    g.fillStyle = "#ffffff";
    g.strokeStyle = INK;
    g.lineWidth = 14;
    g.beginPath();
    g.ellipse(300, 260, 130, 120, 0, 0, Math.PI * 2);
    g.fill(); g.stroke();

    // Dark anime forehead anger shadow gradient
    const shadowG = g.createLinearGradient(0, 150, 0, 280);
    shadowG.addColorStop(0, "rgba(30,41,59,0.85)");
    shadowG.addColorStop(1, "rgba(30,41,59,0.0)");
    g.fillStyle = shadowG;
    g.beginPath();
    g.ellipse(300, 230, 126, 80, 0, 0, Math.PI * 2);
    g.fill();

    // Red zigzag fury lightning aura radiating from head
    g.strokeStyle = "#ef4444";
    g.lineWidth = 7;
    g.beginPath(); g.moveTo(140, 220); g.lineTo(110, 260); g.lineTo(70, 240); g.stroke();
    g.beginPath(); g.moveTo(460, 220); g.lineTo(490, 260); g.lineTo(530, 240); g.stroke();
    g.beginPath(); g.moveTo(210, 140); g.lineTo(180, 80); g.lineTo(150, 110); g.stroke();
    g.beginPath(); g.moveTo(390, 140); g.lineTo(420, 80); g.lineTo(450, 110); g.stroke();
    g.beginPath(); g.moveTo(300, 140); g.lineTo(290, 60); g.lineTo(320, 40); g.stroke();

    // Slanted fierce rage brows
    g.strokeStyle = INK;
    g.lineWidth = 10;
    g.beginPath(); g.moveTo(225, 235); g.lineTo(275, 255); g.stroke();
    g.beginPath(); g.moveTo(375, 235); g.lineTo(325, 255); g.stroke();

    // Glowing Red Eyes with white pupils
    g.fillStyle = "#dc2626";
    g.beginPath(); g.arc(255, 265, 16, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.arc(345, 265, 16, 0, Math.PI * 2); g.fill();
    g.fillStyle = "#ffffff";
    g.beginPath(); g.arc(255, 265, 6, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.arc(345, 265, 6, 0, Math.PI * 2); g.fill();

    // Clenched Teeth Gritting Scowl
    const mouthY = 320;
    g.fillStyle = "#ffffff";
    g.strokeStyle = INK;
    g.lineWidth = 6;
    g.fillRect(265, mouthY - 12, 70, 26);
    g.strokeRect(265, mouthY - 12, 70, 26);
    g.lineWidth = 3;
    g.beginPath(); g.moveTo(265, mouthY + 1); g.lineTo(335, mouthY + 1); g.stroke();
    for (let tx = 277; tx <= 325; tx += 10) {
      g.beginPath(); g.moveTo(tx, mouthY - 11); g.lineTo(tx, mouthY + 13); g.stroke();
    }

    // Arms flexed with clenched fists holding snapped needles
    g.strokeStyle = INK;
    g.lineWidth = 16;
    g.beginPath(); g.moveTo(170, 440); g.lineTo(120, 410); g.lineTo(150, 340); g.stroke();
    g.beginPath(); g.moveTo(430, 440); g.lineTo(480, 410); g.lineTo(450, 340); g.stroke();

    // Broken yellow knitting needle halves in fists
    g.strokeStyle = "#facc15";
    g.lineWidth = 8;
    // Left jagged half
    g.beginPath(); g.moveTo(100, 370); g.lineTo(170, 320); g.stroke();
    // Right jagged half
    g.beginPath(); g.moveTo(500, 370); g.lineTo(430, 320); g.stroke();
  });
}
