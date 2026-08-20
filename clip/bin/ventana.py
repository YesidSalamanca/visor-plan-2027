import sys, wave, numpy as np, sherpa_onnx
M="/opt/asr/sherpa-onnx-whisper-small"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(
    encoder=f"{M}/small-encoder.int8.onnx", decoder=f"{M}/small-decoder.int8.onnx",
    tokens=f"{M}/small-tokens.txt", language="es", task="transcribe", num_threads=4)
with wave.open(sys.argv[1]) as w:
    pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
s = (pcm/32768.0).astype(np.float32)
for a,b in [(float(x.split('-')[0]), float(x.split('-')[1])) for x in sys.argv[2:]]:
    st = rec.create_stream(); st.accept_waveform(16000, s[int(a*16000):int(b*16000)]); rec.decode_stream(st)
    print(f"[{a:6.1f}-{b:6.1f}] {st.result.text.strip()}", flush=True)
