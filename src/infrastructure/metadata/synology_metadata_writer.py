"""Synology metadata file writer."""
from pathlib import Path
from typing import Optional

from domain.models.video import Video
from domain.constants.synology import MetadataIndex


class SynologyMetadataWriter:
    """Writes/updates metadata in Synology .SYNO files."""
    
    @staticmethod
    def update_metadata(transcoded_video_path: str, transcoded_video: Video) -> bool:
        """
        Updates the Synology metadata file with transcoded video information.
        
        The metadata file for the transcoded video is located at:
        <original_video_directory>/@eaDir/<original_video_filename>/@eaDir/<transcoded_filename>/SYNOINDEX_MEDIA_INFO
        
        For example, if the original is `video.mp4` and transcoded is `SYNOPHOTO_FILM_H.mp4`:
        <dir>/@eaDir/video.mp4/@eaDir/SYNOPHOTO_FILM_H.mp4/SYNOINDEX_MEDIA_INFO
        
        This method reads the existing file, updates only the known fields
        (according to MetadataIndex), and writes it back, preserving all
        unknown fields.
        
        Args:
            transcoded_video_path: Full path to the transcoded video file (e.g., SYNOPHOTO_FILM_H.mp4)
            transcoded_video: Video object with transcoded video metadata
            
        Returns:
            True if update succeeded, False otherwise
        """
        transcoded_file = Path(transcoded_video_path)
        # The metadata file is in @eaDir/<transcoded_filename>/SYNOINDEX_MEDIA_INFO
        syno_file = transcoded_file.parent / '@eaDir' / transcoded_file.name / "SYNOINDEX_MEDIA_INFO"
        
        # If file doesn't exist, we can't update it
        if not syno_file.exists():
            return False
        
        try:
            # Read the file
            with open(syno_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # The main data is in line 2 (index 1)
            if len(lines) < 2:
                return False
            
            # Parse line 2 into tokens
            tokens = lines[1].strip().split()
            
            # Update known fields based on MetadataIndex
            # Ensure we have enough tokens
            max_index = max(
                MetadataIndex.DURATION.value,
                MetadataIndex.AUDIO_BITRATE.value,
                MetadataIndex.TOTAL_BITRATE.value,
                MetadataIndex.VIDEO_BITRATE.value,
                MetadataIndex.FRAMERATE.value,
                MetadataIndex.SAMPLE_RATE.value,
                MetadataIndex.CHANNELS.value,
                MetadataIndex.WIDTH.value,
                MetadataIndex.HEIGHT.value,
                MetadataIndex.FILE_SIZE.value,
                MetadataIndex.VIDEO_CODEC.value,
                MetadataIndex.CONTAINER.value,
                MetadataIndex.AUDIO_CODEC.value
            )
            
            # Extend tokens if necessary
            while len(tokens) <= max_index:
                tokens.append("0")
            
            # Update fields from transcoded video
            # Duration (seconds)
            if transcoded_video.container.duration > 0:
                tokens[MetadataIndex.DURATION.value] = f"{transcoded_video.container.duration:.9e}"
            
            # Audio bitrate (convert from kbps to bps)
            if transcoded_video.audio_track.bitrate > 0:
                tokens[MetadataIndex.AUDIO_BITRATE.value] = str(int(transcoded_video.audio_track.bitrate * 1000))
            
            # Video bitrate (convert from kbps to bps)
            if transcoded_video.video_track.bitrate > 0:
                tokens[MetadataIndex.VIDEO_BITRATE.value] = str(int(transcoded_video.video_track.bitrate * 1000))
            
            # Total bitrate (audio + video)
            total_bitrate = transcoded_video.container.total_bitrate
            if total_bitrate > 0:
                tokens[MetadataIndex.TOTAL_BITRATE.value] = str(int(total_bitrate * 1000))
            elif transcoded_video.video_track.bitrate > 0 and transcoded_video.audio_track.bitrate > 0:
                total = (transcoded_video.video_track.bitrate + transcoded_video.audio_track.bitrate) * 1000
                tokens[MetadataIndex.TOTAL_BITRATE.value] = str(int(total))
            
            # Framerate
            if transcoded_video.video_track.framerate > 0:
                tokens[MetadataIndex.FRAMERATE.value] = str(transcoded_video.video_track.framerate)
            
            # Sample rate (audio sample rate - not directly available, keep existing or use default)
            # We don't have this in Video model, so we preserve the existing value
            
            # Channels
            if transcoded_video.audio_track.channels > 0:
                tokens[MetadataIndex.CHANNELS.value] = str(transcoded_video.audio_track.channels)
            
            # Width and Height
            if transcoded_video.video_track.width > 0:
                tokens[MetadataIndex.WIDTH.value] = str(transcoded_video.video_track.width)
            if transcoded_video.video_track.height > 0:
                tokens[MetadataIndex.HEIGHT.value] = str(transcoded_video.video_track.height)
            
            # File size (bytes)
            if transcoded_video.container.file_size > 0:
                tokens[MetadataIndex.FILE_SIZE.value] = str(transcoded_video.container.file_size)
            
            # Video codec
            if transcoded_video.video_track.codec_name:
                tokens[MetadataIndex.VIDEO_CODEC.value] = transcoded_video.video_track.codec_name
            
            # Container format
            if transcoded_video.container.format:
                tokens[MetadataIndex.CONTAINER.value] = transcoded_video.container.format
            
            # Audio codec
            if transcoded_video.audio_track.codec:
                tokens[MetadataIndex.AUDIO_CODEC.value] = transcoded_video.audio_track.codec
            
            # Reconstruct line 2
            lines[1] = ' '.join(tokens) + '\n'
            
            # Write back
            with open(syno_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            return False
