#!/usr/bin/env python3
"""Create a seed SQLite database for dashboard screenshot capture."""
import sqlite3
import sys

DB_PATH = sys.argv[1] if len(sys.argv) > 1 else "seed.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER NOT NULL PRIMARY KEY,
    hw_transcoding BOOLEAN NOT NULL,
    execution_threads INTEGER NOT NULL,
    startup_delay INTEGER NOT NULL,
    execution_interval INTEGER NOT NULL,
    video_codec VARCHAR(20) NOT NULL,
    video_bitrate INTEGER NOT NULL,
    video_resolution VARCHAR(10) NOT NULL,
    video_profile VARCHAR(30),
    audio_codec VARCHAR(20) NOT NULL,
    audio_bitrate INTEGER NOT NULL,
    audio_channels INTEGER NOT NULL,
    audio_profile VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS transcodings (
    original_video_path VARCHAR(1000) NOT NULL PRIMARY KEY,
    transcoded_video_path VARCHAR(1000) NOT NULL,
    transcoded_video_resolution VARCHAR(20) NOT NULL,
    transcoded_video_codec VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_original_path ON transcodings (original_video_path);
CREATE INDEX IF NOT EXISTS idx_status ON transcodings (status);
"""

SETTINGS = (
    1,      # id
    1,      # hw_transcoding
    2,      # execution_threads
    1440,   # startup_delay  — prevents scanner from running during capture
    1440,   # execution_interval
    "h264", # video_codec
    2000,   # video_bitrate
    "720p", # video_resolution
    "high", # video_profile
    "aac",  # audio_codec
    128,    # audio_bitrate
    2,      # audio_channels
    "aac_lc", # audio_profile
)

ROWS = [
    # completed — h264, various resolutions
    ("/media/photos/vacation/2023/beach_sunset.mp4",       "/media/photos/vacation/2023/@eaDir/beach_sunset.mp4/SYNOPHOTO_FILM_H.mp4",       "1280x720",  "h264", "completed",    None),
    ("/media/photos/vacation/2023/pool_afternoon.mp4",     "/media/photos/vacation/2023/@eaDir/pool_afternoon.mp4/SYNOPHOTO_FILM_H.mp4",     "1920x1080", "h264", "completed",    None),
    ("/media/photos/vacation/2023/market_walk.mp4",        "/media/photos/vacation/2023/@eaDir/market_walk.mp4/SYNOPHOTO_FILM_H.mp4",        "1280x720",  "h264", "completed",    None),
    ("/media/user1/wedding/ceremony.mov",                  "/media/user1/wedding/@eaDir/ceremony.mov/SYNOPHOTO_FILM_H.mp4",                  "1920x1080", "h264", "completed",    None),
    ("/media/user1/wedding/reception_dance.mp4",           "/media/user1/wedding/@eaDir/reception_dance.mp4/SYNOPHOTO_FILM_H.mp4",           "3840x2160", "hevc", "completed",    None),
    ("/media/user1/birthday/cake_blowout.mp4",             "/media/user1/birthday/@eaDir/cake_blowout.mp4/SYNOPHOTO_FILM_H.mp4",             "1280x720",  "hevc", "completed",    None),
    ("/media/photos/family/christmas_2022.mp4",            "/media/photos/family/@eaDir/christmas_2022.mp4/SYNOPHOTO_FILM_H.mp4",            "1920x1080", "h264", "completed",    None),
    ("/media/photos/family/new_year_fireworks.mp4",        "/media/photos/family/@eaDir/new_year_fireworks.mp4/SYNOPHOTO_FILM_H.mp4",        "3840x2160", "hevc", "completed",    None),
    # failed
    ("/media/user2/trips/japan_tokyo_timelapse.mp4",       "/media/user2/trips/@eaDir/japan_tokyo_timelapse.mp4/SYNOPHOTO_FILM_H.mp4",       "1920x1080", "h264", "failed",       "Error opening input file: No such file or directory"),
    ("/media/user2/trips/kyoto_temple.mp4",                "/media/user2/trips/@eaDir/kyoto_temple.mp4/SYNOPHOTO_FILM_H.mp4",                "1280x720",  "h264", "failed",       "Conversion failed: Invalid data found when processing input"),
    ("/media/photos/vacation/2022/corrupted_clip.mp4",     "/media/photos/vacation/2022/@eaDir/corrupted_clip.mp4/SYNOPHOTO_FILM_H.mp4",     "1280x720",  "h264", "failed",       "Error opening input file: Invalid argument"),
    # pending
    ("/media/user1/sports/marathon_finish.mp4",            "/media/user1/sports/@eaDir/marathon_finish.mp4/SYNOPHOTO_FILM_H.mp4",            "1920x1080", "h264", "pending",      None),
    ("/media/user1/sports/cycling_tour.mp4",               "/media/user1/sports/@eaDir/cycling_tour.mp4/SYNOPHOTO_FILM_H.mp4",               "1280x720",  "h264", "pending",      None),
    # in_progress
    ("/media/photos/family/summer_bbq.mp4",                "/media/photos/family/@eaDir/summer_bbq.mp4/SYNOPHOTO_FILM_H.mp4",                "1920x1080", "hevc", "in_progress",  None),
    # not_required
    ("/media/user2/archive/old_recording.mp4",             "/media/user2/archive/@eaDir/old_recording.mp4/SYNOPHOTO_FILM_H.mp4",             "640x480",   "h264", "not_required", None),
]

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.executescript(SCHEMA)
c.execute(
    "INSERT OR REPLACE INTO settings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
    SETTINGS,
)
c.executemany(
    "INSERT OR REPLACE INTO transcodings VALUES (?,?,?,?,?,?)",
    ROWS,
)
conn.commit()
conn.close()

counts = {status: sum(1 for r in ROWS if r[4] == status) for status in {r[4] for r in ROWS}}
print(f"Seeded {DB_PATH}: {len(ROWS)} rows — {counts}")
