# Local / Offline Operation

1. Install FFmpeg.
2. Install Ollama locally.
3. Download a local chat model in Ollama.
4. Set AI_PROVIDER=ollama.
5. Start the YTB API.
6. Keep all media in the local workspace.

The AI generation layer can remain local. Web research, current platform-policy refresh,
cloud providers and YouTube publishing require internet and are intentionally optional.

Offline operation does not mean current policy knowledge: if disconnected, YTB should use
the last-known-good policy snapshot and clearly show its age.
