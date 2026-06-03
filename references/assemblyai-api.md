# AssemblyAI API Reference

## Endpoints

- Upload: `POST https://api.assemblyai.com/v2/upload`
- Submit: `POST https://api.assemblyai.com/v2/transcript`
- Query: `GET https://api.assemblyai.com/v2/transcript/{transcript_id}`

## Auth

```python
HEADERS = {"authorization": "your-api-key"}
```

## Submit Payload

```python
{
    "audio_url": "https://...",           # from upload response
    "speech_models": ["universal-2"],      # REQUIRED: plural list, not singular
    "speaker_labels": True,                # enables speaker diarization
    "punctuate": True,                     # adds punctuation
    "format_text": True,                   # improves formatting
    # Optional:
    "language_detection": True,            # auto-detect language
    "auto_highlights": True,               # topic detection
}
```

## Response (completed)

```python
{
    "id": "transcript_id",
    "status": "completed",
    "text": "full transcript text",
    "words": [{"text": "...", "start": 0, "end": 500, "speaker": "A"}],
    "utterances": [
        {
            "start": 0,
            "end": 3500,
            "text": "今天...",
            "speaker": "A"
        }
    ],
    "confidence": 0.95,
    "audio_duration": 6312,   # milliseconds
}
```

## Status Values

- `queued` — waiting
- `processing` — in progress
- `completed` — done
- `error` — failed

## Error: speech_model deprecated

If you get: `'"speech_models" must be a non-empty list...'`

The API changed — `speech_model` (singular) is no longer accepted. Use:

```python
"speech_models": ["universal-2"]   # list format required
```

## Upload Response

```python
{"upload_url": "https://cdn.assemblyai.com/upload/a1b2c3..."}
# Use this URL as audio_url in the submit payload
```
