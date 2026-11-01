import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CLAMP, ease} from './ease';
import type {Pan, TopClip} from './types';

const FONT = 'Inter, "DejaVu Sans", "Noto Sans", system-ui, sans-serif';
const MONO = '"JetBrains Mono", "DejaVu Sans Mono", Menlo, monospace';
const ACCENT = '#E8735A';

// A still panned and zoomed across over the clip's length -- the explainer
// format: one big diagram, the camera walking it while the speaker talks.
//
// objectPosition moves the cover-crop window toward the focus point, and the
// scale grows around that same point, so a pan from one corner of a wide
// diagram to another reads as the camera travelling, not the image sliding.
const PanImage: React.FC<{src: string; from: Pan; to: Pan; duration: number}> = ({src, from, to, duration}) => {
  const frame = useCurrentFrame();
  const p = ease('inOutCubic', frame / Math.max(1, duration));
  const cx = from[0] + (to[0] - from[0]) * p;
  const cy = from[1] + (to[1] - from[1]) * p;
  const z = from[2] + (to[2] - from[2]) * p;
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#fff'}}>
      <Img
        src={staticFile(src)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: `${cx * 100}% ${cy * 100}%`,
          transform: `scale(${z})`,
          transformOrigin: `${cx * 100}% ${cy * 100}%`,
        }}
      />
    </AbsoluteFill>
  );
};

const Pill: React.FC<{text: string; visible: number}> = ({text, visible}) => (
  <div
    style={{
      position: 'absolute',
      left: '50%',
      // Clear of the seam caption bar, which straddles the panel's bottom edge.
      bottom: 84,
      transform: `translateX(-50%) scale(${0.9 + 0.1 * visible})`,
      opacity: visible,
      background: '#0d0d0f',
      color: '#fff',
      fontFamily: FONT,
      fontWeight: 800,
      fontSize: 30,
      letterSpacing: 1.5,
      padding: '8px 18px',
      borderRadius: 8,
      whiteSpace: 'nowrap',
    }}
  >
    {text}
  </div>
);

// "Write this -> get this": a chat box types a command, then the result it
// produced springs in beside it. The seam pill flips from the first label to
// the second on the reveal, so the viewer is told what they are looking at
// on every beat. Typing finishes a little before the reveal -- a result that
// appears mid-word reads as a glitch, not as cause and effect.
const PromptPanel: React.FC<{clip: TopClip}> = ({clip}) => {
  const frame = useCurrentFrame();
  const {fps, width} = useVideoConfig();
  const typingEnd = Math.max(1, Math.round(clip.reveal * 0.85));
  const shown = Math.round(interpolate(frame, [0, typingEnd], [0, clip.text.length], CLAMP));
  const revealed = frame >= clip.reveal;
  const pop = revealed ? spring({frame: frame - clip.reveal, fps, config: {damping: 12, mass: 0.6}}) : 0;
  const cursorOn = Math.floor(frame / 8) % 2 === 0;
  const enter = spring({frame, fps, config: {damping: 20}});

  return (
    <AbsoluteFill style={{background: '#141416', alignItems: 'center', justifyContent: 'center'}}>
      <div
        style={{
          display: 'flex',
          gap: 26,
          alignItems: 'center',
          width: width * 0.94,
          marginBottom: 90,
          transform: `translateY(${(1 - enter) * 30}px)`,
          opacity: enter,
        }}
      >
        <div
          style={{
            flex: 1.25,
            background: '#232327',
            border: '1px solid #36363c',
            borderRadius: 22,
            padding: 26,
            fontFamily: FONT,
            boxShadow: '0 20px 50px rgba(0,0,0,.45)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20}}>
            <div style={{width: 64, height: 64, borderRadius: 12, background: '#3a3a40'}} />
            <div style={{color: '#9a9aa2', fontSize: 20}}>
              <div style={{background: '#55555c', color: '#fff', fontSize: 14, fontWeight: 700, borderRadius: 4,
                padding: '1px 6px', display: 'inline-block', marginBottom: 4}}>RAW</div>
              <div>take.mov</div>
            </div>
          </div>
          <div style={{fontFamily: MONO, fontSize: 44, color: ACCENT, minHeight: 116, lineHeight: 1.3,
            wordBreak: 'break-word'}}>
            {clip.text.slice(0, shown)}
            <span style={{color: '#fff', opacity: cursorOn ? 1 : 0}}>|</span>
          </div>
          <div style={{display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 12, marginTop: 14}}>
            <span style={{color: '#77777e', fontSize: 18}}>ReelForge</span>
            <div style={{width: 34, height: 34, borderRadius: 17, background: ACCENT}} />
          </div>
        </div>
        <div
          style={{
            flex: 0.75,
            aspectRatio: '9 / 16',
            borderRadius: 20,
            overflow: 'hidden',
            background: '#000',
            border: '3px solid #2b2b30',
            transform: `scale(${0.6 + 0.4 * pop})`,
            opacity: pop,
            boxShadow: '0 20px 50px rgba(0,0,0,.5)',
          }}
        >
          {clip.result ? (
            clip.resultIsVideo ? (
              <OffthreadVideo src={staticFile(clip.result)} muted
                style={{width: '100%', height: '100%', objectFit: 'cover'}} />
            ) : (
              <Img src={staticFile(clip.result)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
            )
          ) : null}
        </div>
      </div>
      <Pill text={revealed ? clip.resultLabel : clip.label} visible={Math.min(1, enter * 1.4)} />
    </AbsoluteFill>
  );
};

export const TopPanel: React.FC<{clips: TopClip[]; background: string}> = ({clips, background}) => (
  <AbsoluteFill style={{background, overflow: 'hidden'}}>
    {clips.map((clip, i) => (
      <Sequence key={i} from={clip.from} durationInFrames={clip.duration} name={`top ${clip.kind}`}>
        {clip.kind === 'image' ? (
          <PanImage src={clip.src} from={clip.panFrom} to={clip.panTo} duration={clip.duration} />
        ) : clip.kind === 'video' ? (
          <AbsoluteFill>
            <OffthreadVideo src={staticFile(clip.src)} muted
              style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          </AbsoluteFill>
        ) : (
          <PromptPanel clip={clip} />
        )}
      </Sequence>
    ))}
  </AbsoluteFill>
);
