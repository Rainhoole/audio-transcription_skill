#!/usr/bin/env python3
"""Transcribe a local audio file with AssemblyAI and save raw Markdown + JSON.

Usage:
  ASSEMBLYAI_API_KEY=*** python3 transcribe_assemblyai_local.py input.m4a output_dir

Requires ffmpeg/ffprobe on PATH and Python requests installed.

This script intentionally stops at raw ASR output. The Hermes skill should run a
second AI cleanup pass afterward to create refined_transcript.md.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

BASE_URL = "https://api.assemblyai.com/v2"
SEGMENT_SECONDS = 600


def run(cmd):
    subprocess.run(cmd, check=True)


def ts(ms):
    seconds = int(ms // 1000)
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", help="Local audio file path")
    parser.add_argument("output_dir", help="Directory for audio.wav, chunks, transcript_result.*")
    parser.add_argument("--title", default=None, help="Markdown title")
    args = parser.parse_args()

    api_key = os.environ.get("ASSEMBLYAI_API_KEY")
    if not api_key:
        raise SystemExit("Set ASSEMBLYAI_API_KEY in the environment; do not hardcode it in the script.")

    source = Path(args.input_path).expanduser().resolve()
    work = Path(args.output_dir).expanduser().resolve()
    chunks_dir = work / "chunks"
    work.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    wav = work / "audio.wav"
    run(["ffmpeg", "-y", "-i", str(source), "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le", str(wav)])
    run(["ffmpeg", "-y", "-i", str(wav), "-f", "segment", "-segment_time", str(SEGMENT_SECONDS), "-c", "copy", str(chunks_dir / "chunk_%03d.wav")])

    headers = {"authorization": api_key}
    results = []
    chunks = sorted(chunks_dir.glob("chunk_*.wav"))
    print(f"Chunks: {[p.name for p in chunks]}", flush=True)

    for idx, chunk in enumerate(chunks):
        print(f"Uploading {chunk.name} ({idx + 1}/{len(chunks)})", flush=True)
        with chunk.open("rb") as f:
            resp = requests.post(f"{BASE_URL}/upload", headers=headers, data=f, timeout=300)
        resp.raise_for_status()
        audio_url = resp.json()["upload_url"]

        payload = {
            "audio_url": audio_url,
            "speech_models": ["universal-2"],
            "speaker_labels": True,
            "punctuate": True,
            "format_text": True,
        }
        resp = requests.post(f"{BASE_URL}/transcript", headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        transcript_id = resp.json()["id"]

        while True:
            time.sleep(5)
            data = requests.get(f"{BASE_URL}/transcript/{transcript_id}", headers=headers, timeout=30).json()
            status = data.get("status")
            print(f"  {chunk.name}: {status}", flush=True)
            if status == "completed":
                results.append({
                    "chunk": chunk.name,
                    "chunk_index": idx,
                    "offset_ms": idx * SEGMENT_SECONDS * 1000,
                    "transcript_id": transcript_id,
                    "text": data.get("text", ""),
                    "utterances": data.get("utterances", []),
                    "raw": data,
                })
                break
            if status == "error":
                raise RuntimeError(f"Transcription failed for {chunk.name}: {data.get('error')}")

    (work / "transcript_result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    title = args.title or f"{source.stem} - 转录稿"
    lines = [f"# {title}", "", f"原始文件：`{source}`", "", "说明：说话人标签由 AssemblyAI 自动分离，可能需要人工校正。", ""]
    for result in results:
        lines.append(f"## {result['chunk']} ({ts(result['offset_ms'])} 开始)")
        lines.append("")
        utterances = result.get("utterances") or []
        if utterances:
            for u in utterances:
                start = result["offset_ms"] + int(u.get("start") or 0)
                end = result["offset_ms"] + int(u.get("end") or 0)
                speaker = u.get("speaker", "?")
                text = (u.get("text") or "").strip()
                lines.append(f"**[{ts(start)} -> {ts(end)}] Speaker {speaker}:** {text}")
                lines.append("")
        else:
            lines.append((result.get("text") or "").strip())
            lines.append("")

    (work / "transcript_result.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved: {work / 'transcript_result.md'}")
    print(f"Saved: {work / 'transcript_result.json'}")
    print(f"Total chars: {sum(len(r.get('text', '')) for r in results)}")
    print(f"Total utterances: {sum(len(r.get('utterances') or []) for r in results)}")


if __name__ == "__main__":
    sys.exit(main())
