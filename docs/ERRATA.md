# Errata

**ID:** SC8280XP-QAIRT-ER | **Rev:** 1.0 | **Status:** Released

Known limitations on the target platform. Each entry records the observed
signature and the workarounds that were tested and found ineffective.

---

## ERRATA-001 — 2.51.40 skel triggers a watchdog reset

**Affected:** QAIRT 2.51.40.260930 skel on HTP v68.

**Signature:**

```
qcom_q6v5_pas 1b300000.remoteproc: fatal error received
remoteproc remoteproc1: crash detected in cdsp: type fatal error
PM: Reset by PSHOLD
Warm reset detected without ramdump, performing hard reset
```

**Effect:** system reboot required. CDSP remains `offline` afterwards;
`echo start > /sys/class/remoteproc/remoteproc1/state` returns
`can't start rproc cdsp: -110`.

**Workaround:** use SDK versions listed as PASS in COMPATIBILITY-MATRIX §2.

---

## ERRATA-002 — QNN does not initialize inside containers

**Affected:** all evaluated SDK versions (2.37.1, 2.40.1, 2.42).

**Signature:**

```
Unable to initialize logging in the backend
error = 4000
```

**Ruled out:** device nodes (`/dev/fastrpc-cdsp` created and cgroup
permission granted), seccomp, IPC/PID namespaces, `/dev/log` symlink,
`libcdsprpc` version mismatch, SDK version.

**Workaround:** run QNN on the host.

---

## ERRATA-003 — Context binaries are not forward compatible

**Affected:** QAIRT context binaries.

**Signature:** `Create From Binary failure` or `err 0x3ea` when a binary
produced by a newer SDK is loaded by an older runtime; the reverse direction
is also unsupported.

**Related:** `socModel` must match the target. Patching the metadata field
does not change the compiled code inside the binary.

| Attempted workaround | Result |
| --- | --- |
| Generator `--htp_socs` with four different SoC names | artifact socModel unchanged |
| Generator `--config_file` with `soc_id` / `soc_model` | unchanged |
| `QNN_FORCE_FIREWHEEL_SOCID` | unchanged |
| Editing DLC `soc_model` metadata | unchanged |
| Direct binary patch of the socModel field | utility reports the new value; load still fails |
| Converter `--target_soc_model SC8280X` | rejected as unsupported |

**Workaround:** obtain an artifact built for a compatible target, or build
with a toolchain matching the target runtime.

---

## ERRATA-004 — Quantization accuracy limit on Conformer ASR encoders

**Affected:** w8a8 post-training quantization of Conformer-based ASR
encoder graphs on HTP v68.

**Measurement:** encoder output correlated against an fp32 reference on
identical input.

| Configuration | Correlation coefficient |
| --- | --- |
| fp32 reference | 1.000 |
| min-max w8a8 | 0.050 |
| CLE | 0.081 |
| per-channel weights | 0.099 |
| percentile 99.9 | 0.466 |
| percentile 99.9 + 12 real calibration samples | 0.556 |
| percentile 99.9 + 40 real calibration samples | 0.557 |
| AIMET PTQ encodings | not deployable, see below |

**Observed:** CTC decoding produced isolated correct tokens but not complete
sentences. Frame alignment was correct; the logits dynamic range collapsed
toward the blank class.

**Ruled out:**
- 16-bit activation quantization (ERRATA-005)
- float fallback (requires QAT encodings)
- `--onnx_skip_simplification`
- CLE combined with percentile calibration (no additional gain)
- recalibrating the CTC head independently (breaks the encoder/CTC amplitude
  coupling)
- increasing calibration samples beyond 12 (plateau at 0.557)
- AIMET PTQ: encodings are name-compatible, but the
  `--quantization_overrides` path retains unquantized float tensors and the
  offline compiler rejects the mixed-precision graph on v68

**Status:** open. The measured correlation loss is established for the
evaluated W8A8 PTQ configurations. The cause is not yet isolated. The
following have not been ruled out: numerical change during ONNX-to-DLC
conversion, calibration preprocessing differing from the original frontend,
a single dominant Conformer operator or normalization layer, and a mismatch
in quantization encodings, output tensor order or layout. Intermediate
tensor-level error comparison has not been performed.

This entry is separate from ERRATA-003 and ERRATA-007, which concern
context binary SoC binding and on-device generated artifacts.

---

## ERRATA-005 — 16-bit precision not available on v68

**Affected:** FP16 graphs, 16-bit activation quantization, 16-bit overrides
on sensitive layers.

**Signature:**

```
<E> The SocModel doesn't support FP16
<E> [4294967295] has incorrect Value 68, expected >= 73
```

**Effect:** offline graph finalization fails. v73 or newer is required.

**Workaround:** none on this hardware.

---

## ERRATA-006 — ORT QNN EP graph execution aborts

**Affected:** `onnxruntime_qnn` 1.23.2 with QAIRT 2.42 and 2.50 libraries.

**Signature:** EP registration, backend load, device and context creation,
graph construction (validation passed) and finalization complete. Execution
returns 6001 in 22 us, indicating a host-side rejection before DSP dispatch.

**Ruled out:** model complexity, w8a8 quantization, skel path,
`PRODUCT_SOC` / `DSP_ARCH`, FP16 settings, dspqueue symbols.

**Status:** open.

---

## ERRATA-007 — On-device generated context binaries are rejected

**Affected:** `qnn-context-binary-generator` executed on the aarch64 target.

**Signature:** generation completes; `qnn-net-run` on the same board reports
`Create From Binary failure`. Generated artifacts consistently carry
socModel 39 regardless of converter or generator SoC settings.

**Ruled out:** converter target SoC, generator `--htp_socs`, generator
config file, environment variables, DLC metadata modification, binary
patching.

**Status:** open. See ERRATA-003 for the underlying binding rule.
