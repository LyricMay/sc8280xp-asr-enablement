# SC8280XP QAIRT Compatibility Matrix

**ID:** SC8280XP-QAIRT-CM | **Rev:** 1.0 | **Status:** Released

## 1. Target platform

| Parameter | Value |
| --- | --- |
| Board | Radxa Dragon Q8B |
| SoC | SC8280XP (`/sys/devices/soc0/machine`), `soc_id = 460` |
| DSP | Hexagon HTP v68; QNN runtime reports SA8295 |
| Memory | 30 GiB |
| OS | Armbian 26.8.1 / Ubuntu 26.04 |
| Kernel | 7.0.11-vendor-sc8280xp |
| DSP firmware | `qccdsp8280.mbn`, 3571712 bytes |

## 2. SDK version compatibility

| Version | buildId | Converter (aarch64) | Generator (aarch64) | Runtime on target | Status |
| --- | --- | --- | --- | --- | --- |
| 2.37.1.250807 | — | N/A | present | present | PASS (runtime only) |
| 2.40.1.251119 | `v2.40.1.251119112345_189394` | N/A | N/A | Genie | PASS |
| 2.42.0.251225 | `v2.42.0.251225135753_193295` | N/A | present | present | PASS |
| 2.44.0.260225 | `v2.44.0.260225` | N/A | present | present | PASS |
| 2.48.40.260702 | `v2.48.40.260702151143` | N/A | present | present | PASS |
| 2.50.0.260828 | `v2.50.0.260828221209` | present | present | present | PASS |
| 2.51.40.260930 | — | N/A | N/A | skel rejected | FAIL |

Notes:
- 2.51.40 assets contain a Genie library only; the associated skel triggers
  a CDSP fatal error and a SoC watchdog reset. See ERRATA-001.
- Only 2.50 (aarch64) ships the complete converter Python module set.
- 2.42 / 2.44 ship full converter modules only in the x86 package variant.
- The 2.50 official distribution URL is account-gated (HTTP 403 without
  credentials). This matrix does not describe acquisition methods.

### 2.1 Python requirement

| SDK | Converter interpreter |
| --- | --- |
| 2.42 / 2.44 | CPython 3.10 |
| 2.48.40 | CPython 3.12 |
| 2.50 (aarch64) | CPython 3.12 (enforced at import) |

Dependency set verified for the aarch64 converter:

```
pyyaml
setuptools
numpy==1.26.4
onnx==1.16.1
```

## 3. socModel compatibility

Enumeration from QAIRT 2.44 `QnnTypes.h`:

| Constant | Value |
| --- | --- |
| `QNN_SOC_MODEL_SM7325` | 35 |
| `QNN_SOC_MODEL_SC8280X` | 37 |
| `QNN_SOC_MODEL_SA8295` | 39 |

Radxa documented configuration:

| SoC | dsp_arch | soc_id |
| --- | --- | --- |
| QCS6490 | v68 | 35 |
| SC8280XP | v68 | 37 |
| QCS9075 | v73 | 77 |

Per the vendor model-zoo documentation, SC8280XP and QCS6490 artifacts are
mutually usable.

### 3.1 Artifact compatibility results

| Test ID | Artifact | buildId | socModel | blobVer | Status |
| --- | --- | --- | --- | --- | --- |
| TC-AM-01 | Radxa qwen LLM | 2.40.1 | 35 | 3.3.3 | PASS |
| TC-AM-02 | AI Hub whisper sa8295p | 2.42.0 | 39 | 3.3.4 | FAIL |
| TC-AM-03 | sherpa-onnx SA8295 | 2.40.0 | 39 | 3.3.3 | FAIL |
| TC-AM-04 | AI Hub QCS6490 whisper | 2.50.0 | 93 | 4.0.5 | PASS |
| TC-AM-05 | Board-generated artifact | 2.50.0 | 39 | 4.0.5 | FAIL |

TC-AM-02 and TC-AM-03 share `backendApiVersion` and `contextBlobVersion`
with TC-AM-01. `socModel` is the isolating variable.

### 3.2 ASR model family enablement

| Model family | Architecture | QCS6490 artifact | Status on target | Limit |
| --- | --- | --- | --- | --- |
| Whisper-Small-Quantized | autoregressive encoder-decoder | available | PASS | TC-AS-01 / TC-AS-02 |
| Whisper-Medium-Quantized | autoregressive encoder-decoder | available | NT | — |
| Whisper-Large-V3-Turbo-Quantized | autoregressive encoder-decoder | available | NT | — |
| SenseVoice | non-autoregressive | not published | FAIL | no QCS6490 build |
| Paraformer | non-autoregressive | not published | FAIL | no QCS6490 build |
| FireRedASR2-AED | Conformer AED + CTC | not published | FAIL | ERRATA-004 |

sherpa-onnx QNN targets: QCS9100, SA8255, SA8295, SM8350, SM8450, SM8475,
SM8550, SM8650, SM8750, SM8850. QCS6490 is absent.

## 4. Runtime backend compatibility

Environment for all cases: `LD_LIBRARY_PATH`, `ADSP_LIBRARY_PATH`,
`PRODUCT_SOC=8280`, `DSP_ARCH=68`, execution on the host.

| Test ID | Backend | Input | Result | Status |
| --- | --- | --- | --- | --- |
| TC-RT-01 | `qnn-net-run` | context binary, socModel 35/37/93 | `Finished Executing Graphs` | PASS |
| TC-RT-02 | `qnn-net-run` | context binary, socModel 39 | `Create From Binary failure` | FAIL |
| TC-RT-03 | `snpe-net-run --use_dsp` | quantized DLC | `error_code=7001` | FAIL |
| TC-RT-04 | `qairt-net-run --input_dlc --use_htp` | quantized DLC | `CAPI call failed` | FAIL |
| TC-RT-05 | `qnn-net-run --dlc_path` | quantized DLC | `Graph Execution failure` | FAIL |
| TC-RT-06 | ORT `QNNExecutionProvider` | ONNX, `soc_model=35` | execute 6001 | FAIL |
| TC-RT-07 | Genie | quantized LLM bundle | coherent output | PASS |
| TC-RT-08 | any QNN backend in container | any | `error = 4000` | FAIL |

### 4.1 ORT QNN EP provider options

Observed in `libonnxruntime_providers_qnn.so`:

```
backend_path, backend_type, soc_model, htp_arch,
enable_htp_fp16_precision, htp_performance_mode,
htp_graph_finalization_optimization_mode,
enable_htp_shared_memory_allocator, offload_graph_io_quantization
```

`soc_model` accepts numeric strings. Non-numeric values are treated as 0 and
the graph falls back to CPU. With numeric values, the graph builds and
finalizes but execution returns 6001.

## 5. Precision support

| Test ID | Configuration | Result | Status |
| --- | --- | --- | --- |
| TC-PR-01 | FP16 graph | `SocModel doesn't support FP16` | FAIL |
| TC-PR-02 | 16-bit activation quantization | `incorrect Value 68, expected >= 73` | FAIL |
| TC-PR-03 | w8a8 quantized graph | executes | PASS |
| TC-PR-04 | float graph on DSP | CDSP fatal error | FAIL |

## 6. Platform capability summary

| Capability | Status | Reference |
| --- | --- | --- |
| Quantized LLM inference | PASS | TC-RT-07 |
| Autoregressive ASR encoder-decoder execution with state passing | PASS | TC-AS-01 |
| Sustained multi-invocation ASR graph execution | PASS | TC-AS-02 |
| Arbitrary ONNX model deployment | FAIL | TC-RT-03..06, ERRATA-003 |
| Conformer ASR encoder w8a8 accuracy preservation | FAIL | ERRATA-004 |

## 7. References

- Radxa Dragon Q8B NPU documentation: qairt-usage, qairt-tools, model-zoo
- Qualcomm QAIRT / QNN SDK documentation
- See `TEST-PROCEDURE.md` for the verification method behind each test ID
