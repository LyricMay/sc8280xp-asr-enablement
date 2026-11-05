# ASR Workload Specification

**ID:** SC8280XP-QAIRT-AW | **Rev:** 1.0

This document specifies the ASR workload used to verify end-to-end graph
execution on the target. ASR model enablement is one of the two project
scopes defined in README. The evaluated model families and their measured
limits are listed in COMPATIBILITY-MATRIX §3.2 and ERRATA-004.

The workload described here is an autoregressive ASR encoder-decoder model
in QNN context binary form. It exercises multi-graph execution, quantized
tensor passing between graphs, acoustic feature input, and autoregressive
state handling.

## 1. Artifact

| Property | Value |
| --- | --- |
| Model family | quantized autoregressive ASR encoder-decoder |
| Artifact precision | w8a16 |
| Target | `qualcomm_qcs6490` context binary |
| Artifact socModel | 93 |
| buildId | `v2.50.0.260828221209` |
| Files | `encoder.bin`, `decoder.bin`, `metadata.json` |

The artifact is not distributed with this repository.

## 2. Graph specification

### Encoder

| Tensor | Shape | Dtype | Quantization |
| --- | --- | --- | --- |
| `input_features` | `[1, 80, 3000]` | uint16 | scale `4.677007e-05`, zero point 32072 |
| `k_cache_cross_0..11` | `[12, 1, 64, 1500]` | uint8 | per-tensor from metadata |
| `v_cache_cross_0..11` | `[12, 1, 1500, 64]` | uint8 | per-tensor from metadata |

### Decoder

| Tensor | Shape | Dtype |
| --- | --- | --- |
| `input_ids` | `[1, 1]` | int32 |
| `position_ids` | `[1]` | int32 |
| `k_cache_self_0..11` | `[12, 1, 64, 199]` | uint8 |
| `v_cache_self_0..11` | `[12, 1, 199, 64]` | uint8 |
| `k_cache_cross_0..11` | `[12, 1, 64, 1500]` | uint8 |
| `v_cache_cross_0..11` | `[12, 1, 1500, 64]` | uint8 |
| `attention_mask` | `[1, 1, 1, 200]` | uint16 |
| `logits` | `[1, 51865, 1, 1]` | uint16, scale `0.00129254`, zp 17867 |
| `k_cache_self_*_out` | `[12, 1, 64, 199]` | uint8 |

### Special tokens

```
SOT = 50258, en = 50259, zh = 50260,
transcribe = 50359, no_timestamps = 50363, EOT = 50257
```

## 3. Input order

`qnn-net-run` consumes tensor files in the order defined by the compiled
graph. For this decoder:

```
input_ids, position_ids,
(k_cache_self_i, v_cache_self_i, k_cache_cross_i, v_cache_cross_i) x 12,
attention_mask
```

Other model variants use different orders. Determine the order from
`qnn-context-binary-utility` output or the execution metadata YAML. The
in-process `PythonBackendManager` API matches tensors by name, so order is
not significant there.

## 4. Quantization handling

- Encoder input is uint16. The clip bound must be 65535. Clipping to 255
  collapses the acoustic features to a constant and produces output
  unrelated to the input signal.
- Encoder and decoder outputs are dequantized by the runtime into floats.
  Re-quantize them with the per-tensor `scale` / `zero_point` from
  `metadata.json` before feeding them to the next graph.
- Self-attention caches are initialized to zero (encoded as zero point 128).
- After each decode step, replace the self-cache inputs with the
  corresponding graph outputs, re-quantized.
- `attention_mask` is set to all-valid (65535).

## 5. Execution

```bash
export QAIRT_ROOT=<SDK_ROOT>
export MODEL_DIR=<DIRECTORY_WITH_THE_ARTIFACT>
export WHISPER_HF=openai/whisper-small

python3 scripts/asr_workload.py <input.wav> auto [max_tokens]
```

The script performs: acoustic feature extraction, encoder graph execution,
cross-cache quantization, prompt steps, greedy autoregressive decode, and
token decoding.

## 6. Verification results

| Test | Input | Result |
| --- | --- | --- |
| TC-AS-01 | short utterance A | expected reference text, correct |
| TC-AS-01 | short utterance B | expected reference text, correct |
| TC-AS-02 | 35.5-minute recording | 71 timestamped chunks, 8262 characters |

TC-AS-02 processing time was 56.9 minutes for 35.5 minutes of input
(RTF about 1.6). Each decoded token invokes one `qnn-net-run` process;
process startup dominates. In-process execution reduces per-token latency
to 19-96 ms but requires matching the graph state (see ERRATA-006).

## 7. Chunking

Chunk length is 30 seconds, matching the encoder input width. Silent chunks
are skipped. Output is timestamped text. Script conversion is applied as a
post-processing step where required.

## 8. Observed limits

- Autoregressive decoding is slower than non-autoregressive alternatives on
  the same board.
- The model emits no punctuation or case normalization.
- Accuracy on noisy recordings is lower than on clean utterances.
