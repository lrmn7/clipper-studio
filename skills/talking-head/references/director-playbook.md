# Director Playbook: beat → visual → typography → SFX

| Beat (what the speaker does) | Visual / effect | Typography | Position | SFX |
|---|---|---|---|---|
| Hook, 0–3.5s (bold claim/question) | punch zoom + hook card / glass-hook / one-big-slam | 2–5 words, biggest size | behind head or upper third | 1 impact/whoosh |
| Asks a question / names a problem | spotlight darken around the face, question card | a question in an accent color | upper third (below 13.5%) | soft riser |
| Says a number, %, price, date | stat card, counter, bento, glass-track | the number huge, label small | lower third, below the chin | tick/pop |
| Lists items (pertama, kedua…) | checklist / stack / sticker-stack | 1 line per item, staggered | lower-mid | light tick per item |
| Comparison (A vs B, naik/turun) | split, toggles, arrows | two contrasting colors | lower third | switch click |
| Key word / emphasis | spotlight-word, zoom-in 1.1–1.2× | single word | behind head | none or subtle |
| Pause / breath / topic change | B-roll (crop of a relevant area, generated board, screen), whip transition | none | full frame / glass panel | whoosh |
| Story / emotion | slow push-in, vignette, desaturation | minimal serif | lower | none |
| Climax / verdict | verdict card, slam | conclusion in 3–6 words | center-low | impact |
| CTA / outro | outro card ("follow untuk part 2") | short CTA | lower, left of the right rail | soft chime |

## Pacing
- 1 visual event every 2–4s. Calm topics: 4–6s.
- Max 2 simultaneous overlays. Captions hide during big cards and B-roll.
- Don't over-edit podcasts: let real reactions breathe.

## Captions
- Chunks of 2–5 words, synced to `.words.json`, highlight 1 key word per chunk at most.
- Never scroll lyric-style lines, and never animate every word with sound.

## SFX rules
- Every SFX must match a visual event. Silence is fine.
- Mix the SFX 12–18 dB below the voice. Serious topics: fewer and deeper. Fun topics: more and brighter.
- Style 11 / "clean audio" requests: zero SFX.

## Quality checklist before the final render
1. Faces and eyes are never covered (check the stills at hook, data, B-roll, outro).
2. Everything sits inside the safe zones (top 13.5%, bottom 77.2%, right 83.5% in the lower half).
3. Spelling of numbers and names matches the corrected transcript.
4. Fonts contain every glyph (avoid → · in PermanentMarker).
5. Contrast ≥ 4.5:1 on text over the video (add a scrim or glass behind it if needed).
