# Audio Transcription Skill

A production-oriented Hermes Agent skill for converting local meeting recordings into high-quality, readable transcripts.

This skill is designed for long-form audio such as WeChat voice recordings, Zoom calls, founder meetings, expert calls, diligence calls, and internal strategy discussions. It uses a two-stage workflow:

1. **Raw transcription**: convert, chunk, upload, transcribe, and save auditable raw Markdown + JSON.
2. **AI transcript refinement**: run a second AI pass to produce a clean, readable transcript while preserving the original conversation order.

The default output is **not a summary**. It is an optimized transcript: chronological, dialogue-preserving, easier to read, and suitable for review or downstream memo generation.

---

## Why This Skill Exists

Most transcription workflows stop at raw ASR output. That is rarely enough for real meetings:

- Speaker labels are often wrong, especially on single-channel Chinese or mixed-language audio.
- Long utterances become unreadable walls of text.
- ASR systems produce repeated fillers, broken token spacing, and domain-specific errors.
- Technical terms such as `foundation model`, `teleop`, `MPC`, `BEV`, `OpenDriveLab`, or `Physical Intelligence` often need normalization.
- Users usually need a document they can actually read, not just a provider dump.

This skill solves that by always preserving the raw provider output first, then creating a cleaned transcript as the user-facing deliverable.

---

## Capabilities

- Transcribe local audio files without requiring a public URL.
- Convert common audio formats (`m4a`, `mp3`, `wav`, `aac`, etc.) to 16 kHz mono WAV.
- Split long recordings into stable 10-minute chunks.
- Upload chunks to AssemblyAI using multipart local file upload.
- Save raw timestamped transcript and raw provider JSON.
- Run a second AI pass to create a polished transcript, not a summary.
- Preserve chronological flow, dialogue structure, timestamps, and oral texture.
- Handle weak diarization by using context-derived role labels.
- Optionally render the optimized transcript as PDF.

---

## Default Workflow

```text
Local audio file
  -> ffmpeg conversion
  -> 10-minute chunks
  -> AssemblyAI transcription
  -> transcript_result.md
  -> transcript_result.json
  -> AI cleanup pass
  -> refined_transcript.md
  -> optional refined_transcript.pdf
```

### Output Files

A typical run creates:

```text
~/transcribe_work/<recording_slug>/
  audio.wav
  chunks/
    chunk_000.wav
    chunk_001.wav
    ...
  transcript_result.md       # raw timestamped ASR transcript
  transcript_result.json     # raw provider response, including utterances
  refined_transcript.md      # optimized readable transcript, default final output
  refined_transcript.pdf     # optional, only when requested
```

The raw files are the audit trail. The refined transcript is the document most people should read.

---

## Installation

Clone this repository or install/copy the skill into your Hermes skills directory.

```bash
git clone https://github.com/Rainhoole/audio-transcription_skill.git
```

For Hermes Agent, place the skill folder under:

```bash
~/.hermes/skills/media/audio-transcription/
```

or use your preferred Hermes skill installation method.

---

## Requirements

### System Dependencies

- `ffmpeg`
- `ffprobe`
- Python 3.10+
- Python package: `requests`

On Ubuntu / WSL:

```bash
sudo apt update
sudo apt install -y ffmpeg
python3 -m pip install requests
```

If your environment is PEP 668-managed, use a virtual environment or `uv` instead of global pip.

```bash
uv venv .venv
source .venv/bin/activate
uv pip install requests
```

### API Key

AssemblyAI is the default provider because it supports direct local file upload.

```bash
export ASSEMBLYAI_API_KEY="your_assemblyai_key"
```

Do not hardcode API keys into scripts. Keep secrets in environment variables or your Hermes profile configuration.

---

## Usage

### In Hermes Agent

Ask Hermes to transcribe a local recording:

```text
转录这个录音：/path/to/meeting.m4a
```

For WeChat files on WSL, paths often look like:

```text
/mnt/d/WeChat Files/<username>/FileStorage/File/2026-06/meeting.m4a
```

The skill should:

1. Inspect the audio file and duration.
2. Convert it to 16 kHz mono WAV.
3. Split it into chunks.
4. Transcribe with AssemblyAI.
5. Save raw Markdown and JSON.
6. Run the optimized transcript pass.
7. Return paths to the raw and refined outputs.

### Script-Based Usage

If using the included reusable script pattern:

```bash
ASSEMBLYAI_API_KEY="your_key" \
python3 scripts/transcribe_assemblyai_local.py \
  "/path/to/input.m4a" \
  "~/transcribe_work/my_meeting" \
  --title "My Meeting"
```

This script produces the raw transcript and JSON. The Hermes skill then performs the required AI cleanup pass to create `refined_transcript.md`.

---

## The Optimized Transcript Pass

The second pass is the most important part of the skill.

### What It Does

- Keeps the transcript chronological.
- Keeps the conversation as dialogue.
- Removes obvious ASR artifacts.
- Splits long blocks into readable turns.
- Normalizes technical terms when context is clear.
- Relabels speakers by role when diarization is weak.
- Preserves uncertainty instead of pretending accuracy.

### What It Does Not Do

- It does not summarize the meeting by default.
- It does not turn the transcript into a memo.
- It does not invent names, numbers, facts, or decisions.
- It does not silently erase uncertainty.
- It does not publish or share the recording.

### Recommended Refined Transcript Format

```markdown
# <Meeting Title> - 优化后 Transcript

> 说明：这是基于自动转录稿整理的可读版逐字稿 / transcript，不是 summary。
> 整理原则是保留原对话顺序、口语感和主要内容；去掉明显 ASR 噪音；
> 对说话人不确定处用角色标签标注。

---

## 00:00 - 00:10 <short section label>

**[00:00:05] Speaker / Role：**

Cleaned utterance.

**Speaker / Role：**

Cleaned response.

---
```

### Speaker Labeling Guidance

Raw diarization labels such as `Speaker A`, `Speaker B`, and `Speaker C` are useful only when they are stable. For noisy, informal, or single-channel audio, they may be misleading.

When diarization is weak, use role labels inferred from context:

- `MoE`
- `Founder`
- `机器人团队`
- `投资人`
- `客户`
- `旁人`
- `多人/未确认`

When unsure, mark uncertainty explicitly:

```markdown
**[00:23:41] 机器人团队（未确认）：**
```

---

## Example

### Raw ASR

```markdown
**[00:10:00 -> 00:19:59] Speaker A:** 并 转 的 一个 状态 你 这 Figure 他们 在 干嘛 Figure 他们其实现在做的事都很好然后不过他们最近放了很多 demo...
```

### Optimized Transcript

```markdown
## 00:10 - 00:20 Figure、硬件路线、融资与数据成本

**[00:10:00] 机器人团队：**

Figure 最近放了很多 demo，比如 BattleRoom、厨房那些，确实很有意思。人形机器人难点在于全身控制能不能像 demo 里那么丝滑。如果能做到那种程度，teleop 可以做很多事情。

但我们听说 Figure 整个 pipeline 还是偏 replay，每个任务、每个 step 都会用特调的 MPC，而不是一个非常 general 的 tracker。
```

The refined version is still a transcript. It is not a summary: it preserves the original topic flow and the speaker's intent.

---

## PDF Output

PDF generation is optional. Use it when the user asks for a polished document or shareable file.

Recommended flow:

1. Generate `refined_transcript.md`.
2. Convert Markdown to HTML or PDF using your local renderer.
3. Verify the PDF exists, page count is nonzero, and Chinese text is extractable.

Example with WeasyPrint:

```bash
weasyprint refined_transcript.html refined_transcript.pdf
```

For Chinese text, make sure your system has a CJK font installed, such as:

- WenQuanYi Zen Hei
- Noto Sans CJK
- Microsoft YaHei
- Source Han Sans

---

## Path Handling on WSL

When users provide Windows paths, translate them to WSL paths before processing.

```text
D:\WeChat Files\...  ->  /mnt/d/WeChat Files/...
C:\Users\...         ->  /mnt/c/Users/...
```

Always quote paths because WeChat filenames often contain spaces, Chinese characters, and symbols such as `&`.

```bash
ffprobe "/mnt/d/WeChat Files/user/FileStorage/File/2026-06/李天羽 & 李弘扬.m4a"
```

---

## Quality Checklist

Before reporting completion, verify:

- The source file exists.
- Audio duration was inspected.
- WAV conversion succeeded.
- Chunks were generated.
- All chunks were transcribed.
- `transcript_result.md` exists.
- `transcript_result.json` exists.
- `refined_transcript.md` exists.
- The refined transcript is chronological and dialogue-preserving.
- The refined transcript is not a summary unless explicitly requested.
- Diarization caveats are clearly stated.
- If PDF was requested, `refined_transcript.pdf` exists and has extractable text.

---

## Troubleshooting

### AssemblyAI rejects the request

Use `speech_models`, not the deprecated singular `speech_model` field.

```json
{
  "speech_models": ["universal-2"]
}
```

### Speaker labels are bad

This is common for single-channel informal recordings. Keep the raw diarization in `transcript_result.json`, but use context-derived role labels in `refined_transcript.md`.

### Long audio fails or times out

Split into 10-minute chunks. Do not submit very long files as a single job.

### Chinese text does not render in PDF

Install a CJK font and configure your PDF renderer to use it.

On Ubuntu / WSL:

```bash
sudo apt install -y fonts-wqy-zenhei fonts-noto-cjk
```

### Local files do not work with Doubao / Volcengine

Many providers require a public audio URL. AssemblyAI and Deepgram support direct local file upload, which is why this skill defaults to AssemblyAI.

---

## Security and Privacy

- Do not hardcode API keys.
- Do not commit audio files or transcripts containing sensitive meeting content.
- Keep raw JSON output private if it includes word-level timestamps or speaker metadata.
- Use local Whisper if recordings are too sensitive to upload to a third-party provider.
- Treat optimized transcripts as sensitive documents unless the user explicitly says otherwise.

---

## Recommended Hermes Skill Behavior

When this skill is loaded for a transcription request, the agent should treat the job as complete only after the optimized transcript exists.

Minimum final response:

```text
转录完成。

- Raw transcript: <path>/transcript_result.md
- Raw JSON: <path>/transcript_result.json
- Optimized transcript: <path>/refined_transcript.md
- PDF: <path>/refined_transcript.pdf  # only if requested
- Duration: <duration>
- Chunks: <count>
- Caveat: speaker labels are automatic and may need correction
```

---

## License

Apache-2.0. See [LICENSE](LICENSE).
