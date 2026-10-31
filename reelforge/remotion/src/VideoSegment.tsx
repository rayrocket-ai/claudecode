import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CLAMP, ease} from './ease';
import type {Seg, Source} from './types';

// One kept span of the source, reframed to the output aspect.
//
// The crop window arrives from Python already computed by the same function
// the ffmpeg engine uses (filters.crop_window), centred on the subject and
// clamped so it never runs off the frame. Here it only has to be honoured:
// scale the source so the window fills the output, offset it so the window
// sits at the origin, then magnify around the centre for a push-in. That is
// the ffmpeg engine's animated path -- crop at the widest point, then scale
// up over time -- expressed as a CSS transform.
export const VideoSegment: React.FC<{seg: Seg; source: Source}> = ({seg, source}) => {
  const frame = useCurrentFrame();
  const {width} = useVideoConfig();

  const zoom = seg.animate
    ? seg.zoomFrom + (seg.zoomTo - seg.zoomFrom) * ease(seg.ease, frame / Math.max(1, seg.duration))
    : 1;

  const scale = width / seg.crop.w;
  const opacity = Math.min(
    seg.fadeIn > 0 ? interpolate(frame, [0, seg.fadeIn], [0, 1], CLAMP) : 1,
    seg.fadeOut > 0
      ? interpolate(frame, [seg.duration - seg.fadeOut, seg.duration], [1, 0], CLAMP)
      : 1,
  );

  // A ramp at each edge so two segments spliced at arbitrary sample values do
  // not click. The volume function receives frames relative to this segment.
  const volume = (f: number): number => {
    if (seg.audioFade <= 0) return 1;
    return Math.min(
      interpolate(f, [0, seg.audioFade], [0, 1], CLAMP),
      interpolate(f, [seg.duration - seg.audioFade, seg.duration], [1, 0], CLAMP),
    );
  };

  return (
    <AbsoluteFill style={{backgroundColor: 'black', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${zoom})`, transformOrigin: '50% 50%', opacity}}>
        <OffthreadVideo
          src={staticFile(source.src)}
          trimBefore={seg.trimBefore}
          playbackRate={seg.playbackRate}
          volume={volume}
          style={{
            position: 'absolute',
            left: -seg.crop.x * scale,
            top: -seg.crop.y * scale,
            width: source.width * scale,
            height: source.height * scale,
            maxWidth: 'none',
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
