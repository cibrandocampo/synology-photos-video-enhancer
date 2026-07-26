# Upgrading

Guidance for moving from an older version. Each entry starts from something you can **observe** —
a value in the dashboard, a count that moved, a container that is no longer there — because that is
usually what sends you looking, not the version number you happen to be on.

This is not a changelog. Only two kinds of entry belong here: upgrades that need you to do something,
and behaviour changes that would otherwise look like a regression. Everything else lives in the
[release notes](https://github.com/cibrandocampo/synology-photos-video-enhancer/releases).

Every entry states which versions it applies to, so entries can be removed once nobody is upgrading
from that far back.

---

## Odd resolutions in the dashboard: `44100x2`, `2x1280`

**Applies to**: databases written by **4.2.2 or earlier**. The repair tool ships in **4.2.4**.

### What you would see

The dashboard's resolution distribution lists values that are not resolutions — `44100x2` is an audio
sample rate next to a channel count, `2x1280` is a channel count next to a width. Affected videos may
also be visibly wrong: portrait clips encoded far too narrow, or a file larger than the original.

### What happened

`SYNOINDEX_MEDIA_INFO`, Synology's metadata index, stores strings as `<byte_length> <content>` —
including the media path. Older versions split that record on whitespace, so **every space in a media
path shifted all the following fields by one position**. Width and height then read the audio sample
rate and channel count. Album names like `2020 Family Trip` are enough to trigger it.

The damage was not limited to the stored value. The same misaligned fields decided orientation,
framerate and channel count, so affected files were encoded with the wrong settings — not merely
described incorrectly. See [Synology metadata](synology-metadata.md) for the format and the full
analysis.

### What to do

1. **Upgrade to 4.2.4 or later first.** This matters: re-encoding while an older image is running
   reproduces the original damage, because the old parser is what produces the wrong settings.

2. **Run the repair in dry-run mode.** It writes nothing and prints what it would do:

   ```bash
   docker exec synology-photos-video-enhancer \
     python /app/scripts/repair_transcoding_metadata.py --verbose
   ```

3. **Read the summary before going further.** It separates records whose *file* is wrong and needs
   re-encoding from records whose file is fine and only the stored values are stale. Expect the
   re-encode count to be higher than the number of odd resolutions you can see: files whose geometry
   came out right by chance can still carry the wrong framerate, and videos Synology never indexed were
   encoded with a guessed framerate of 30.

4. **Apply it.**

   ```bash
   docker exec synology-photos-video-enhancer \
     python /app/scripts/repair_transcoding_metadata.py --apply
   ```

   Stale records are corrected immediately. Files needing a re-encode are reset to `pending`, and the
   next scheduled run reprocesses them — each one costs a full transcode, so a large queue takes a
   while on a low-power NAS. `--limit N` processes only the first N records if you would rather
   rehearse on a handful first.

Back up `transcodings.db` before step 4 if the database matters to you. Videos whose paths contain no
spaces were never affected.

---

## Re-encoded videos report a different frame rate than before

**Applies to**: upgrades to **4.3.0 or later**.

### What you would see

Videos re-encoded after the upgrade report frame rates they did not report before. Clips that used to read
30 fps now read 29.97. Some report no single rate at all. If you run the repair tool, it queues far more
files than it did on 4.2.4 — potentially most of your library.

### What happened

Frame rate handling was wrong in three places at once, and all three are fixed together.

Synology's index stores the frame rate as a **numerator and a denominator** in two adjacent fields. Earlier
versions read the numerator alone and rounded it, so an NTSC video storing `30000 1001` — a rate of
29.97 fps — was treated as 30. In the production library measured for this change, 41% of indexed videos
carry such a fractional rate. The target rate was then truncated to a whole number on its way to FFmpeg,
turning 29.97 into 29, and a source whose rate could not be read at all was simply assumed to be 30.

The practical effect of encoding a 29.97 fps source at 30 is about one duplicated frame every thirty
seconds, which drifts audio against video over a long clip.

Two behaviours are new rather than merely corrected:

- **The output rate is never higher than the source's.** A source at a rate with no standard equivalent at
  or below it keeps its own rate instead of being pushed to the nearest one.
- **Variable-rate sources keep their variable cadence.** Screen recordings and phone clips that spend frames
  only where there is motion are no longer forced to a constant rate. Doing so either duplicated frames the
  camera chose not to record or discarded frames it chose to keep — larger either way. Detecting this
  requires probing the file, so source videos are now probed first and Synology's index is the fallback.

See [Supported formats](supported-formats.md) for the resulting rules.

### What to do

**Nothing is required.** Existing files keep working; they are simply encoded at a slightly different rate
than they would be today. If you never run the repair tool, nothing is re-encoded.

If you want the library brought in line, the repair tool now judges the frame rate as well as the geometry:

```bash
docker exec synology-photos-video-enhancer \
  python /app/scripts/repair_transcoding_metadata.py --verbose
```

**Read the dry-run summary before applying it.** Expect a much larger re-encode queue than the earlier
entry on this page describes: that one covered files damaged by a parsing defect, a few dozen in a library
of thousands. This one covers every file whose frame rate differs from what the current rules would
produce. Measured against a real library of 1356 transcoded videos, that was **26% of the files whose
frame rate could be judged**, or 17% of the library as a whole — dominated by 59.94 fps phone recordings
that were previously halved to a flat 30 fps instead of 29.97. Your proportion depends on how many of your
videos come from phones. Each queued file costs a full transcode, and the queue is worked through by the
normal processing cycle — on a low-power NAS that is measured in days, not minutes.

**When to run it is an operational choice, not a correctness one.** The existing files are watchable. Use
`--limit N` to work through the library in batches if you would rather not hand the NAS a queue of
thousands at once.

Variable-rate sources are exempt from the frame-rate comparison, because there is no single rate their
output should carry. When such a record is queued for another reason, the summary says so rather than
leaving you to wonder why one axis was not judged.

---

## More failures reported after upgrading

**Applies to**: upgrades to **4.2.3 or later**.

### What you would see

The dashboard's failure count rises on the first run after upgrading, listing videos that were
previously reported as transcoded.

### What happened

This is intended, and it is not a regression. Older versions, when they could not determine a video's
dimensions, fell back to placeholder values and transcoded anyway — with guessed orientation and
framerate. From 4.2.3 a video whose geometry cannot be determined, neither from Synology's index nor by
probing the file, is recorded as `failed` and left untouched.

The files those records point at were already being produced incorrectly. The change is that the
problem is now visible instead of silent.

### What to do

Nothing is required. Check the error list on the dashboard: each entry names the video and the reason.
A common cause is a file the container cannot read, which is a permissions issue on the host rather
than a problem with the video.

Note that `not_required` is not a failure: it means Synology never generated a transcoded version for
that video, so there is nothing for this tool to improve.

---

## Coming from the Grafana-based dashboard

**Applies to**: upgrades from **3.x or earlier** to **4.0.0 or later**.

### What you would see

The `grafana` and `grafana-init` containers are gone from the new `docker-compose.yml`, and the old
dashboard on port `3000` no longer responds.

### What happened

4.0.0 replaced the Grafana stack with a dashboard built into the application, served from the same
process. No extra container, no external service.

### What to do

- **Pull the new image** and redeploy.
- **Edit `.env`** — add `WEB_USER`, `WEB_PASSWORD` (required) and `WEB_SECRET_KEY` (required). Generate
  the secret with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Optionally set
  `WEB_PORT` and `WEB_COOKIE_SECURE`. Remove the now-defunct `GRAFANA_*` variables.
- **Update `docker-compose.yml`** — the current template no longer contains the `grafana` or
  `grafana-init` services. If you copied the previous compose locally, drop those service blocks
  yourself.
- **Optionally delete `./grafana-data`** on the host — leftover state from the old container.
- **Update DSM's reverse proxy** — replace the rule pointing at port `3000` with one pointing at
  `${WEB_PORT:-9200}`.

See [Dashboard](https://github.com/cibrandocampo/synology-photos-video-enhancer#dashboard) for
endpoints and authentication, and the [Configuration Guide](configuration.md) for the full variable
reference.
