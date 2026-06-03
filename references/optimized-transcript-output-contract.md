# Optimized Transcript Output Contract

Use this reference after raw ASR has completed and before reporting a transcription task as finished.

## Default deliverable

For meeting recordings, the user-facing default is now the optimized transcript, not the raw ASR and not a summary.

Required files:

- `transcript_result.md` — raw provider transcript with timestamps/speaker labels.
- `transcript_result.json` — raw provider JSON / audit trail.
- `refined_transcript.md` — AI-cleaned readable transcript; this is the default final document.
- `refined_transcript.pdf` — only when the user asks for a PDF, polished file, or shareable document.

## What "optimized transcript" means

An optimized transcript is still a transcript. It preserves:

- Chronological order.
- Dialogue structure.
- Important timestamps.
- Speaker intent and oral texture.
- Concrete names, numbers, claims, and technical terms.

It improves readability by:

- Removing obvious ASR filler loops and duplicated fragments.
- Splitting wall-of-text ASR into readable turns and paragraphs.
- Normalizing clear technical terms and mixed English/Chinese phrasing.
- Relabeling weak diarization into context-based role labels when needed.

## What it must not become

Do not turn the optimized transcript into:

- A meeting summary.
- A memo.
- A diligence note.
- A bullet-only outline.
- A polished article.

If the user asks for a summary or memo, create it as a separate output, not as a replacement for `refined_transcript.md`.

## Speaker labeling

If ASR diarization is stable, keep speaker labels and optionally map them to names.

If diarization is weak, do not blindly trust `Speaker A/B/C`. Use broad role labels inferred from context, for example:

- `MoE`
- `Founder`
- `机器人团队`
- `投资人`
- `客户`
- `旁人`
- `多人/未确认`

Mark uncertainty explicitly when needed, e.g. `机器人团队（未确认）`.

## Recommended top note

```markdown
> 说明：这是基于自动转录稿整理的可读版逐字稿 / transcript，不是 summary。整理原则是保留原对话顺序、口语感和主要内容；去掉明显 ASR 噪音；对说话人不确定处用角色标签标注。
```

## Completion checklist

Before final response:

- Raw transcript exists.
- Raw JSON exists.
- Optimized transcript exists.
- Optimized transcript is chronological and dialogue-preserving.
- The file does not read like a summary/memo unless separately requested.
- Diarization caveat is stated when relevant.
- PDF exists and has been verified if requested.
