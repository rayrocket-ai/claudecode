import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';

// One Instagram carousel, one slide per frame. Rendered as a PNG sequence
// (`--sequence`), so frame N is slide N -- a carousel is a set of stills, and
// treating it as a 1fps "video" keeps the whole thing in one composition with
// one brand, one font load and one browser launch.

export type Slide = {
  role: 'hook' | 'body' | 'cta';
  headline: string;
  body?: string;
  kicker?: string;
};

export type CarouselBrand = {
  primary: string;
  accent: string;
  text: string;
  muted: string;
  font: string;
  handle: string;
  name: string;
};

export type CarouselProps = {
  slides: Slide[];
  brand: CarouselBrand;
  keyword: string;
  width: number;
  height: number;
};

// *word* in a headline is drawn in the accent colour -- the one emphasis a
// writer gets, so the eye lands where the argument is.
const Emph: React.FC<{text: string; accent: string}> = ({text, accent}) => (
  <>
    {text.split(/(\*[^*]+\*)/g).map((part, i) =>
      part.startsWith('*') && part.endsWith('*') && part.length > 2 ? (
        <span key={i} style={{color: accent}}>{part.slice(1, -1)}</span>
      ) : (
        <React.Fragment key={i}>{part}</React.Fragment>
      ),
    )}
  </>
);

// Long headlines shrink instead of overflowing; short ones get big. A slide
// is read at thumbnail size in the feed first, so size is legibility.
const headlineSize = (text: string, role: Slide['role'], w: number) => {
  const n = text.replace(/\*/g, '').length;
  const base = role === 'hook' ? 0.105 : role === 'cta' ? 0.088 : 0.072;
  const scale = n <= 28 ? 1 : n <= 48 ? 0.85 : n <= 72 ? 0.72 : 0.6;
  return Math.round(w * base * scale);
};

const Footer: React.FC<{brand: CarouselBrand; index: number; total: number; w: number; last: boolean}> = ({
  brand, index, total, w, last,
}) => (
  <div style={{position: 'absolute', left: w * 0.08, right: w * 0.08, bottom: w * 0.065, display: 'flex',
    justifyContent: 'space-between', alignItems: 'center', color: brand.muted, fontSize: w * 0.026, fontWeight: 600}}>
    <span>{brand.handle || brand.name}</span>
    <span style={{display: 'flex', alignItems: 'center', gap: 18}}>
      <span style={{letterSpacing: 2}}>{String(index + 1).padStart(2, '0')}/{String(total).padStart(2, '0')}</span>
      {!last ? (
        <span style={{width: w * 0.07, height: w * 0.07, borderRadius: '50%', background: brand.accent,
          color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: w * 0.04}}>
          →
        </span>
      ) : null}
    </span>
  </div>
);

const Progress: React.FC<{index: number; total: number; brand: CarouselBrand; w: number}> = ({index, total, brand, w}) => (
  <div style={{position: 'absolute', left: w * 0.08, right: w * 0.08, top: w * 0.06, display: 'flex', gap: 8}}>
    {Array.from({length: total}).map((_, i) => (
      <div key={i} style={{flex: 1, height: 6, borderRadius: 3,
        background: i <= index ? brand.accent : 'rgba(255,255,255,.18)'}} />
    ))}
  </div>
);

export const Carousel: React.FC<CarouselProps> = ({slides, brand, keyword}) => {
  const frame = useCurrentFrame();
  const w = 1080;
  const index = Math.min(frame, Math.max(0, slides.length - 1));
  const slide = slides[index];
  if (!slide) return <AbsoluteFill style={{background: brand.primary}} />;
  const last = index === slides.length - 1;
  const size = headlineSize(slide.headline, slide.role, w);
  const pad = w * 0.08;

  return (
    <AbsoluteFill style={{background: brand.primary, fontFamily: brand.font, color: brand.text}}>
      {/* a soft accent glow, off-centre, so slides are not flat fields of navy */}
      <div style={{position: 'absolute', width: w * 1.1, height: w * 1.1, borderRadius: '50%',
        right: -w * 0.55, top: slide.role === 'hook' ? -w * 0.45 : w * 0.7,
        background: `radial-gradient(circle, ${brand.accent}33 0%, transparent 62%)`}} />
      <Progress index={index} total={slides.length} brand={brand} w={w} />

      <div style={{position: 'absolute', left: pad, right: pad, top: w * 0.16, bottom: w * 0.2,
        display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
        {slide.role === 'body' ? (
          <div style={{fontSize: w * 0.16, fontWeight: 900, color: brand.accent, lineHeight: 1, opacity: 0.95,
            marginBottom: w * 0.03}}>
            {String(index).padStart(2, '0')}
          </div>
        ) : null}
        {slide.kicker ? (
          <div style={{alignSelf: 'flex-start', background: brand.accent, color: '#fff', fontWeight: 800,
            fontSize: w * 0.03, letterSpacing: 2, textTransform: 'uppercase', padding: '10px 18px',
            borderRadius: 8, marginBottom: w * 0.04}}>
            {slide.kicker}
          </div>
        ) : null}
        <div style={{fontSize: size, fontWeight: 900, lineHeight: 1.06, letterSpacing: '-0.02em'}}>
          <Emph text={slide.headline} accent={brand.accent} />
        </div>
        {slide.body ? (
          <div style={{marginTop: w * 0.045, fontSize: w * 0.041, lineHeight: 1.38, color: brand.muted,
            fontWeight: 500, whiteSpace: 'pre-line'}}>
            <Emph text={slide.body} accent={brand.accent} />
          </div>
        ) : null}
        {slide.role === 'cta' && keyword ? (
          <div style={{marginTop: w * 0.06, alignSelf: 'flex-start', border: `4px solid ${brand.accent}`,
            borderRadius: 18, padding: '22px 34px', fontSize: w * 0.05, fontWeight: 800}}>
            Comment <span style={{color: brand.accent}}>"{keyword}"</span>
          </div>
        ) : null}
      </div>

      <Footer brand={brand} index={index} total={slides.length} w={w} last={last} />
    </AbsoluteFill>
  );
};
