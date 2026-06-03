---
name: audio-transcription
description: >
  Use when transcribing meeting recordings, voice memos, or long-form audio into raw ASR plus an AI-optimized readable transcript. Covers local audio conversion, chunking, AssemblyAI upload/polling, raw Markdown/JSON output, transcript cleanup, diarization caveats, and optional PDF generation.
version: 1.0.0
author: Rainhoole
license: Apache-2.0
platforms: [linux, macos, windows, wsl]
metadata:
  hermes:
    tags: [audio, transcription, speech-to-text, meeting-notes, assemblyai, whisper, ffmpeg]
    related_skills: []
---

# Audio Transcription Skill

## Workflow Overview

```
Local Audio File
       │
       ▼
┌──────────────────┐
│  Format Convert  │  m4a/AAC/48kHz → 16kHz mono PCM/WAV
│  (ffmpeg)        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Chunking        │  Split into ≤10min segments (30min API limit)
│  (ffmpeg seg)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Upload          │  AssemblyAI/Deepgram: multipart upload (no public URL needed)
│  (provider API)  │  Others (豆包/Volcengine): require public URL — harder for local files
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Transcribe      │  Submit job → poll → collect result
│  (provider API)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Merge + Save    │  Combine chunks, format as raw Markdown + JSON
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  AI Transcript   │  Run a second AI pass: readable optimized transcript
│  Optimization    │  (not summary/memo) + optional PDF on request
└──────────────────┘
```

## Provider Comparison

| Provider | Upload Method | Free Tier | Best For |
|---|---|---|---|
| **AssemblyAI** | Multipart file upload (no public URL needed) | 5h/month | Easiest — local files just work |
| **Deepgram** | Multipart file upload | 150h/month | High volume, lower cost |
| **Whisper (local)** | No upload, runs locally | Free | Privacy-sensitive, no internet needed |
| **豆包/Volcengine** | Requires public URL | Unknown | Chinese audio (but setup complex) |

## Step-by-Step: AssemblyAI (Recommended)

### 1. Format Convert

```bash
# m4a/AAC/any → 16kHz mono WAV (required by most APIs)
ffmpeg -y -i "input.m4a" -ar 16000 -ac 1 -acodec pcm_s16le "audio.wav"
```

### 2. Chunk (for audio >10 min)

```bash
mkdir -p chunks
# Split into 10-minute segments (600s)
ffmpeg -y -i "audio.wav" \
  -f segment -segment_time 600 \
  -c copy "chunks/chunk_%03d.wav"
```

### 3. Transcribe (Python)

```python
import os, requests, json, time

API_KEY = "your-key"
HEADERS = {"authorization": API_KEY}
BASE_URL = "https://api.assemblyai.com/v2"
CHUNK_DIR = "chunks"

chunks = sorted([f for f in os.listdir(CHUNK_DIR) if f.endswith(".wav")])
all_results = []

for chunk in chunks:
    filepath = os.path.join(CHUNK_DIR, chunk)

    # Upload (multipart — no public URL needed!)
    with open(filepath, "rb") as f:
        resp = requests.post(f"{BASE_URL}/upload", headers=HEADERS, data=f, timeout=300)
    resp.raise_for_status()
    audio_url = resp.json()["upload_url"]

    # Submit — CRITICAL: use speech_models (plural), not speech_model
    payload = {
        "audio_url": audio_url,
        "speech_models": ["universal-2"],   # ← MUST be plural list
        "speaker_labels": True,
        "punctuate": True,
        "format_text": True,
    }
    resp = requests.post(f"{BASE_URL}/transcript", headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    tid = resp.json()["id"]

    # Poll
    while True:
        time.sleep(5)
        d = requests.get(f"{BASE_URL}/transcript/{tid}", headers=HEADERS, timeout=15).json()
        if d["status"] == "completed":
            all_results.append({"chunk": chunk, "text": d["text"], "utterances": d.get("utterances", [])})
            break
        elif d["status"] == "error":
            print(f"Error: {d.get('error')}")
            break
```

### 4. Merge Results: Raw Transcript

Always save the raw AssemblyAI output first. This is the audit trail and fallback source.

```python
with open("transcript_result.md", "w", encoding="utf-8") as f:
    f.write("# 会议录音转录结果\n\n")
    for r in all_results:
        f.write(f"## {r['chunk']}\n\n")
        for utt in r.get("utterances", []):
            speaker = utt.get("speaker", "?")
            start_s = utt["start"] / 1000
            end_s = utt["end"] / 1000
            f.write(f"[{int(start_s//60):02d}:{int(start_s%60):02d}] Speaker {speaker}: {utt['text']}\n")
        f.write("\n")
```

### 5. Second Pass: Optimized Transcript (Default User-Facing Output)

After raw transcription, run one AI cleanup pass and save a readable transcript as `refined_transcript.md`. This is now the default final output for meeting recordings unless the user explicitly asks for raw-only, summary, memo, or minutes.

**Important: optimized transcript is not a summary.** Preserve conversation order and the transcript nature. Do not convert it into a meeting memo, investment note, or bullet-only summary.

Optimization rules:

1. Preserve the original chronological order and timestamp sections.
2. Keep the speaker's oral texture and informal wording, but remove obvious ASR noise such as repeated filler loops, duplicated words, and broken token spacing.
3. Split very long ASR paragraphs into readable turns and paragraphs by semantic boundaries.
4. Lightly correct obvious ASR errors and normalize common technical terms (`BEV`, `OpenDriveLab`, `Figure`, `Sonic`, `Physical Intelligence`, `π0.5`, `whole-body intelligence`, `foundation model`, `teleop`, `MPC`, `action space`, `GTM`).
5. If diarization is weak, do not blindly trust `Speaker A/B/C`. Relabel by context as role labels such as `机器人团队`, `MoE`, `客户`, `投资人`, `旁人`, or `多人/未确认`.
6. Add a short note at the top explaining that it is an AI-optimized readable transcript, not a summary, and that speaker labels may be context-inferred.
7. Do not invent facts, quotes, names, or numbers. If uncertain, mark `[未确认]` or keep the raw phrase.
8. Preserve important timestamps at least by 5-10 minute sections; include exact timestamps for clear speaker turns when available.
9. Save raw outputs and optimized output side by side:
   - `transcript_result.md` — raw timestamped transcript
   - `transcript_result.json` — raw provider JSON
   - `refined_transcript.md` — optimized readable transcript
   - `refined_transcript.pdf` — only if user asks for PDF or polished document output

Recommended optimized transcript structure:

```markdown
# <title> - 优化后 Transcript

> 说明：这是基于自动转录稿整理的可读版逐字稿 / transcript，不是 summary。整理原则是保留原对话顺序、口语感和主要内容；去掉明显 ASR 噪音；对说话人不确定处用角色标签标注。

---

## 00:00 - 00:10 <short section label>

**[00:00:05] <Speaker/Role>：**

<cleaned utterance>

**<Speaker/Role>：**

<cleaned response>

---
```

If the user asks for a PDF, convert `refined_transcript.md` to `refined_transcript.pdf` after the cleanup pass and verify page count/text extraction.

## Pitfalls

- **豆包/Volcengine requires public URL**: local files are unusable unless you upload to TOS first. AssemblyAI is vastly simpler for local files.
- **AssemblyAI `speech_model` deprecated**: must use `speech_models: ["universal-2"]` (plural, list format). Using the old singular key returns an error.
- **Audio length limits**: AssemblyAI free tier 5h/month. 豆包 30min per job. Chunk long recordings.
- **Diarization can be weak**: for Chinese informal single-channel audio, early chunks may collapse into one speaker/utterance. The second AI pass should infer broad role labels from context, but must mark uncertainty instead of pretending voiceprint accuracy.
- **Optimized transcript ≠ summary**: default post-processing should produce a cleaned transcript that preserves order and dialogue. Only create a summary/memo/minutes when the user asks for it.
- **PDF is optional**: raw + `refined_transcript.md` are default; create `refined_transcript.pdf` when the user asks for a PDF/polished document.

## Support Files

- `references/assemblyai-api.md` — API quirks, endpoint details, request/response shapes
- `references/ffmpeg-audio处理.md` — ffmpeg conversion and chunking commands
- `references/assemblyai-local-meeting-notes.md` — local WeChat/Windows-path meeting transcription notes, output layout, diarization caveats, and API key handling.
- `references/optimized-transcript-output-contract.md` — default post-ASR deliverable contract: raw outputs plus AI-cleaned `refined_transcript.md`, preserving transcript form rather than summary/memo.
- `scripts/transcribe_chunks.py` — ready-to-run transcription script
- `scripts/transcribe_assemblyai_local.py` — reusable local-file AssemblyAI pipeline that converts, splits, uploads, polls, and writes raw Markdown + JSON. After running it, perform the required AI cleanup pass to create `refined_transcript.md` (and PDF if requested).
