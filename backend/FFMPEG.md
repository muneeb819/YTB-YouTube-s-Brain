# FFmpeg Pipeline

The runtime uses ffprobe to inspect uploaded assets and FFmpeg to render.

Current functional render:
- trim by start time
- optional duration
- stream-copy when possible
- H.264/AAC re-encode fallback
- fast-start MP4 output

Extend the same deterministic boundary for:
- captions
- audio ducking
- B-roll insertion
- transitions
- loudness normalization
- 16:9/9:16 layouts
- thumbnail frames
- multi-track audio
