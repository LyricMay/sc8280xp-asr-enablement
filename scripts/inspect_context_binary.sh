#!/usr/bin/env bash
# Extract metadata from a QNN context binary.
#
# Usage:
#   SDK_ROOT=/path/to/qairt ./inspect_context_binary.sh model.bin [output.json]
#
# Prints socModel, buildId, contextBlobVersion and the graph I/O list.

set -euo pipefail

SDK_ROOT="${SDK_ROOT:?SDK_ROOT must be set to the QAIRT SDK root}"
BINARY="${1:?usage: inspect_context_binary.sh <context.bin> [output.json]}"
OUTPUT="${2:-/tmp/context_meta.json}"

export LD_LIBRARY_PATH="${SDK_ROOT}/lib:${LD_LIBRARY_PATH:-}"

UTILITY="${SDK_ROOT}/bin/qnn-context-binary-utility"
if [[ ! -x "${UTILITY}" ]]; then
    echo "qnn-context-binary-utility not found under ${SDK_ROOT}/bin" >&2
    exit 1
fi

"${UTILITY}" --context_binary="${BINARY}" --json_file="${OUTPUT}" >/dev/null

python3 - "${OUTPUT}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)["info"]

print("buildId            :", data.get("buildId"))
print("socModel           :", data.get("socModel"))
print("contextBlobVersion :", data.get("contextBlobVersion"))
print("backendApiVersion  :", data.get("backendApiVersion"))
print("coreApiVersion     :", data.get("coreApiVersion"))
print("numGraphs          :", data.get("numGraphs"))

for graph in data.get("graphs", []):
    info = graph["info"]
    print("graph              :", info.get("graphName"))
    for index, tensor in enumerate(info.get("graphInputs", [])):
        detail = tensor["info"]
        print(f"  input[{index}] dimensions: {detail.get('dimensions')}")
    for index, tensor in enumerate(info.get("graphOutputs", [])):
        detail = tensor["info"]
        print(f"  output[{index}] dimensions: {detail.get('dimensions')}")
PY
