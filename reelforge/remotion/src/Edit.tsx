import React from 'react';
import {AbsoluteFill, OffthreadVideo, Sequence, staticFile} from 'remotion';
import {Captions} from './Captions';
import {Emoji, GRAPHICS} from './graphics';
import {Music, SoundEffects} from './Sound';
import type {EditProps} from './types';
import {VideoSegment} from './VideoSegment';

// A whole edit. Layer order matches the ffmpeg engine: picture, b-roll,
// graphics and emoji, then captions last so text is never hidden behind a
// graphic.
export const Edit: React.FC<EditProps> = (props) => (
  <AbsoluteFill style={{backgroundColor: 'black'}}>
    {props.segments.map((seg) => (
      <Sequence key={seg.id} from={seg.from} durationInFrames={seg.duration} name={`segment ${seg.id}`}>
        <VideoSegment seg={seg} source={props.source} />
      </Sequence>
    ))}

    {props.broll.map((b, i) => (
      <Sequence key={`broll-${i}`} from={b.from} durationInFrames={b.duration} name="b-roll">
        <AbsoluteFill>
          <OffthreadVideo
            src={staticFile(b.src)}
            muted
            style={{width: '100%', height: '100%', objectFit: 'cover'}}
          />
        </AbsoluteFill>
      </Sequence>
    ))}

    {props.overlays.map((o, i) => (
      <Sequence key={`ov-${i}`} from={o.from} durationInFrames={o.duration} name={o.kind === 'emoji' ? 'emoji' : o.comp}>
        {o.kind === 'emoji' ? (
          <Emoji overlay={o} />
        ) : (
          React.createElement(GRAPHICS[o.comp], {duration: o.duration, ...o.props})
        )}
      </Sequence>
    ))}

    <Captions captions={props.captions} />

    {props.music ? <Music music={props.music} /> : null}
    <SoundEffects sfx={props.sfx} />
  </AbsoluteFill>
);
