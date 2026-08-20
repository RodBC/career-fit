#!/usr/bin/env bash
# Legacy Chrome-for-Testing fetch — RETIRED.
# Camoufox replaced Selenium. Use:
#   pip install -e ".[linkedin]"
#   python -m camoufox fetch
set -euo pipefail
echo "scripts/fetch_chrome.sh is retired." >&2
echo "Use: pip install -e '.[linkedin]' && python -m camoufox fetch" >&2
exit 1
