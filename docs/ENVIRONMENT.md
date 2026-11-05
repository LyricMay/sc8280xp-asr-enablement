# Environment Guide

**ID:** SC8280XP-QAIRT-EG | **Rev:** 1.0

## 1. Runtime variables

Set on the host. QNN does not initialize in containers (ERRATA-002).

```bash
export LD_LIBRARY_PATH=<SDK_ROOT>/lib
export ADSP_LIBRARY_PATH=<SDK_ROOT>/skel
export PRODUCT_SOC=8280
export DSP_ARCH=68
```

`ADSP_LIBRARY_PATH` must point to the directory containing
`libQnnHtpV68Skel.so`. Omitting it causes device creation to fail with 1008.

## 2. Device nodes

FastRPC device nodes must exist in `/dev` and be permitted by the device
cgroup. Missing nodes produce error 14001 at device creation.

Verify DSP state:

```bash
cat /sys/class/remoteproc/remoteproc1/state
```

`running` is required. `offline` after a crash requires a reboot.

## 3. Python environment (aarch64 converter)

QAIRT 2.50 aarch64 requires CPython 3.12. Other versions are listed in
COMPATIBILITY-MATRIX §2.1.

```
pyyaml
setuptools
numpy==1.26.4
onnx==1.16.1
```

Rationale for pinned versions:
- `setuptools` supplies `distutils`, removed in Python 3.12.
- `onnx` 1.17+ removed the `onnx.version` submodule used by the converter.
- `numpy` 2.5.x triggers an `addFloat()` argument-type error in the IR layer.

Additional packages for the ASR workload:

```
onnxruntime-qnn==1.23.2
transformers
soundfile
kaldi-native-fbank
sentencepiece
zhconv
```

## 4. Backend extension configuration

Two files are required by `qnn-context-binary-generator`.

`config_backend.json`:

```json
{
  "graphs": [{"graph_names": ["<GRAPH_NAME>"], "vtcm_mb": 0}],
  "devices": [{"dsp_arch": "v68", "soc_id": 37}]
}
```

`config_file.json`:

```json
{
  "backend_extensions": {
    "shared_library_path": "<SDK_ROOT>/lib/libQnnHtpNetRunExtensions.so",
    "config_file_path": "<ABSOLUTE_PATH>/config_backend.json"
  }
}
```

`graph_names` must match the graph name reported by:

```bash
qairt-dlc-info -i <model>.dlc | grep "Info of graph"
```

`soc_id` values are defined in COMPATIBILITY-MATRIX §3.

## 5. Conversion sequence

```bash
# 1. ONNX -> DLC
qairt-converter \
    --input_network model.onnx \
    --output_path model.dlc \
    --source_model_input_shape <NAME> <DIMS> \
    --target_backend HTP

# 2. Quantization (an input_list with calibration data is required)
qairt-quantizer \
    --input_dlc model.dlc \
    --output_dlc model_q8.dlc \
    --input_list calib.txt \
    --act_bitwidth 8 --weights_bitwidth 8 --bias_bitwidth 8

# 3. Context binary
qnn-context-binary-generator \
    --model <SDK_ROOT>/lib/libQnnModelDlc.so \
    --backend <SDK_ROOT>/lib/libQnnHtp.so \
    --dlc_path model_q8.dlc \
    --binary_file model \
    --config_file config_file.json \
    --output_dir .
```

Notes:
- `--source_model_input_shape` takes the name and comma-separated
  dimensions as two arguments. There is no `--input_dim` flag.
- Quantization without `--input_list` reports success but writes a float DLC.
- Calibration list lines contain absolute paths; multiple tensor files per
  line are separated by spaces.
- `--use_per_channel_quantization` fails on Conv nodes without bias
  (`preprocessPerChannel: No bias info`).
- `--float_bitwidth 32` avoids FP16 graph rejection but leaves unquantized
  tensors in the graph.

## 6. Inference

```bash
qnn-net-run \
    --retrieve_context model.bin \
    --backend <SDK_ROOT>/lib/libQnnHtp.so \
    --input_list inputs.txt \
    --output_dir out
```

Success criterion: `Finished Executing Graphs`.
