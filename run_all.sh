#!/bin/bash
# Runs the seven steps, then the checks. A few seconds on a laptop. No key, no account, no network.
set -e
cd "$(dirname "$0")"
for step in step1_folder step2_split step3_numbers step4_store step5_agent step6_trust step7_bill; do
  echo
  echo "=== $step.py"
  python3 $step.py
done
echo
python3 tests.py
