// The contract between ReelForge (Python) and this composition.
//
// Every decision is made on the Python side and arrives here already
// resolved into frames: which source frames to show, where the crop window
// sits, when each caption card appears, when the music ducks. This
// composition draws; it never decides. That is the same rule the ffmpeg
// engine follows, and it is what lets both engines render one EDL
// identically -- and what lets QC repair the EDL rather than the pixels.

export type Ease = 'linear' | 'outCubic' | 'inOutCubic';

export type Source = {
  src: string; // file name inside the job's public dir
  width: number;
  height: number;
};

export type Crop = {x: number; y: number; w: number; h: number}; // source px

export type Seg = {
  id: string;
  from: number; // output frame
  duration: number; // frames
  trimBefore: number; // source frames skipped before this segment starts
  playbackRate: number;
  crop: Crop; // widest point of the move, already clamped inside the frame
  cropFull: Crop; // the same, at the full-frame aspect -- for the end card's phone frame
  animate: boolean;
  zoomFrom: number; // normalised so the smaller end is 1.0
  zoomTo: number;
  ease: Ease;
  fadeIn: number; // frames of dip from black (transitions)
  fadeOut: number; // frames of dip to black
  audioFade: number; // frames of volume ramp at each edge -- kills pops
};

export type CaptionWord = {text: string; start: number; end: number};
export type CaptionPage = {from: number; duration: number; words: CaptionWord[]};

export type CaptionStyle = {
  fontSize: number;
  color: string;
  highlight: string;
  outline: string;
  outlineWidth: number;
  positionY: number; // bottom (or centre, see anchor) of the caption block, 0..1
  anchor: 'bottom' | 'center';
  box: boolean; // white on a full-width black bar -- the split-screen seam caption
  marginX: number; // px each side
  fontFamily: string;
};

export type Captions = {enabled: boolean; style: CaptionStyle; pages: CaptionPage[]};

export type Anchor = 'tl' | 'tr' | 'bl' | 'br' | 'c';

export type EmojiOverlay = {
  kind: 'emoji';
  from: number;
  duration: number;
  glyph: string;
  anchor: Anchor;
  size: number;
  anim: 'pop' | 'fade' | 'none';
};

export type GraphicName = 'lower-third' | 'callout' | 'kinetic' | 'progress';

export type GraphicOverlay = {
  kind: 'graphic';
  from: number;
  duration: number;
  comp: GraphicName;
  props: Record<string, unknown>;
};

export type Overlay = EmojiOverlay | GraphicOverlay;

export type BRoll = {from: number; duration: number; src: string};

export type Music = {
  src: string; // pre-trimmed to the edit's exact length
  volume: number; // linear
  duckVolume: number; // linear, while speech is present
  windows: [number, number][]; // frames where someone is speaking
  attack: number; // frames
  release: number; // frames
};

export type Sfx = {src: string; from: number; trimBefore: number; volume: number};

export type EditProps = {
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  source: Source;
  segments: Seg[];
  captions: Captions;
  overlays: Overlay[];
  broll: BRoll[];
  music: Music | null;
  sfx: Sfx[];
  layout: Layout;
  endCard: EndCard | null;
};

export type Pan = [number, number, number]; // centre x, centre y (0..1), zoom

export type TopClip = {
  kind: 'image' | 'video' | 'prompt';
  from: number;
  duration: number;
  src: string; // image or video for image/video kinds
  panFrom: Pan;
  panTo: Pan;
  text: string; // prompt kind: what types into the box
  result: string; // prompt kind: what appears beside it
  resultIsVideo: boolean;
  label: string; // seam pill while typing
  resultLabel: string; // seam pill once the result shows
  reveal: number; // frames into the clip when the result appears
};

export type Layout = {
  kind: 'full' | 'split';
  topHeight: number; // px
  background: string;
  top: TopClip[];
};

export type EndCard = {
  from: number;
  duration: number;
  keyword: string;
  subtitle: string;
  handle: string;
  outro: number; // frames at the very end
  accent: string;
};
