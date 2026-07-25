# Synology Metadata (`SYNOINDEX_MEDIA_INFO`)

When Synology Photos indexes a video it writes a sidecar metadata file next to it, inside the hidden `@eaDir`
directory:

```
<directory>/@eaDir/<filename>/SYNOINDEX_MEDIA_INFO
```

Synology writes one for the original video **and** one for every derived file it generates. The transcoded stream it
produces lives at `<directory>/@eaDir/<filename>/SYNOPHOTO_FILM_H.mp4`, and its own index therefore sits one level
deeper:

```
<directory>/@eaDir/<filename>/@eaDir/SYNOPHOTO_FILM_H.mp4/SYNOINDEX_MEDIA_INFO
```

This application reads these files instead of probing every video with `ffprobe` on every cycle. See
[Why this format is worth reading](#why-this-format-is-worth-reading) for the second, less obvious reason.

## File structure

The file is a [Boost serialization](https://www.boost.org/doc/libs/release/libs/serialization/) **text archive**.
Three lines:

| Line | Content |
|------|---------|
| 1 | Archive header: `22 serialization::archive <version> 0 0 0 0 2 1 1` |
| 2 | The media record — everything this application reads |
| 3 | Trailing archive data (thumbnail geometry and flags) |

Archive versions **17** and **19** have both been observed in production, with identical field positions. The
version must not be assumed or used to select a layout.

## The encoding rule that matters

Fields are separated by single spaces, but the archive is **not** a whitespace-separated record. Strings are
serialised as a length prefix followed by the content:

```
<byte_length> <content>
```

Line 2 contains one such string that varies in width: the absolute path of the media file.

```
0 0 0 0 83 /volume1/photo/PhotoLibrary/2021/08/@eaDir/20210807_212052.mp4/SYNOPHOTO_FILM_H.mp4 0  0 …
          ▲  ▲
          │  └── exactly 83 bytes of path, then a separator space
          └───── declared length of the string that follows
```

Two properties of that length are easy to get wrong and both were verified against production files:

- **It counts bytes, not characters.** A path containing `Cumpleaños` is one byte longer than it is long in
  characters. Slicing by characters overshoots the separator.
- **It is the only reliable delimiter.** Paths legitimately contain spaces, so the field cannot be recovered by
  counting tokens.

Empty strings appear as a length of `0` followed by nothing, which is why line 2 contains runs of double spaces
(`0  0  0`). They must be preserved when copying a record into a test fixture.

## Field positions

Once the path is treated as a single token, the fields this application reads sit at fixed positions, declared in
`src/domain/constants/synology.py`:

| Index | Field | Example |
|-------|-------|---------|
| 4 | Declared byte length of the path | `83` |
| 5 | Media path (one logical field, any number of spaces) | `/volume1/photo/…` |
| 31 | Duration in seconds | `8.000000000e+00` |
| 32 | Audio bitrate | `256044` |
| 33 | Total bitrate | `5607669` |
| 34 | Video bitrate | `5342923` |
| 35 | Framerate | `30` |
| 37 | Audio sample rate | `48000` |
| 38 | Audio channels | `2` |
| 39 | Width | `720` |
| 40 | Height | `1280` |
| 41 | File size in bytes | `6097640` |
| 47 | Video codec | `h264` |
| 49 | Container format | `mp4` |
| 53 | Audio codec | `aac_lc` |

The three timestamps occupying indices 22–30 are each written as `19 YYYY-MM-DD HH:MM:SS` — a length-prefixed string
whose content contains one space, so each consumes three tokens. That shape is constant, which is why fixed indices
work for everything except the path.

## Why this format is worth reading

Two reasons this application prefers the index over invoking `ffprobe`:

1. **It is already on disk.** No subprocess per video per processing cycle.
2. **It stores display geometry, with rotation already applied.** A portrait iPhone clip is recorded as
   `1080 1920`. `ffprobe` reports the *coded* geometry — `width=1920 height=1080` — and carries the orientation
   separately as stream side data (`rotation=-90`). Any consumer of `ffprobe` output must apply that swap itself or
   it will treat the video as landscape.

`ffprobe` remains the authority where the index cannot be trusted: when it is missing, unparseable, implausible, or
when the file is output this application has just written — Synology's index of that file still describes the version
that was overwritten.

## The failure mode this parser prevents

Until 2026-07, the parser split line 2 on whitespace and indexed the positions above directly. Every space inside the
media path shifted all subsequent fields one position to the right:

| Spaces in path | Index 39 (width) actually read | Index 40 (height) actually read | Stored resolution |
|----------------|-------------------------------|--------------------------------|-------------------|
| 0 | width | height | correct |
| 1 | audio channels | width | `2x1280` |
| 2 | audio sample rate | audio channels | `44100x2` |

A production audit on 2026-07-25 found 42 affected rows out of 1356 completed transcodings. The damage was not
limited to the stored string: the same misaligned fields drove orientation, framerate and channel-count decisions,
producing 13 vertical videos encoded at 404x720 instead of 720x1280, two videos upscaled from 1080p to 2274x1280,
two downmixed from stereo to mono, and 25 fps sources re-encoded at 30 fps.

`SynoIndexMediaInfo` (`src/domain/parsers/synoindex_media_info.py`) slices the path out by its declared byte length
before tokenising, so the positions hold regardless of the path. It also applies a plausibility gate — geometry
within 16–16384 px, framerate within 1–1000 fps — and reports failure rather than returning an impossible record. A
width of `44100` is rejected at the parser and the caller falls back to `ffprobe`.

## Test fixtures

`tests/fixtures/synoindex/` holds anonymised copies of real production records. Names are replaced; the byte layout
that matters is preserved exactly — space count, multibyte characters, declared lengths, field values and archive
version.

| Fixture | Reproduces |
|---------|-----------|
| `no_spaces.txt` | Baseline, unaffected by the defect (v19) |
| `one_space.txt` | The `2x1280` corruption (v19) |
| `two_spaces.txt` | A mono source record, shifted by two positions (v19) |
| `two_spaces_transcoded.txt` | The exact `44100x2` value stored 40 times in production (v19) |
| `accented_path.txt` | Byte-versus-character slicing: 76 bytes, 75 characters (v17) |

`tests/domain/test_synoindex_media_info.py` asserts both directions for each: that a naive whitespace split
reproduces the historical corruption, and that the parser does not.
