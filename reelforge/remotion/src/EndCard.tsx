import React from 'react';
import {AbsoluteFill, interpolate, Sequence, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {activePage} from './Captions';
import {CLAMP} from './ease';
import type {Captions, EndCard as EndCardProps, Seg, Source} from './types';
import {VideoSegment} from './VideoSegment';

const FONT = 'Inter, "DejaVu Sans", "Noto Sans", system-ui, sans-serif';

const InstagramMark: React.FC<{size: number}> = ({size}) => (
  <svg width={size} height={size} viewBox="0 0 100 100">
    <defs>
      <linearGradient id="ig" x1="0" y1="1" x2="1" y2="0">
        <stop offset="0" stopColor="#FEDA75" />
        <stop offset="0.35" stopColor="#FA7E1E" />
        <stop offset="0.6" stopColor="#D62976" />
        <stop offset="0.85" stopColor="#962FBF" />
        <stop offset="1" stopColor="#4F5BD5" />
      </linearGradient>
    </defs>
    <rect x="6" y="6" width="88" height="88" rx="26" fill="none" stroke="url(#ig)" strokeWidth="9" />
    <circle cx="50" cy="50" r="19" fill="none" stroke="url(#ig)" strokeWidth="9" />
    <circle cx="73" cy="27" r="5.5" fill="url(#ig)" />
  </svg>
);

// "Comment KEYWORD" over the last seconds of the edit: the comment-to-DM lead
// magnet both reference reels end on. The speaker keeps talking inside a
// phone-shaped frame -- a static card would kill the energy right at the ask
// -- with the current caption words inside the frame. The final `outro`
// frames darken to the handle and an Instagram mark.
//
// The phone frame is the same segment timeline drawn again, muted, at the
// full-frame crop: a Sequence offset by -from realigns its clock with the
// edit's, so the speaker in the frame is exactly the speaker the edit plays.
export const EndCard: React.FC<{
  card: EndCardProps;
  segments: Seg[];
  source: Source;
  captions: Captions;
}> = ({card, segments, source, captions}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const fade = interpolate(frame, [0, 6], [0, 1], CLAMP);
  const pop = spring({frame, fps, config: {damping: 13, mass: 0.6}});
  const outroStart = card.duration - card.outro;
  const outro = card.outro > 0 ? interpolate(frame, [outroStart, outroStart + 8], [0, 1], CLAMP) : 0;

  const phoneW = width * 0.46;
  const phoneH = phoneW * (16 / 9);
  const scale = phoneW / width;
  const absolute = card.from + frame;
  const page = captions.enabled ? activePage(captions.pages, absolute) : undefined;

  return (
    <AbsoluteFill style={{background: '#161618', opacity: fade, alignItems: 'center', fontFamily: FONT}}>
      <div style={{marginTop: height * 0.2, textAlign: 'center', transform: `scale(${0.85 + 0.15 * pop})`}}>
        <div style={{color: '#fff', fontSize: height * 0.036, fontWeight: 600}}>
          Comment{' '}
          <span style={{color: card.accent, textDecoration: 'underline', textUnderlineOffset: 8}}>
            "{card.keyword}"
          </span>
        </div>
        {card.subtitle ? (
          <div style={{display: 'inline-block', marginTop: 14, background: card.accent, color: '#fff',
            fontSize: height * 0.015, fontWeight: 600, padding: '6px 14px', borderRadius: 6}}>
            {card.subtitle}
          </div>
        ) : null}
      </div>

      <div style={{position: 'relative', marginTop: height * 0.025, width: phoneW, height: phoneH,
        borderRadius: 28, overflow: 'hidden', border: '2px solid #2e2e33',
        boxShadow: '0 30px 80px rgba(0,0,0,.6)'}}>
        <div style={{width, height, transform: `scale(${scale})`, transformOrigin: '0 0'}}>
          <Sequence from={-card.from} layout="none">
            {segments.map((seg) => (
              <Sequence key={seg.id} from={seg.from} durationInFrames={seg.duration}>
                <VideoSegment seg={seg} source={source} crop={seg.cropFull} muted />
              </Sequence>
            ))}
          </Sequence>
        </div>
        {page ? (
          <div style={{position: 'absolute', left: 0, right: 0, bottom: phoneH * 0.24, textAlign: 'center'}}>
            <span style={{background: 'rgba(0,0,0,.55)', color: '#fff', fontWeight: 800,
              fontSize: height * 0.014, letterSpacing: 1, padding: '4px 10px', borderRadius: 4,
              textTransform: 'uppercase'}}>
              {page.words.map((w) => w.text).join(' ')}
            </span>
          </div>
        ) : null}
        {outro > 0 ? (
          <AbsoluteFill style={{background: `rgba(10,10,12,${0.75 * outro})`, alignItems: 'center',
            justifyContent: 'center', flexDirection: 'column', gap: 18, opacity: outro}}>
            <InstagramMark size={phoneW * 0.32} />
            {card.handle ? (
              <div style={{color: '#fff', fontWeight: 700, fontSize: height * 0.014, letterSpacing: 1}}>
                {card.handle.toUpperCase()}
              </div>
            ) : null}
          </AbsoluteFill>
        ) : null}
      </div>

      {card.handle ? (
        <div style={{marginTop: 16, color: '#9a9aa2', fontSize: height * 0.013, display: 'flex',
          alignItems: 'center', gap: 8, opacity: 1 - 0.6 * outro}}>
          <div style={{width: 22, height: 22, borderRadius: 11, background: '#3a3a40'}} />
          {card.handle.replace(/^@/, '')}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
