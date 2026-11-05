# SC8280XP ASR Model Enablement and Compatibility

**Document ID:** SC8280XP-QAIRT-EN
**Revision:** 1.0
**Status:** Released
**Scope:** Radxa Dragon Q8B (Qualcomm SC8280XP, Hexagon HTP v68)

Model enablement and compatibility record for deploying ASR models on the
Qualcomm AI Runtime (QAIRT) / QNN stack on the SC8280XP platform.

Two parallel scopes:

1. **Platform compatibility** — SDK versions, SoC targets, runtime backends,
   and precision support, published as a compatibility matrix and errata.
2. **ASR model enablement** — porting, quantization, and execution of
   autoregressive and non-autoregressive ASR model families on the HTP v68
   target, with measured limits recorded per model family.

Deliverables: compatibility matrix, errata, verification procedure, ASR
workload specifications, configuration templates, and scripts.

## Document set

| ID | Title | Description |
| --- | --- | --- |
| SC8280XP-QAIRT-CM | [Compatibility Matrix](docs/COMPATIBILITY-MATRIX.md) | SDK versions, runtime backends, SoC targets, model artifact compatibility |
| SC8280XP-QAIRT-ER | [Errata](docs/ERRATA.md) | Known limitations and ruled-out workarounds |
| SC8280XP-QAIRT-TP | [Test Procedure](docs/TEST-PROCEDURE.md) | Verification method, test case IDs, pass/fail criteria |
| SC8280XP-QAIRT-GL | [Glossary](docs/GLOSSARY.md) | Terms and identifiers |
| SC8280XP-QAIRT-EG | [Environment Guide](docs/ENVIRONMENT.md) | Runtime environment and dependencies |
| SC8280XP-QAIRT-AW | [ASR Workload Specification](docs/ASR-WORKLOAD.md) | Graph specification and execution of evaluated ASR workloads |

## Status legend

| Status | Definition |
| --- | --- |
| PASS | Verified on target hardware with the recorded output |
| FAIL | Reproducible failure; error signature recorded |
| N/A | Component absent from the evaluated package |
| NT | Not tested |

## Revision history

| Rev | Date | Change |
| --- | --- | --- |
| 1.0 | 2026-11-05 | Initial release |

## Deployment

Documentation is published to GitHub Pages from the `docs/` tree via the
workflow in `.github/workflows/pages.yml`. The build uses MkDocs with the
configuration in `mkdocs.yml`.

Site URL: https://lyricmay.github.io/sc8280xp-asr-enablement/

## Compliance

This repository contains documentation, configuration templates, and
originally authored scripts only. It does not distribute Qualcomm QAIRT/QNN
SDK binaries, archives, or model weights. Those components are governed by
the applicable upstream license and must be obtained from the vendor.

Model artifacts and dataset references appear as identifiers only. No raw
recordings and no derived text containing personal data are included.

## License

Original content: MIT. See `LICENSE`.
