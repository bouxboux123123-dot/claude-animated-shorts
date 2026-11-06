import React, { useMemo } from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import WORDS from "./words.json";

export interface WordItem {
  word: string;
  start: number;
  end: number;
  frame: number;
}

export interface Chunk {
  text: string;
  startFrame: number;
  endFrame: number;
}

export const buildChunks = (words: WordItem[]): Chunk[] => {
  const chunks: Chunk[] = [];
  let cur: WordItem[] = [];

  for (let i = 0; i < words.length; i++) {
    const w = words[i];
    cur.push(w);
    const txt = w.word.trim();
    const isPunct = /[.?!,;:]$/.test(txt);
    const isLast = i === words.length - 1;

    // Chunk size: 2-3 words, or end-of-clause punctuation
    if (cur.length >= 3 || (cur.length >= 2 && txt.length > 4) || isPunct || isLast) {
      const nextWord = words[i + 1];
      const startF = cur[0].frame;
      // Hold until next word begins, or at least 14 frames after last word
      const naturalEnd = cur[cur.length - 1].frame + Math.max(14, Math.round((cur[cur.length - 1].end - cur[cur.length - 1].start) * 30));
      const endF = nextWord ? Math.min(nextWord.frame, naturalEnd + 6) : naturalEnd + 15;

      chunks.push({
        text: cur.map((item) => item.word.trim()).join(" ").toUpperCase(),
        startFrame: startF,
        endFrame: Math.max(startF + 6, endF),
      });
      cur = [];
    }
  }

  return chunks;
};

export const KineticCaptions: React.FC = () => {
  const f = useCurrentFrame();
  const chunks = useMemo(() => buildChunks(WORDS as WordItem[]), []);

  const active = useMemo(() => {
    return chunks.find((c) => f >= c.startFrame && f < c.endFrame);
  }, [chunks, f]);

  if (!active) return null;

  const df = f - active.startFrame;
  const pop = df < 4 ? 1.0 + (4 - df) * 0.035 : 1.0;

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        top: "67%",
        height: "180px",
        transform: "translateY(-50%)",
      }}
    >
      <div
        style={{
          fontFamily: '"Impact", "Montserrat Black", "Arial Black", -apple-system, sans-serif',
          fontSize: "84px",
          fontWeight: 900,
          lineHeight: "1.05",
          letterSpacing: "-1.5px",
          color: "#ffffff",
          WebkitTextStroke: "6px #000000",
          paintOrder: "stroke fill",
          textShadow: "0 6px 20px rgba(0, 0, 0, 0.8)",
          textAlign: "center",
          textTransform: "uppercase",
          maxWidth: "880px",
          padding: "0 30px",
          transform: `scale(${pop})`,
          transformOrigin: "center center",
        }}
      >
        {active.text}
      </div>
    </AbsoluteFill>
  );
};
