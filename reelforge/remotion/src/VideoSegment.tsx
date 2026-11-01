import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CLAMP, ease} from './ease';
import {ShotPicture} from './Shot';
import type {Crop, Seg, Source} from './types';

// One kept span of the source, reframed to the region it is drawn into.
//
// The crop window arrives from Python already computed by the same function
// the ffmpeg engine uses (filters.crop_window), centred on the subject and
// clamped so it never runs off the frame. Here it only has to be honoured:
// scale the source so the window fills the region's width, offset it so the
// window sits at the origin, then magnify around the centre for a push-in.
//
// `crop` overrides the segment's own window -- the end card's phone frame
// draws the speaker at the full-frame aspect even when the edit is split.
// `muted` is for that same copy: the speaker's voice must play once.
export const VideoSegment: React.FC<{seg: Seg; source: Source; crop?: Crop; muted?: boolean}> = ({
  seg,
  source,
  crop,
  muted = false,
}) => {
  const frame = useCurrentFrame();
  const {width} = useVideoConfig();
  const window = crop ?? seg.crop;

  const zoom = seg.animate
    ? seg.zoomFrom + (seg.zoomTo - seg.zoomFrom) * ease(seg.ease, frame / Math.max(1, seg.duration))
    : 1;

  const scale = width / window.w;
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

  // Several camera setups inside one segment: the picture cuts between them
  // while the voice plays once, unbroken, underneath -- a picture cut with no
  // audio cut is what makes one camera read as several. The end card's phone
  // frame (which passes its own crop) keeps the plain single-window path.
  if (!crop && seg.shots && seg.shots.length > 0) {
    return (
      <AbsoluteFill style={{backgroundColor: 'black', overflow: 'hidden', opacity}}>
        {seg.shots.map((shot, i) => (
          <Sequence key={i} from={shot.from} durationInFrames={shot.duration} name={`shot ${shot.size}`}>
            <ShotPicture shot={shot} source={source} playbackRate={seg.playbackRate} />
          </Sequence>
        ))}
        {muted ? null : (
          <Audio src={staticFile(source.src)} trimBefore={seg.trimBefore} playbackRate={seg.playbackRate} />
        )}
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{backgroundColor: 'black', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${zoom})`, transformOrigin: '50% 50%', opacity}}>
        <OffthreadVideo
          src={staticFile(source.src)}
          trimBefore={seg.trimBefore}
          playbackRate={seg.playbackRate}
          volume={volume}
          muted={muted}
          style={{
            position: 'absolute',
            left: -window.x * scale,
            top: -window.y * scale,
            width: source.width * scale,
            height: source.height * scale,
            maxWidth: 'none',
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
