# AssemblyAI Local Meeting Workflow

Condensed from the former `audio-transcription-workflow` skill.

## Scope

Use for local meeting recordings where AssemblyAI is the preferred provider because it supports direct multipart file upload without a public URL.

## Workflow

1. Convert source audio to 16 kHz mono WAV with ffmpeg.
2. Split long audio into about 10-minute chunks.
3. Upload each chunk to `https://api.assemblyai.com/v2/upload` with the `authorization` header.
4. Submit transcription jobs to `/v2/transcript` using `speech_models: ["universal-2"]`.
5. Poll `/v2/transcript/{id}` until completed or error.
6. Merge chunk transcripts into Markdown and JSON.
7. If requested, generate meeting minutes with topic, decisions, action items, owners, and open questions.

## Key API Quirks

- Use `speech_models` as a list, not deprecated singular `speech_model`.
- Direct local file upload works; no public URL hosting is required.
- Speaker labels are useful for 2-4 speakers.
- Typical processing can be roughly 20-40 seconds per 10-minute chunk.

## Fallback Providers

- Deepgram: direct file upload and high free tier.
- Whisper/faster-whisper: local and private, no upload.
- Speechmatics: direct upload.

## Contrast With Public-URL Providers

Providers such as Doubao/Volcengine may require public URLs or object storage. Prefer AssemblyAI/Deepgram/Whisper for local WSL files unless the user specifically chooses another provider.
