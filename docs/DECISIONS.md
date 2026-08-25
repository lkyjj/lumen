# LUMEN specification decisions

This log resolves contradictions found while converting `PLAN.md` and `HANDOVER.md` into executable
contracts. The source documents remain preserved; runtime behavior follows this file and tests.

## D-001 · Runtime length

- Decision: 95 seconds of 14 shots plus 5 seconds of end cards equals an exact 100-second master.
- Evidence: the shot table sums to 95 seconds while the plan separately allocates 5 seconds to
  system-log and title cards.
- Contract: `film.duration_target == sum(shots.duration) + title_cards_duration`.

## D-002 · Frozen authoring is the default

- Decision: `film.yaml` is the approved source. Screenwriter/storyboarder default to frozen mode and
  never overwrite its 14 shots. Regeneration must be explicit and must preserve IDs, order, duration
  and references.
- Why: silently replacing a hand-edited film contract makes review and reproducibility meaningless.

## D-003 · Anchor ownership

- Decision: S03/S08 use A; S06/S11 use B; S05/S12 use HANDS; S09 uses EVOLVED_EYES.
- Why: this matches the shot table and the intended framing. The prose that groups S11 with A is
  treated as a typo.

## D-004 · S12 hand-action exception

- Decision: keep the story beat, but frame it as a medium side view of the entire prosthetic arm
  pulling a large knife switch. Fingers are not featured and no fine button interaction is shown.
- Why: this preserves the choice while respecting the “no fine hand action” model constraint.

## D-005 · Dialogue inventory

- Decision: the frozen contract contains two utterances: one system sentence in S07 and one human
  sentence in S12. The schedule's “three system lines plus one human line” is not authoritative.

## D-006 · Quality adjudication

- Decision: pass only when the local average is at least 7.0 and every dimension is at least 6.0.
  The VLM's `overall` and `passed` fields are ignored and recalculated.

## D-007 · Video capability matrix

- Decision: dispatch by model capability, not by `startswith("wan3")` alone.
  - Wan 3.0: `input.media`, supports `ratio`.
  - Wan 2.7 I2V: `input.media`, output ratio follows first frame.
  - Wan 2.6 I2V: `input.img_url`, output ratio follows first frame.
- Routing: invited Wan 3.0 → stable Wan 2.7 → low-cost Wan 2.6 Flash → human review.

## D-008 · Pricing

- Decision: use public list prices and model-specific price tables. `discount_multiplier` defaults to
  1.0. Free quota or a campaign discount is applied only after a human confirms the control panel.
- Correction: a five-second shot costs five times the per-second price; the UI never displays the
  per-second price as the whole-shot price.

## D-009 · Human gates

- Decision: generated anchor files are candidates until each `anchors[].approved` field is committed
  as `true`. Presence of a file is not approval. Batch video also requires a recorded D9 Go/No-Go.

## D-010 · Media publication

- Decision: large generated MP4/WAV assets stay out of the Git source repository. The ModelScope
  Studio artifact repository or a release asset can carry the demo master; README/config/logs remain
  in Git. This avoids the conflict between `*.mp4` ignore rules and deployment media.

## D-011 · Reproducibility

- Decision: reproducible means replayable inputs and traceable outputs—not pixel-identical sampling.
  Config, model ID, prompts, anchors, attempts, timestamps, costs, critique, hashes and outputs are
  versioned or logged.

## D-012 · BYOK isolation

- Decision: developer providers may fall back to environment variables; Studio providers receive
  request-local keys. Studio must not mutate `os.environ`, serialize keys, cache clients across users
  or include raw provider exceptions in logs.

## D-013 · TTS default

- Decision: default to `cosyvoice-v3-flash` and an explicitly enabled system voice.
- Why: `cosyvoice-v3.5-plus/flash` only accepts cloned/designed voices. Choosing it by default would
  add an undocumented voice-creation gate. The v3.5 family remains configurable after a custom
  voice has been created and approved.
