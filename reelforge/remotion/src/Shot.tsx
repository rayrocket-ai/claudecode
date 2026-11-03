import React from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {ease} from './ease';
import type {Crop, Shot, Source} from './types';

const lerp = (a: number, b: number, p: number) => a + (b - a) * p;

const lerpWindow = (a: Crop, b: Crop, p: number): Crop => ({
  x: lerp(a.x, b.x, p),
  y: lerp(a.y, b.y, p),
  w: lerp(a.w, b.w, p),
  h: lerp(a.h, b.h, p),
});

// Handheld sway: two slow, incommensurate sines per axis, so the motion never
// visibly loops. Seeded per shot, so a render is a pure function of its props.
const sway = (t: number, seed: number) => {
  const s = seed * 0.017;
  return {
    x: Math.sin(2 * Math.PI * 0.27 * t + s) + 0.45 * Math.sin(2 * Math.PI * 0.71 * t + s * 2.3),
    y: Math.sin(2 * Math.PI * 0.21 * t + s * 1.7) + 0.4 * Math.sin(2 * Math.PI * 0.63 * t + s * 0.9),
    r: Math.sin(2 * Math.PI * 0.17 * t + s * 3.1),
  };
};

// A soft, dark shape at one edge of the frame drifting across it: the look of
// a camera placed behind a plant or a shelf edge, shooting past it. It adds
// depth a single locked-off angle does not have, and it moves against the
// camera's own move, which is what sells it as foreground.
const Peek: React.FC<{side: string; progress: number}> = ({side, progress}) => {
  const {width, height} = useVideoConfig();
  const dir = side === 'left' ? 1 : -1;
  return (
    <div
      style={{
        position: 'absolute',
        top: -height * 0.15,
        [side === 'left' ? 'left' : 'right']: -width * 0.16,
        width: width * 0.42,
        height: height * 1.3,
        borderRadius: '45%',
        background: 'radial-gradient(ellipse at center, rgba(14,12,10,.95) 0%, rgba(14,12,10,.75) 40%, rgba(14,12,10,0) 72%)',
        filter: `blur(${Math.round(width * 0.03)}px)`,
        transform: `translateX(${dir * -width * 0.07 * progress}px)`,
      }}
    />
  );
};

// One shot. The crop window glides from its first state to its last over
// `moveFrames` -- push, pull, pan or punch are all just two windows -- and the
// handheld sway rides on top, with a touch of overscan so the edge of the
// source never shows.
export const ShotPicture: React.FC<{shot: Shot; source: Source; playbackRate: number}> = ({
  shot,
  source,
  playbackRate,
}) => {
  const frame = useCurrentFrame();
  const {fps, width} = useVideoConfig();
  const p = ease(shot.ease, frame / Math.max(1, shot.moveFrames));
  const progress = frame / Math.max(1, shot.duration);

  const s = sway(frame / fps, shot.seed);
  const amp = shot.drift * width;
  // Sway peaks at ~1.45x amp plus a hint of roll; 4.5x drift of overscan covers
  // both with margin, so the frame edge can never come into view.
  const overscan = 1 + shot.drift * 4.5;
  const handheld = shot.drift > 0
    ? `translate(${s.x * amp}px, ${s.y * amp}px) rotate(${s.r * shot.drift * 12}deg) scale(${overscan})`
    : 'none';

  if (shot.angle) {
    return (
      <AbsoluteFill style={{overflow: 'hidden', background: 'black'}}>
        <AbsoluteFill style={{transform: handheld}}>
          <OffthreadVideo
            src={staticFile(shot.angle)}
            trimBefore={shot.angleTrimBefore}
            playbackRate={shot.angleRate}
            muted
            style={{width: '100%', height: '100%', objectFit: 'cover'}}
          />
        </AbsoluteFill>
        {shot.peek ? <Peek side={shot.peek} progress={progress} /> : null}
      </AbsoluteFill>
    );
  }

  const win = lerpWindow(shot.windowFrom, shot.windowTo, p);
  const scale = width / win.w;
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: 'black'}}>
      <AbsoluteFill style={{transform: handheld, transformOrigin: '50% 50%'}}>
        <OffthreadVideo
          src={staticFile(source.src)}
          trimBefore={shot.trimBefore}
          playbackRate={playbackRate}
          muted
          style={{
            position: 'absolute',
            left: -win.x * scale,
            top: -win.y * scale,
            width: source.width * scale,
            height: source.height * scale,
            maxWidth: 'none',
          }}
        />
      </AbsoluteFill>
      {shot.peek ? <Peek side={shot.peek} progress={progress} /> : null}
    </AbsoluteFill>
  );
};
