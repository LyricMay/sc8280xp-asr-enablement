"""ASR workload: autoregressive inference on a QNN HTP context binary.

Configuration is supplied through environment variables:
    QAIRT_ROOT   - QAIRT SDK root (contains bin/ and lib/)
    MODEL_DIR    - directory with encoder.bin, decoder.bin, metadata.json
    WHISPER_HF   - Hugging Face model id for the tokenizer/feature extractor

Usage:
    python3 asr_workload.py <input.wav> [auto|zh|en] [max_tokens]

Reference: docs/COMPATIBILITY-MATRIX.md, test case TC-AS-01.
"""

import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np

QAIRT_ROOT = os.environ.get("QAIRT_ROOT", "").rstrip("/")
MODEL_DIR = os.environ.get("MODEL_DIR", "").rstrip("/")
WHISPER_HF = os.environ.get("WHISPER_HF", "openai/whisper-small")

if not QAIRT_ROOT or not MODEL_DIR:
    sys.exit("QAIRT_ROOT and MODEL_DIR must be set")

with open(os.path.join(MODEL_DIR, "metadata.json"), encoding="utf-8") as handle:
    META = json.load(handle)

ENCODER = os.path.join(MODEL_DIR, "encoder.bin")
DECODER = os.path.join(MODEL_DIR, "decoder.bin")
BACKEND = os.path.join(QAIRT_ROOT, "lib", "libQnnHtp.so")
NETRUN = os.path.join(QAIRT_ROOT, "bin", "qnn-net-run")
ENV = dict(
    os.environ,
    LD_LIBRARY_PATH=os.path.join(QAIRT_ROOT, "lib"),
    ADSP_LIBRARY_PATH=os.path.join(QAIRT_ROOT, "skel"),
)

LANG_TOKEN = {"en": 50259, "zh": 50260}
SOT, TRANSCRIBE, NO_TIMESTAMPS, EOT = 50258, 50359, 50363, 50257


def quant_params(graph, kind, name):
    return META["model_files"][graph][kind][name]["quantization_parameters"]


def quantize(array, params, max_value=255):
    scaled = np.round(array / params["scale"]) + params["zero_point"]
    dtype = np.uint16 if max_value > 255 else np.uint8
    return np.clip(scaled, 0, max_value).astype(dtype)


def read_tensor(path, shape):
    """Read a raw output tensor, auto-detecting the element width."""
    elements = int(np.prod(shape))
    size = os.path.getsize(path)
    if size == elements * 4:
        dtype = np.float32
    elif size == elements * 2:
        dtype = np.float16
    else:
        dtype = np.uint8
    return np.fromfile(path, dtype=dtype).reshape(shape).astype(np.float32)


def run_net(binary, files, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    list_path = os.path.join(output_dir, "input_list.txt")
    with open(list_path, "w", encoding="utf-8") as handle:
        handle.write(" ".join(files) + "\n")
    result = subprocess.run(
        [
            NETRUN,
            "--retrieve_context", binary,
            "--backend", BACKEND,
            "--input_list", list_path,
            "--output_dir", output_dir,
            "--use_native_input_files",
        ],
        env=ENV,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if "Finished Executing Graphs" not in (result.stdout + result.stderr):
        raise RuntimeError((result.stdout + result.stderr)[-400:])
    return os.path.join(output_dir, "Result_0")


def encoder_run(features):
    params = quant_params("encoder.bin", "inputs", "input_features")
    shape = META["model_files"]["encoder.bin"]["inputs"]["input_features"]["shape"]
    work = os.path.join(MODEL_DIR, "_work", "encoder")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    raw = os.path.join(work, "input_features.raw")
    quantize(features, params, 65535).reshape(*shape).tofile(raw)
    run_net(ENCODER, [raw], work)
    return work


def build_decoder_inputs(work, cross, self_cache, token, position, layers):
    """Write decoder tensors in the order required by the compiled graph."""
    files = []

    def put(name, array, dtype):
        path = os.path.join(work, name + ".raw")
        array.astype(dtype).tofile(path)
        files.append(path)

    put("input_ids", np.array([[token]], dtype=np.int32), np.int32)
    put("position_ids", np.array([position], dtype=np.int32), np.int32)
    for layer in range(layers):
        put(f"k_cache_self_{layer}_in",
            self_cache[f"k_cache_self_{layer}_in"], np.uint8)
        put(f"v_cache_self_{layer}_in",
            self_cache[f"v_cache_self_{layer}_in"], np.uint8)
        put(f"k_cache_cross_{layer}", cross[f"k_cache_cross_{layer}"], np.uint8)
        put(f"v_cache_cross_{layer}", cross[f"v_cache_cross_{layer}"], np.uint8)
    put("attention_mask", np.full((1, 1, 1, 200), 65535, dtype=np.uint16),
        np.uint16)
    return files


def decode_step(cross, self_cache, token, position):
    decoder_meta = META["model_files"]["decoder.bin"]
    layers = len([
        name for name in decoder_meta["inputs"]
        if name.startswith("k_cache_self_") and name.endswith("_in")
    ])
    work = os.path.join(MODEL_DIR, "_work", "decoder")
    os.makedirs(work, exist_ok=True)
    files = build_decoder_inputs(work, cross, self_cache, token, position, layers)
    result_dir = run_net(DECODER, files, work)

    logits_shape = decoder_meta["outputs"]["logits"]["shape"]
    logits = read_tensor(os.path.join(result_dir, "logits.raw"), logits_shape)
    logits = logits.reshape(-1)

    updated = {}
    for name, spec in decoder_meta["outputs"].items():
        if not name.startswith(("k_cache_self_", "v_cache_self_")):
            continue
        value = read_tensor(os.path.join(result_dir, name + ".raw"), spec["shape"])
        params = quant_params("decoder.bin", "outputs", name)
        updated[name.replace("_out", "_in")] = quantize(value, params)
    return logits, updated


def main():
    from transformers import WhisperFeatureExtractor, WhisperTokenizer
    import soundfile as sf

    wav = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "auto"
    max_tokens = int(sys.argv[3]) if len(sys.argv) > 3 else 120

    feature_extractor = WhisperFeatureExtractor.from_pretrained(WHISPER_HF)
    tokenizer = WhisperTokenizer.from_pretrained(WHISPER_HF)

    audio, sample_rate = sf.read(wav, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sample_rate != 16000:
        count = int(len(audio) * 16000 / sample_rate)
        audio = np.interp(np.linspace(0, len(audio), count),
                          np.arange(len(audio)), audio)

    features = feature_extractor(
        audio, sampling_rate=16000, return_tensors="np"
    )["input_features"].astype(np.float32)

    started = time.time()
    encoder_dir = encoder_run(features)

    encoder_meta = META["model_files"]["encoder.bin"]["outputs"]
    cross = {}
    for name, spec in encoder_meta.items():
        value = read_tensor(
            os.path.join(encoder_dir, "Result_0", name + ".raw"), spec["shape"]
        )
        params = quant_params("encoder.bin", "outputs", name)
        cross[name] = quantize(value, params)

    decoder_inputs = META["model_files"]["decoder.bin"]["inputs"]
    self_cache = {
        name: np.full(spec["shape"], 128, dtype=np.uint8)
        for name, spec in decoder_inputs.items()
        if name.startswith(("k_cache_self_", "v_cache_self_"))
    }

    position = 0
    if language == "auto":
        logits, updated = decode_step(cross, self_cache, SOT, 0)
        self_cache.update(updated)
        lang_id = 50259 + int(np.argmax(logits[50259:50299]))
        print("detected language:", tokenizer.decode([lang_id]))
        prompt = [lang_id, TRANSCRIBE, NO_TIMESTAMPS]
        position = 1
    else:
        prompt = [SOT, LANG_TOKEN.get(language, 50260),
                  TRANSCRIBE, NO_TIMESTAMPS]

    for token in prompt:
        logits, updated = decode_step(cross, self_cache, token, position)
        self_cache.update(updated)
        position += 1

    generated = []
    for _ in range(max_tokens):
        next_token = int(np.argmax(logits))
        if next_token == EOT:
            break
        generated.append(next_token)
        logits, updated = decode_step(cross, self_cache, next_token, position)
        self_cache.update(updated)
        position += 1

    elapsed = time.time() - started
    print(f"tokens={len(generated)} elapsed={elapsed:.1f}s")
    print(tokenizer.decode(generated))


if __name__ == "__main__":
    main()
