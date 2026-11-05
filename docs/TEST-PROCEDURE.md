# Test Procedure

**ID:** SC8280XP-QAIRT-TP | **Rev:** 1.0 | **Status:** Released

Method used to produce the entries in COMPATIBILITY-MATRIX and ERRATA.

## 1. Preconditions

- Host execution only (ERRATA-002).
- `LD_LIBRARY_PATH` and `ADSP_LIBRARY_PATH` set per ENVIRONMENT.md.
- CDSP state `running`:

```bash
cat /sys/class/remoteproc/remoteproc1/state
```

- If `offline`, reboot before testing. Do not continue with a crashed DSP.

## 2. Artifact metadata extraction (TC-AM-*)

```bash
qnn-context-binary-utility \
    --context_binary=<artifact>.bin \
    --json_file=meta.json
```

Record `socModel`, `buildId`, `contextBlobVersion`, `backendApiVersion`,
graph name, and tensor shapes/dtypes.

## 3. Context binary load (TC-RT-01 / TC-RT-02)

```bash
qnn-net-run \
    --retrieve_context=<artifact>.bin \
    --backend=<SDK>/lib/libQnnHtp.so \
    --input_list=<input list> \
    --output_dir=<out>
```

PASS criterion: output contains `Finished Executing Graphs` and at least one
non-empty tensor in `<out>/Result_0/`.

`Executing Graphs` without `Finished Executing Graphs` is a FAIL.

## 4. Input list format

One line per inference group. Multiple tensor files on a line are separated
by spaces and must follow the graph's input order, obtained from the
artifact metadata. Use `--use_native_input_files` only when reading
natively typed quantized data; otherwise the runtime reads floats and
quantizes them. `scripts/asr_workload.py` writes uint8/uint16 tensors in
`quantize()` and must pass this flag. A/B verification on the Whisper
encoder showed that omitting it does not fail the load but changes the
output tensor width (fp32 vs fp16) and the values (correlation 0.9516 on
`k_cache_cross_0`).

## 5. Backend matrix (TC-RT-03 .. TC-RT-08)

| Case | Command |
| --- | --- |
| SNPE | `snpe-net-run --container <dlc> --use_dsp --input_list <list>` |
| qairt-net-run | `qairt-net-run --input_dlc <dlc> --use_htp --input_list <list>` |
| QNN DLC | `qnn-net-run --dlc_path <dlc> --backend libQnnHtp.so --input_list <list>` |
| ORT EP | `InferenceSession(..., providers=["QNNExecutionProvider"], provider_options=[...])` |
| Genie | `genie-t2t-run -c <config> -p <prompt>` |

## 6. fp32 reference baseline (TC-PR-*, quantization work)

Reference execution uses the original ONNX graph on CPU with optimizations
disabled:

```python
session_options.graph_optimization_level = ORT_DISABLE_ALL
session = onnxruntime.InferenceSession(model, sess_options,
                                       providers=["CPUExecutionProvider"])
```

Correlation is computed between the flattened fp32 encoder output and the
flattened NPU encoder output for the same input:

```python
coef = numpy.corrcoef(fp32_output, npu_output)[0, 1]
```

Interpretation:
- coefficient near 1.0 — quantized output preserves the signal
- coefficient near 0 — output is dominated by quantization noise
- comparing standard deviation alone is insufficient; amplitude scaling
  does not recover an uncorrelated signal

## 7. Calibration procedure

Calibration inputs must use the real feature distribution of the deployed
frontend (fbank with CMVN), not synthetic normal noise. Percentile
calibration was applied to activation ranges:

```bash
qairt-quantizer --input_dlc <float.dlc> --output_dlc <quant.dlc> \
    --input_list <calibration list> \
    --act_bitwidth 8 --weights_bitwidth 8 --bias_bitwidth 8 \
    --act_quantizer_calibration percentile \
    --percentile_calibration_value 99.9
```

Calibration sample counts evaluated: 3, 10, 12, 40.

## 8. End-to-end ASR graph execution (TC-AS-01 / TC-AS-02)

TC-AS-01 uses two fixed short inputs with known reference outputs and
verifies the ASR encoder graph, cross-graph quantized tensor passing, the
autoregressive decoder loop, and token decoding.

| Input | Verification |
| --- | --- |
| short input A | decoded output matches reference text |
| short input B | decoded output matches reference text |

TC-AS-02 uses a 35.5-minute input divided into 30-second segments with
silence detection, and verifies sustained execution across 71 segment
invocations.

## 9. DSP crash handling

A crashed CDSP produces a deterministic signature (ERRATA-001/003). Record
the crash count, verify `remoteproc1/state`, and reboot before the next test.
Do not interpret results obtained while the CDSP is degraded.
