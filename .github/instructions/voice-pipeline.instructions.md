---
description: "Use when writing voice recording, VAD (voice activity detection), WebSocket audio streaming, AudioContext, MediaRecorder, TTS playback, or Whisper STT integration. Covers the full browser-to-AI-to-browser audio pipeline."
---

# Voice Pipeline Conventions

## Full Pipeline Flow

```
Browser getUserMedia
  → MediaRecorder (WebM/Opus)
  → WebSocket binary frame
  → Whisper STT (backend)
  → InputSanitizer.check()
  → text-moderation-stable
  → GPT-4o (sandwiched prompt)
  → TTS-1-HD (selected persona voice)
  → WebSocket binary frame back
  → AudioContext.decodeAudioData() → play
```

## Browser Audio Capture

Always request `{ audio: true, video: false }` — never request video in a voice-only flow.

```js
const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
```

MediaRecorder codec must be `audio/webm;codecs=opus`. Always check support before using:

```js
const mimeType = 'audio/webm;codecs=opus'
const recorder = new MediaRecorder(stream, { mimeType })
recorder.start(100)  // 100ms chunks — not a single blob at end
```

## AudioContext & AnalyserNode

Create one `AudioContext` per voice session. Connect the microphone stream to an `AnalyserNode` for VAD and waveform visualization.

```js
const ctx = new AudioContext()
const source = ctx.createMediaStreamSource(stream)
const analyser = ctx.createAnalyser()
analyser.fftSize = 256
source.connect(analyser)
```

Pass `analyser` as a prop to `AudioVisualizer` and `VADProcessor`. **Never** create a second AudioContext for the same stream.

Always close the AudioContext on cleanup:

```js
useEffect(() => {
  return () => audioContextRef.current?.close()
}, [])
```

## VAD — Voice Activity Detection

RMS energy detection from `getFloatTimeDomainData()` (not frequency data):

| Parameter | Value | Reason |
|---|---|---|
| RMS threshold | `0.015` | Empirically tuned for typical microphone levels |
| Speech start | 3 consecutive frames above threshold | Avoids false positives on noise |
| Speech end | 40 frames (~800ms at 50fps) of silence | Natural pause without cutting off |

```js
analyser.getFloatTimeDomainData(dataArray)
let sum = 0
for (let i = 0; i < bufferLength; i++) sum += dataArray[i] ** 2
const rms = Math.sqrt(sum / bufferLength)
```

## Push-to-Talk

UI must handle both mouse and touch events. Recording starts on `mousedown`/`touchstart`, stops on `mouseup`/`touchend`.

```jsx
<button
  onMouseDown={startRecording}
  onMouseUp={stopRecording}
  onTouchStart={startRecording}
  onTouchEnd={stopRecording}
/>
```

## WebSocket Protocol

| Frame type | Direction | Content |
|---|---|---|
| Text JSON `{ session_token }` | client → server | Auth handshake (first frame only) |
| Binary (`ArrayBuffer`) | client → server | WebM/Opus audio chunk |
| Binary (`ArrayBuffer`) | server → client | MP3 TTS audio response |
| Text JSON `{ type: "control", event: "question", ... }` | server → client | Question advance signal |
| Text JSON `{ type: "control", event: "completed" }` | server → client | Session end signal |

Set `ws.binaryType = 'arraybuffer'` immediately after creating the WebSocket.

## TTS Audio Playback

Decode server binary frames with `AudioContext.decodeAudioData()`, not `Audio(url)` (avoids creating object URLs that need manual revocation):

```js
const decoded = await audioCtx.decodeAudioData(arrayBuffer)
const source = audioCtx.createBufferSource()
source.buffer = decoded
source.connect(audioCtx.destination)
source.start()
```

## Backend STT / AI Orchestration

- Whisper model: `whisper-1`; pass audio as `("audio.webm", bytes, "audio/webm")`
- GPT-4o model: `gpt-4o`; always use the sandwiched system prompt from `PromptBuilder`
- TTS model: `tts-1-hd`; voice selected by `PersonaManager.get_persona()`; response format `mp3`
- Moderation: `text-moderation-stable`; any flagged category immediately terminates the session and marks it `FLAGGED` in DB

## Refocusing vs Skipping

When user response is off-topic (not necessarily flagged), use `get_refocus_phrase()` to redirect. After `MAX_REFOCUS_BEFORE_SKIP = 3` consecutive refocuses on the same question, call `get_skip_message()` and advance the state machine.

Never skip directly — exhaust refocus attempts first.
