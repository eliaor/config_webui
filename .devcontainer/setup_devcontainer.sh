#!/bin/bash

# curl -fsSL https://antigravity.google/cli/install.sh | bash
sudo uv pip install --system --break-system-packages -r requirements.txt

# agy --mode=accept-edits --dangerously-skip-permissions
