# INSLIGHT — Voice Assistant & Speech Synthesis Guide
**Phase 2: Voice Accessibility Architecture**

---

## 1. Overview

The INSLIGHT Voice Assistant provides voice accessibility for business analytics inquiries and executive narrative narration. It allows business analysts and executives to dictate questions in natural language and listen to spoken executive summaries.

---

## 2. Technical Architecture

```text
User Speech (Mic) ──► Browser Web Speech API (en-IN, hi-IN, kn-IN)
                              │
                              ▼
                     Transcript Populated
                     in Editable Input
                              │
               (User Reviews & Clicks Send)
                              │
                              ▼
                   Authenticated Query API
                              │
                              ▼
                  AI Synthesis (Groq LLaMA)
                              │
                              ▼
           AI Narrative ──► Browser Speech Synthesis API (TTS)
```

---

## 3. Speech Recognition Implementation (`VoiceInput.tsx`)

### 3.1 Browser Web Speech API
- Implemented using standard browser `window.SpeechRecognition` and `window.webkitSpeechRecognition`.
- Detects whether the current browser supports speech recognition natively (e.g. Google Chrome, Microsoft Edge).
- When unsupported, displays an informative fallback tooltip ("Web Speech API not supported in this browser. Use Chrome or Edge").

### 3.2 Multilingual Support
Configured with regional BCP 47 language codes:
1. **English (India):** `en-IN`
2. **हिन्दी (Hindi):** `hi-IN`
3. **ಕನ್ನಡ (Kannada):** `kn-IN`

### 3.3 State Machine & Error Handling
- **Idle:** Displays mic icon 🎙️.
- **Listening:** Pulsing red indicator 🔴 with "Listening... Speak your business question".
- **Permission Denied:** Catches `event.error === 'not-allowed'` and alerts the user to permit microphone access in browser settings.
- **Empty Speech:** Catches `event.error === 'no-speech'` and resets gracefully.
- **Network Glitches:** Catches `event.error === 'network'` and advises retrying.

### 3.4 Strict Human-in-the-Loop Review
To prevent accidental analytical queries or prompt injection from background speech:
- Speech recognition **never executes queries automatically**.
- The transcribed text is populated directly into the standard chat `<input>` field.
- The user can review, edit, fix technical terms or numbers, and press Enter / click Send.

### 3.5 Privacy Guarantees
- Audio streams are processed client-side via the browser's speech recognition engine.
- No raw audio is recorded, transferred, or stored on backend servers.
- A built-in privacy notice pill (ℹ️) explains these protections directly to the user.

---

## 4. Text-to-Speech (AI Voice Response - `VoiceControls.tsx`)

### 4.1 Speech Synthesis API
- Uses `window.speechSynthesis` and `SpeechSynthesisUtterance`.
- **Opt-in Only:** Disabled by default. Users enable it via the "AI Voice Response" checkbox. The preference is persisted in `localStorage`.
- **Sanitized Speech Content:**
  - Strips markdown formatting (`**`, `##`, `_`).
  - Omits code blocks and raw SQL statements to prevent listening to tedious query syntax.
  - Limits speech to the first 350 characters of executive narrative for concise listening.
- **Interactive Controls:** Provides "🔊 Read Aloud" and "⏹️ Stop" buttons for manual playback control.
