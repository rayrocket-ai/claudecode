import React from 'react';
import {AbsoluteFill, Composition} from 'remotion';
import {Edit} from './Edit';
import {GRAPHICS} from './graphics';
import type {EditProps, GraphicName} from './types';

const EMPTY_EDIT: EditProps = {
  fps: 30,
  width: 1080,
  height: 1920,
  durationInFrames: 30,
  source: {src: '', width: 1920, height: 1080},
  segments: [],
  captions: {
    enabled: false,
    pages: [],
    style: {
      fontSize: 106,
      color: '#FFFFFF',
      highlight: '#FFE500',
      outline: '#000000',
      outlineWidth: 7,
      positionY: 0.72,
      marginX: 65,
      fontFamily: 'Inter, "DejaVu Sans", sans-serif',
      anchor: 'bottom',
      box: false,
    },
  },
  overlays: [],
  broll: [],
  music: null,
  sfx: [],
  layout: {kind: 'full', topHeight: 960, background: '#141416', top: []},
  endCard: null,
};

type GraphicProps = {durationInFrames?: number; width?: number; height?: number} & Record<string, unknown>;

// A graphic as a standalone, transparent composition -- used by the ffmpeg
// engine's "remotion" overlay type, which renders it to a PNG sequence and
// composites it. The Edit composition draws the same components inline.
const standalone = (name: GraphicName): React.FC<GraphicProps> => {
  const Component = GRAPHICS[name];
  const Wrapped: React.FC<GraphicProps> = ({durationInFrames = 75, ...rest}) => (
    <AbsoluteFill style={{backgroundColor: 'transparent'}}>
      <Component duration={durationInFrames} {...rest} />
    </AbsoluteFill>
  );
  return Wrapped;
};

const graphicMetadata = ({props}: {props: GraphicProps}) => ({
  durationInFrames: Math.max(1, Math.round(Number(props.durationInFrames ?? 75))),
  width: Number(props.width ?? 1080),
  height: Number(props.height ?? 1920),
});

const GRAPHIC_IDS: [string, GraphicName][] = [
  ['LowerThird', 'lower-third'],
  ['Callout', 'callout'],
  ['Kinetic', 'kinetic'],
  ['Progress', 'progress'],
];

export const Root: React.FC = () => (
  <>
    <Composition
      id="Edit"
      component={Edit}
      defaultProps={EMPTY_EDIT}
      durationInFrames={30}
      fps={30}
      width={1080}
      height={1920}
      // Length, size and rate come from the EDL, not from this file. A
      // composition with a hardcoded duration would truncate or pad every
      // edit that is not exactly that long.
      calculateMetadata={({props}) => ({
        durationInFrames: Math.max(1, props.durationInFrames),
        fps: props.fps,
        width: props.width,
        height: props.height,
      })}
    />
    {GRAPHIC_IDS.map(([id, name]) => (
      <Composition
        key={id}
        id={id}
        component={standalone(name)}
        defaultProps={{durationInFrames: 75} as GraphicProps}
        durationInFrames={75}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={graphicMetadata}
      />
    ))}
  </>
);
