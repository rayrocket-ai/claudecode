import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {CaptionPage, Captions as CaptionsProps} from './types';

export const activePage = (pages: CaptionPage[], frame: number): CaptionPage | undefined =>
  pages.find((p) => frame >= p.from && frame < p.from + p.duration);

// Word-by-word captions. The grouping into cards is decided in Python by the
// same rules the ffmpeg engine uses (ass.group_words: word count, character
// count, pauses, and a forced break after every cut), so a card never
// straddles a cut and never overflows the frame. Here each card springs in
// and the word being spoken is lit.
//
// Two placements. Bottom-anchored (the default) sits exactly where the ffmpeg
// engine's ASS track would. The boxed seam style centres on the line between
// a split-screen's panel and speaker, white on a full-width black bar.
// `hideFrom` stops drawing when the end card takes over the frame.
export const Captions: React.FC<{captions: CaptionsProps; hideFrom?: number}> = ({captions, hideFrom}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  if (!captions.enabled) return null;
  if (hideFrom !== undefined && frame >= hideFrom) return null;

  const page = activePage(captions.pages, frame);
  if (!page) return null;

  const s = captions.style;
  const enter = spring({frame: frame - page.from, fps, config: {damping: 14, mass: 0.5}});

  const words = page.words.map((w, i) => {
    const active = frame >= w.start && frame < w.end;
    return (
      <span
        key={i}
        style={{
          display: 'inline-block',
          margin: '0 0.14em',
          color: active ? s.highlight : s.color,
          transform: active && !s.box ? 'scale(1.08)' : 'none',
          // Stroke painted under the fill, so the outline thickens the glyph
          // outward instead of eating into it -- the difference between a
          // readable caption and a skeletal one on a busy set.
          WebkitTextStroke: s.outlineWidth > 0 ? `${s.outlineWidth}px ${s.outline}` : undefined,
          paintOrder: 'stroke fill',
        }}
      >
        {w.text}
      </span>
    );
  });

  if (s.box) {
    return (
      <AbsoluteFill>
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: s.positionY * height,
            transform: 'translateY(-50%)',
            background: '#000',
            padding: `${s.fontSize * 0.32}px ${s.marginX}px`,
            textAlign: 'center',
            fontFamily: s.fontFamily,
            fontWeight: 600,
            fontSize: s.fontSize,
            lineHeight: 1.15,
            opacity: Math.min(1, enter * 1.5),
          }}
        >
          {words}
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: s.marginX,
          right: s.marginX,
          ...(s.anchor === 'center'
            ? {top: s.positionY * height, transform: `translateY(-50%) scale(${0.85 + 0.15 * enter})`}
            : {
                // Bottom-anchored, exactly like the ASS track the ffmpeg
                // engine burns in: positionY is where the bottom of the block
                // sits, and a two-line card grows upward.
                bottom: (1 - s.positionY) * height,
                transform: `scale(${0.85 + 0.15 * enter})`,
                transformOrigin: '50% 100%',
              }),
          textAlign: 'center',
          fontFamily: s.fontFamily,
          fontWeight: 900,
          fontSize: s.fontSize,
          lineHeight: 1.1,
          letterSpacing: '-0.01em',
        }}
      >
        {words}
      </div>
    </AbsoluteFill>
  );
};
