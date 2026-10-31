import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Captions as CaptionsProps} from './types';

// Word-by-word captions. The grouping into cards is decided in Python by the
// same rules the ffmpeg engine uses (ass.group_words: word count, character
// count, pauses, and a forced break after every cut), so a card never
// straddles a cut and never overflows the frame. Here each card springs in
// and the word being spoken is lit.
export const Captions: React.FC<{captions: CaptionsProps}> = ({captions}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  if (!captions.enabled) return null;

  const page = captions.pages.find((p) => frame >= p.from && frame < p.from + p.duration);
  if (!page) return null;

  const s = captions.style;
  const enter = spring({frame: frame - page.from, fps, config: {damping: 14, mass: 0.5}});

  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: s.marginX,
          right: s.marginX,
          // Bottom-anchored, exactly like the ASS track the ffmpeg engine
          // burns in: positionY is where the bottom of the block sits, and a
          // two-line card grows upward rather than sliding off the frame.
          bottom: (1 - s.positionY) * height,
          transform: `scale(${0.85 + 0.15 * enter})`,
          transformOrigin: '50% 100%',
          textAlign: 'center',
          fontFamily: s.fontFamily,
          fontWeight: 900,
          fontSize: s.fontSize,
          lineHeight: 1.1,
          letterSpacing: '-0.01em',
        }}
      >
        {page.words.map((w, i) => {
          const active = frame >= w.start && frame < w.end;
          return (
            <span
              key={i}
              style={{
                display: 'inline-block',
                margin: '0 0.14em',
                color: active ? s.highlight : s.color,
                transform: active ? 'scale(1.08)' : 'none',
                // Stroke painted under the fill, so the outline thickens the
                // glyph outward instead of eating into it -- the difference
                // between a readable caption and a skeletal one on a busy set.
                WebkitTextStroke: `${s.outlineWidth}px ${s.outline}`,
                paintOrder: 'stroke fill',
              }}
            >
              {w.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
