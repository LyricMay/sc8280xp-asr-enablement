#!/usr/bin/env bash
# Report CDSP/ADSP state before running QNN workloads.
#
# Usage: ./check_dsp.sh
# Exit status: 0 if CDSP is running, 1 otherwise.

set -uo pipefail

for proc in /sys/class/remoteproc/remoteproc*; do
    [[ -d "${proc}" ]] || continue
    name="$(cat "${proc}/name" 2>/dev/null || echo unknown)"
    state="$(cat "${proc}/state" 2>/dev/null || echo unknown)"
    printf '%-8s %s\n' "${name}" "${state}"
done

cdsp="$(cat /sys/class/remoteproc/remoteproc1/state 2>/dev/null || echo unknown)"
if [[ "${cdsp}" != "running" ]]; then
    echo "CDSP is not running; reboot before running QNN workloads." >&2
    exit 1
fi

echo "CDSP ready."
