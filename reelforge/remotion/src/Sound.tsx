import React from 'react';
import {Audio, Sequence, staticFile} from 'remotion';
import type {Music as MusicProps, Sfx} from './types';

// How far into "speech is happening" frame f is, 0..1, with an attack ramp
// before each spoken window and a release ramp after it.
//
// The ffmpeg engine ducks with a sidechain compressor keyed off the audio.
// This engine knows exactly when words are spoken -- the transcript says so --
// so it ducks to a schedule instead. That is not a compromise: it cannot be
// fooled by a cough or a loud room, and it never pumps between words because
// short gaps are merged before the windows ever get here.
export const speechEnvelope = (
  f: number,
  windows: [number, number][],
  attack: number,
  release: number,
): number => {
  let level = 0;
  for (const [start, end] of windows) {
    if (f >= start && f < end) return 1;
    if (f < start && start - f <= attack) level = Math.max(level, 1 - (start - f) / Math.max(1, attack));
    if (f >= end && f - end <= release) level = Math.max(level, 1 - (f - end) / Math.max(1, release));
  }
  return level;
};

export const Music: React.FC<{music: MusicProps}> = ({music}) => (
  <Audio
    src={staticFile(music.src)}
    volume={(f) => {
      const env = speechEnvelope(f, music.windows, music.attack, music.release);
      return music.volume + (music.duckVolume - music.volume) * env;
    }}
  />
);

export const SoundEffects: React.FC<{sfx: Sfx[]}> = ({sfx}) => (
  <>
    {sfx.map((s, i) => (
      // An effect whose lead-in starts before the video does is trimmed at
      // the head rather than delayed -- a riser that must peak on the first
      // frame is already running when the video starts.
      <Sequence key={i} from={s.from} layout="none">
        <Audio src={staticFile(s.src)} trimBefore={s.trimBefore} volume={s.volume} />
      </Sequence>
    ))}
  </>
);
