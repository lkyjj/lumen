# Production runbook

This runbook deliberately separates free checks, low-cost smoke tests and batch production.

## Gate 0 · Rotate credentials

1. Revoke every credential previously shown in chat, screenshots or terminal history.
2. Create replacement keys with only the permissions required by this project.
3. Put replacements in a local `.env`; never commit it.
4. Confirm `git remote -v` contains no credential.

## Gate 1 · Local verification

```bash
.venv/bin/lumen validate projects/vanishing-light/film.yaml
.venv/bin/lumen run projects/vanishing-light/film.yaml --dry-run
.venv/bin/lumen run projects/vanishing-light/film.yaml --mode offline
.venv/bin/pytest
```

Expected: 14 shots, 95 seconds plus 5 seconds of titles, no network during dry-run, and a worst-case
estimate below the ¥300 cap.

## Gate 2 · Anchor approval

Inspect `projects/vanishing-light/03_bible/candidates/` at full resolution. Check:

- same face and coat in all assets;
- anatomical left eye is optical and right eye is human in present-day views;
- anatomical left forearm is metal and right arm is human;
- no resemblance to a real person or existing IP;
- no text, watermark, alpha channel or malformed anatomy.

Only the filmmaker may change `anchors[].approved` to `true`.

## Gate 3 · Minimum paid smoke test

Before sending a request, confirm the console model price and lower `hard_cap` to the exact smoke
allowance. Generate one image, one very short low-cost Wan 2.6 Flash clip with `audio=false`, and one
short TTS line. Use `max_retries=0`. Validate submit → poll → immediate download → charge → log.

If Wan 3.0 returns an invitation/permission error, do not retry it; select Wan 2.7. If Wan 2.7 fails,
select Wan 2.6 Flash. A 403 is never a reason to submit the same paid request repeatedly.

## Gate 4 · D9 Go / No-Go

Create only three test shots (recommended S03, S06, S12) at the cheapest acceptable settings.
Compare identity, eye/arm asymmetry, composition and temporal stability.

- `GO`: record the decision and approved model/settings.
- `PLAN_B`: switch visible-face shots to rear view, silhouette and prosthetic-arm inserts.
- `STOP`: do not batch generate.

## Batch and review

Generate one shot at a time. Preserve every attempt as `Sxx_attempt_01.mp4`, etc. The critic may
request at most two retries and must pass a concrete `fix_hint` into the next prompt. After three
failed attempts, stop and mark the shot for human review.

## Master and publication

The editor must verify: 14 clips; H.264; at least 1280×720; 95-second picture sequence; 5-second
end cards; final duration 100 seconds; audible but non-clipping mix. Publish large media separately
from the source repository, then configure Studio demo mode with a deployment-local media path.
