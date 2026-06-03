# AssemblyAI Local Meeting Transcription Notes

Operational notes for local meeting audio transcription, especially Windows/WSL recordings and informal single-channel conversations.

## Recommended output layout

Use a stable per-recording work directory, for example:

```text
~/transcribe_work/<slug>/
  audio.wav
  chunks/chunk_000.wav
  chunks/chunk_001.wav
  transcript_result.md
  transcript_result.json
  refined_transcript.md
```

The final user-facing response should include the raw Markdown path, raw JSON path, optimized transcript path, audio duration, number of chunks, total text chars, utterance count, and any diarization caveat.

## Path handling

For local audio in WSL, paths may already be absolute under `/mnt/<drive>/...`. If the user gives a Windows path, translate it first:

- `D:\Meetings\recording.m4a` -> `/mnt/d/Meetings/recording.m4a`
- `C:\Users\Name\Downloads\recording.m4a` -> `/mnt/c/Users/Name/Downloads/recording.m4a`

Quote paths because filenames often include spaces, non-ASCII characters, and symbols such as `&`.

## Diarization caveat

AssemblyAI may return valid text but poor speaker segmentation for noisy, single-channel, or informal meeting audio. Some chunks may collapse into one utterance / one speaker, while later chunks have normal `A/B/C` separation. Treat this as a quality caveat rather than a transcription failure.

When reporting completion, explicitly say speaker labels are automatic and may need manual correction, especially if some chunks have only one utterance.

## API key handling

Do not hardcode the AssemblyAI key in reusable scripts. Prefer `ASSEMBLYAI_API_KEY` and keep one-off session scripts out of the skill library.
