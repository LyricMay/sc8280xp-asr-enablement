# SC8280XP ASR Model Enablement and Compatibility

**Document ID:** SC8280XP-QAIRT-EN | **Revision:** 1.0 | **Status:** Released

Model enablement and compatibility record for deploying ASR models on the
Qualcomm AI Runtime (QAIRT) / QNN stack on the SC8280XP platform
(Radxa Dragon Q8B, Hexagon HTP v68).

Two parallel scopes:

1. **Platform compatibility** — SDK versions, SoC targets, runtime backends,
   and precision support.
2. **ASR model enablement** — porting, quantization, and execution of ASR
   model families on the HTP v68 target, with measured limits per family.

| Document | Contents |
| --- | --- |
| Compatibility Matrix | SDK versions, socModel IDs, runtime backends, precision support, ASR model family status |
| Errata | Known limitations with signatures and ruled-out workarounds |
| Test Procedure | Verification method, TC-* case IDs, pass/fail criteria |
| ASR Workload | Graph specification and execution of the evaluated ASR workload |
| Environment Guide | Runtime variables, dependencies, conversion sequence |
| Glossary | Terms and identifiers |

Status legend: PASS, FAIL, N/A, NT. Definitions are in the repository
README.

This site contains documentation only. No Qualcomm QAIRT/QNN SDK binaries,
archives, model weights, recordings, or derived personal text are
distributed here.
