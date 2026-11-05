# Glossary

**ID:** SC8280XP-QAIRT-GL | **Rev:** 1.0

| Term | Definition |
| --- | --- |
| QAIRT | Qualcomm AI Runtime. SDK containing the converter, quantizer, backends, and runtime tools. |
| QNN | Qualcomm Neural Network API layer used by the HTP backend. |
| HTP | Hexagon Tensor Processor. The DSP executing quantized graphs. |
| v68 / v73 | HTP architecture generations. The target platform is v68. |
| DLC | Deep Learning Container. QAIRT's intermediate model representation. |
| Context binary | Precompiled graph artifact loaded by `qnn-net-run` via `--retrieve_context`. |
| socModel | Integer in the context binary metadata identifying the target SoC. See COMPATIBILITY-MATRIX §3. |
| soc_id | Integer in the backend extension configuration (`config_backend.json`). Radxa documents 35 for QCS6490, 37 for SC8280XP. |
| blobVer | `contextBlobVersion` in artifact metadata. Not the deciding compatibility factor. |
| backendApiVersion | QNN backend API version recorded in artifact metadata. |
| EP | Execution Provider (ONNX Runtime). |
| ASR | Automatic Speech Recognition. |
| AED | Attention-based Encoder-Decoder. |
| CTC | Connectionist Temporal Classification. Non-autoregressive decoding head. |
| blank | CTC blank class (id 0). |
| Conformer | Convolution-augmented Transformer encoder architecture. |
| Autoregressive decoding | Sequential token generation where each step consumes the previous output and updated state. |
| KV cache | Per-layer attention state carried across autoregressive decode steps. |
| PTQ | Post-Training Quantization. |
| QAT | Quantization-Aware Training. |
| CLE | Cross Layer Equalization. A quantization algorithm. |
| percentile calibration | Activation range calibration that clips extreme values at a chosen percentile. |
| CMVN | Cepstral Mean and Variance Normalization. Applied to fbank features. |
| fbank | Log-mel filterbank features. 80 dimensions at 25 ms window / 10 ms shift in this project. |
| Genie | QAIRT LLM runtime used with Radxa prebuilt model bundles. |
| `ADSP_LIBRARY_PATH` | Path to the directory containing `libQnnHtpV68Skel.so`. Required for device creation. |
| `PRODUCT_SOC` / `DSP_ARCH` | Environment variables used by some tooling (`8280` / `68`). |
| PASS / FAIL / N/A / NT | Status values defined in README. |
