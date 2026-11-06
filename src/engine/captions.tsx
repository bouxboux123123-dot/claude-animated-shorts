import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";

export type WordCue = {
  word: string;
  start: number; // in seconds
  end: number;
  frame_start?: number;
  frame_end?: number;
};

export type CaptionsProps = {
  words: WordCue[];
  yPercent?: number; // default 0.67 (67% of frame height)
  fontSize?: number; // default 58px at 1080p
  strokeWidth?: number; // default 6px
  fillColor?: string; // default white
  strokeColor?: string; // default black
};

/**
 * Standardized kinetic word-pop subtitles component.
 * Locked to y = 0.67 H with a 3-frame scale punch on each word entry.
 */
export const KineticCaptions: React.FC<CaptionsProps> = ({
  words,
  yPercent = 0.67,
  fontSize = 58,
  strokeWidth = 6,
  fillColor = "#ffffff",
  strokeColor = "#000000",
}) => {
  const f = useCurrentFrame();

  const currentCue = useMemo(() => {
    return words.find((w) => {
      const sf = w.frame_start ?? Math.round(w.start * 30);
      const ef = w.frame_end ?? Math.round(w.end * 30);
      return f >= sf && f < ef;
    });
  }, [words, f]);

  if (!currentCue) return null;

  const sf = currentCue.frame_start ?? Math.round(currentCue.start * 30);
  const elapsed = f - sf;

  // 3-frame scale pop (1.18 -> 1.06 -> 1.00)
  const scale = elapsed === 0 ? 1.18 : elapsed === 1 ? 1.06 : 1.0;

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        top: `${yPercent * 100}%`,
        width: "100%",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        pointerEvents: "none",
        zIndex: 50,
      }}
    >
      <span
        style={{
          fontFamily:
            '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
          fontWeight: 900,
          fontSize: `${fontSize}px`,
          textTransform: "uppercase",
          color: fillColor,
          WebkitTextStroke: `${strokeWidth}px ${strokeColor}`,
          paintOrder: "stroke fill",
          letterSpacing: "1.5px",
          transform: `scale(${scale})`,
          transformOrigin: "center center",
          display: "inline-block",
          textShadow: "0 4px 14px rgba(0,0,0,0.5)",
        }}
      >
        {currentCue.word}
      </span>
    </div>
  );
};
