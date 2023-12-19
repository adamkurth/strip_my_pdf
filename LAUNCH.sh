#!/bin/bash

SCRIPT_TO_RUN="gui.py"

# Check if the script exists and execute it
if [[ -f "$SCRIPT_TO_RUN" ]]; then
    echo "Running $SCRIPT_TO_RUN..."
    python "$SCRIPT_TO_RUN"
else
    echo "Error: $SCRIPT_TO_RUN not found in $(pwd)"
fi
