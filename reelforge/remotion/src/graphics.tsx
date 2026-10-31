import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {CLAMP} from './ease';
import type {Anchor, EmojiOverlay, GraphicName} from './types';

// Motion graphics. Same four compositions as the HyperFrames backend, but
// with real spring physics -- which is the reason to have Remotion at all.

const FONT = 'Inter, "DejaVu Sans", "Noto Sans", system-ui, sans-serif';

const useExit = (duration: number, frames = 10): number => {
  const frame = useCurrentFrame();
  return interpolate(frame, [duration - frames, duration], [1, 0], CLAMP);
};

export const LowerThird: React.FC<{duration: number; title?: string; subtitle?: string; accent?: string}> = ({
  duration,
  title = '',
  subtitle = '',
  accent = '#FF6B2C',
}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 13, mass: 0.7}});
  const bar = spring({frame: frame - 4, fps, config: {damping: 20}});
  const exit = useExit(duration);
  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: 64,
          bottom: height * 0.17,
          transform: `translateX(${(1 - enter) * -120}px)`,
          opacity: Math.min(enter, exit),
          fontFamily: FONT,
        }}
      >
        <div style={{height: 8, width: 260 * bar, background: accent, borderRadius: 4, marginBottom: 18}} />
        <div style={{fontSize: height * 0.036, fontWeight: 800, color: '#fff', textShadow: '0 4px 24px rgba(0,0,0,.55)'}}>
          {title}
        </div>
        {subtitle ? (
          <div style={{fontSize: height * 0.023, fontWeight: 600, color: '#e8e8e8', marginTop: 8, textShadow: '0 3px 18px rgba(0,0,0,.55)'}}>
            {subtitle}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

export const Callout: React.FC<{duration: number; text?: string; accent?: string}> = ({duration, text = '', accent = '#FFD400'}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const pop = spring({frame, fps, config: {damping: 9, mass: 0.6}});
  const exit = useExit(duration, 8);
  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: height * 0.22,
          transform: `translate(-50%,-50%) scale(${Math.max(0.01, pop * (0.75 + 0.25 * exit))})`,
          opacity: exit,
          background: accent,
          color: '#101010',
          padding: '18px 34px',
          borderRadius: 18,
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: height * 0.034,
          whiteSpace: 'nowrap',
          boxShadow: '0 12px 40px rgba(0,0,0,.35)',
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

export const Kinetic: React.FC<{duration: number; words?: string[]; text?: string; accent?: string}> = ({
  duration,
  words,
  text = '',
  accent = '#FFD400',
}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const list = words && words.length ? words : text.split(/\s+/).filter(Boolean);
  const per = duration / (list.length + 1);
  const exit = useExit(duration);
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', opacity: exit}}>
      <div style={{width: '86%', textAlign: 'center', fontFamily: FONT}}>
        {list.map((w, i) => {
          const s = spring({frame: frame - i * per, fps, config: {damping: 11, mass: 0.5}});
          return (
            <span
              key={i}
              style={{
                display: 'inline-block',
                margin: '0 10px',
                fontSize: height * 0.052,
                fontWeight: 900,
                letterSpacing: -1,
                color: i === list.length - 1 ? accent : '#fff',
                opacity: s,
                transform: `translateY(${(1 - s) * 40}px) scale(${0.6 + 0.4 * s})`,
                textShadow: '0 6px 28px rgba(0,0,0,.6)',
              }}
            >
              {w}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Progress: React.FC<{duration: number; accent?: string}> = ({duration, accent = '#FF6B2C'}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, Math.max(1, duration - 1)], [0, 100], CLAMP);
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: 0, bottom: 0, height: 10, width: `${p}%`, background: accent}} />
    </AbsoluteFill>
  );
};

export const GRAPHICS: Record<GraphicName, React.FC<any>> = {
  'lower-third': LowerThird,
  callout: Callout,
  kinetic: Kinetic,
  progress: Progress,
};

const MARGIN = 48;

const anchorStyle = (anchor: Anchor, size: number): React.CSSProperties => {
  switch (anchor) {
    case 'tl':
      return {left: MARGIN, top: MARGIN};
    case 'tr':
      return {right: MARGIN, top: MARGIN};
    case 'bl':
      return {left: MARGIN, bottom: MARGIN};
    case 'br':
      return {right: MARGIN, bottom: MARGIN};
    default:
      return {left: '50%', top: '50%', marginLeft: -size / 2, marginTop: -size / 2};
  }
};

// Emoji are drawn as text with a colour emoji font -- Chrome renders those
// natively, which removes the rasterise-to-PNG step the ffmpeg engine needs
// because libass cannot.
export const Emoji: React.FC<{overlay: EmojiOverlay}> = ({overlay}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop =
    overlay.anim === 'pop'
      ? spring({frame, fps, config: {damping: 8, mass: 0.5}})
      : overlay.anim === 'fade'
        ? interpolate(frame, [0, 6], [0, 1], CLAMP)
        : 1;
  const exit = interpolate(frame, [overlay.duration - 6, overlay.duration], [1, 0], CLAMP);
  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          width: overlay.size,
          height: overlay.size,
          ...anchorStyle(overlay.anchor, overlay.size),
          fontSize: overlay.size * 0.86,
          lineHeight: 1,
          textAlign: 'center',
          fontFamily: '"Apple Color Emoji", "Noto Color Emoji", "Segoe UI Emoji", sans-serif',
          transform: overlay.anim === 'pop' ? `scale(${pop})` : undefined,
          opacity: Math.min(overlay.anim === 'fade' ? pop : 1, exit),
        }}
      >
        {overlay.glyph}
      </div>
    </AbsoluteFill>
  );
};
