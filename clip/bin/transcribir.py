import sys, wave, numpy as np, sherpa_onnx, json, time

M = "/opt/asr/sherpa-onnx-whisper-small"
wav_path, out_json = sys.argv[1], sys.argv[2]

rec = sherpa_onnx.OfflineRecognizer.from_whisper(
    encoder=f"{M}/small-encoder.int8.onnx",
    decoder=f"{M}/small-decoder.int8.onnx",
    tokens=f"{M}/small-tokens.txt",
    language="es", task="transcribe", num_threads=4,
)

vc = sherpa_onnx.VadModelConfig()
vc.silero_vad.model = "/opt/asr/silero_vad.onnx"
vc.silero_vad.threshold = 0.45
vc.silero_vad.min_silence_duration = 0.45
vc.silero_vad.min_speech_duration = 0.25
vc.silero_vad.max_speech_duration = 14.0
vc.sample_rate = 16000
vad = sherpa_onnx.VoiceActivityDetector(vc, buffer_size_in_seconds=240)

with wave.open(wav_path) as w:
    assert w.getframerate() == 16000 and w.getnchannels() == 1
    pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
samples = (pcm / 32768.0).astype(np.float32)

segmentos, t0 = [], time.time()
CH = 8000
def vaciar():
    while not vad.empty():
        s = vad.front
        ini = s.start / 16000.0
        fin = ini + len(s.samples) / 16000.0
        st = rec.create_stream(); st.accept_waveform(16000, s.samples); rec.decode_stream(st)
        txt = st.result.text.strip()
        vad.pop()
        if txt:
            segmentos.append({"ini": round(ini, 2), "fin": round(fin, 2), "texto": txt})
            print(f"[{ini:7.2f} → {fin:7.2f}] {txt}", flush=True)

for i in range(0, len(samples), CH):
    vad.accept_waveform(samples[i:i+CH])
    vaciar()
vad.flush(); vaciar()

json.dump(segmentos, open(out_json, "w"), ensure_ascii=False, indent=1)
print(f"\n{len(segmentos)} segmentos en {time.time()-t0:.0f}s -> {out_json}", flush=True)
