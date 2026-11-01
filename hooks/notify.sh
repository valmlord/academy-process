#!/bin/bash
# End-of-task notification hook. Called by the `notify` pipeline phase (and the watchdog).
# Reads the message body on stdin; $1 is the tier.
#
# DEFAULT: a no-op that just echoes to the terminal, so the pipeline's notify gate passes
# without any external infrastructure. Wire it to whatever you use.
#
# Exit 0 = notified (the notify gate records success). Non-zero = failure (non-fatal; the
# pipeline logs a warning but does not abort).

TIER="${1:-?}"
BODY="$(cat)"

echo "== NOTIFY [$TIER] =="
echo "$BODY"

# --- Optional: wire your own notifier here ----------------------------------
# Read the destination from an environment variable you set yourself - keep any
# URL, token, or address in your own environment, never in this file. Return a
# non-zero exit on failure so the pipeline logs a warning (it does not abort).
# Shape:
#   printf '%s' "$BODY" | <your-notify-command> || exit 1
# ----------------------------------------------------------------------------

exit 0
