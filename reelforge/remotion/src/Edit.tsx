import React from 'react';
import {AbsoluteFill, OffthreadVideo, Sequence, staticFile, useVideoConfig} from 'remotion';
import {Captions} from './Captions';
import {EndCard} from './EndCard';
import {Emoji, GRAPHICS} from './graphics';
import {Music, SoundEffects} from './Sound';
import {TopPanel} from './TopPanel';
import type {EditProps, Seg, Source} from './types';
import {VideoSegment} from './VideoSegment';

const Speaker: React.FC<{segments: Seg[]; source: Source}> = ({segments, source}) => (
  <>
    {segments.map((seg) => (
      <Sequence key={seg.id} from={seg.from} durationInFrames={seg.duration} name={`segment ${seg.id}`}>
        <VideoSegment seg={seg} source={source} />
      </Sequence>
    ))}
  </>
);

// A whole edit. Layer order matches the ffmpeg engine: picture, b-roll,
// graphics and emoji, then captions last so text is never hidden behind a
// graphic -- and the end card over everything when it takes the frame.
//
// In a split layout the top panel and the speaker each get their own region.
// The speaker's crop was computed in Python for the lower region's aspect,
// so the face is framed for the space it actually has, not squashed into it.
export const Edit: React.FC<EditProps> = (props) => {
  const {width, height} = useVideoConfig();
  const split = props.layout.kind === 'split';
  const topH = props.layout.topHeight;

  return (
    <AbsoluteFill style={{backgroundColor: split ? props.layout.background : 'black'}}>
      {split ? (
        <>
          <div style={{position: 'absolute', left: 0, top: 0, width, height: topH, overflow: 'hidden'}}>
            <TopPanel clips={props.layout.top} background={props.layout.background} />
          </div>
          <div style={{position: 'absolute', left: 0, top: topH, width, height: height - topH, overflow: 'hidden'}}>
            <Speaker segments={props.segments} source={props.source} />
          </div>
        </>
      ) : (
        <Speaker segments={props.segments} source={props.source} />
      )}

      {props.broll.map((b, i) => (
        <Sequence key={`broll-${i}`} from={b.from} durationInFrames={b.duration} name="b-roll">
          <AbsoluteFill>
            <OffthreadVideo src={staticFile(b.src)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          </AbsoluteFill>
        </Sequence>
      ))}

      {props.overlays.map((o, i) => (
        <Sequence key={`ov-${i}`} from={o.from} durationInFrames={o.duration} name={o.kind === 'emoji' ? 'emoji' : o.comp}>
          {o.kind === 'emoji' ? <Emoji overlay={o} /> : React.createElement(GRAPHICS[o.comp], {duration: o.duration, ...o.props})}
        </Sequence>
      ))}

      <Captions captions={props.captions} hideFrom={props.endCard ? props.endCard.from : undefined} />

      {props.endCard ? (
        <Sequence from={props.endCard.from} durationInFrames={props.endCard.duration} name="end card">
          <EndCard card={props.endCard} segments={props.segments} source={props.source} captions={props.captions} />
        </Sequence>
      ) : null}

      {props.music ? <Music music={props.music} /> : null}
      <SoundEffects sfx={props.sfx} />
    </AbsoluteFill>
  );
};
