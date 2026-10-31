import type {Ease} from './types';

export const clamp01 = (p: number): number => Math.min(1, Math.max(0, p));

// Identical curves to filters.ease_expr in the ffmpeg engine, so a push-in
// moves the same way whichever engine draws it.
export const ease = (kind: Ease, p: number): number => {
  const t = clamp01(p);
  if (kind === 'linear') return t;
  if (kind === 'inOutCubic') return t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2;
  return 1 - (1 - t) ** 3; // outCubic: fast start, gentle settle
};

export const CLAMP = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
