#!/bin/bash
cd /home/kavia/workspace/code-generation/code-quality-analyzer-45203-45212/bug_detector_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

