// Defaults matching env.example
const DEFAULTS = {
  hw_transcoding:      true,
  execution_threads:   2,
  startup_delay:       30,
  execution_interval:  240,
  video_codec:         'h264_high',
  video_bitrate:       2000,
  video_resolution:    '720p',
  audio_codec:         'aac_lc',
  audio_bitrate:       128,
  audio_channels:      '2',
};

function syncAudioChannels() {
  const codec = document.getElementById('audio_codec');
  const channels = document.getElementById('audio_channels');
  const hint = document.getElementById('hint-hev2-stereo');
  if (!codec || !channels) return;
  const locked = codec.value === 'aac_he_v2';
  channels.disabled = locked;
  if (locked) channels.value = '2';
  if (hint) hint.style.visibility = locked ? 'visible' : 'hidden';
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('btn-reset')?.addEventListener('click', () => {
    const form = document.getElementById('settings-form');
    if (!form) return;
    Object.entries(DEFAULTS).forEach(([name, value]) => {
      const el = form.elements[name];
      if (!el) return;
      if (el.type === 'checkbox') {
        el.checked = value;
      } else {
        el.value = value;
      }
    });
    syncAudioChannels();
  });

  document.getElementById('audio_codec')?.addEventListener('change', syncAudioChannels);
  syncAudioChannels();
});
