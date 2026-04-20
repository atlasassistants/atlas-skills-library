#!/bin/bash
# Fathom API helper for meeting-ops
# Usage: fathom-api.sh meetings [limit] | transcript <recording_id> | summary <recording_id> | new-since [limit]

SECRETS_DIR="${ATLAS_SECRETS_DIR:-$HOME/.atlas/secrets}"
API_KEY=$(cat "$SECRETS_DIR/fathom-api-key")
BASE_URL="https://api.fathom.ai/external/v1"

case "$1" in
  meetings)
    # List recent meetings (default 20)
    LIMIT="${2:-20}"
    curl -s "$BASE_URL/meetings?limit=$LIMIT" \
      -H "X-Api-Key: $API_KEY"
    ;;

  transcript)
    # Get transcript for a recording_id
    RECORDING_ID="$2"
    if [ -z "$RECORDING_ID" ]; then
      echo "Usage: fathom-api.sh transcript <recording_id>" >&2
      exit 1
    fi
    curl -s "$BASE_URL/recordings/$RECORDING_ID/transcript" \
      -H "X-Api-Key: $API_KEY"
    ;;

  summary)
    # Get Fathom's auto-generated summary for a recording_id
    RECORDING_ID="$2"
    if [ -z "$RECORDING_ID" ]; then
      echo "Usage: fathom-api.sh summary <recording_id>" >&2
      exit 1
    fi
    curl -s "$BASE_URL/recordings/$RECORDING_ID/summary" \
      -H "X-Api-Key: $API_KEY"
    ;;

  new-since)
    # Return meetings not yet debriefed.
    # Compares recording_ids against brain/meetings/debriefs/ filenames
    # (debrief files contain fathom_id in frontmatter).
    DEBRIEFS_DIR="${WORKSPACE:-$HOME}/brain/meetings/debriefs"
    LIMIT="${2:-20}"

    MEETINGS=$(curl -s "$BASE_URL/meetings?limit=$LIMIT" \
      -H "X-Api-Key: $API_KEY")

    echo "$MEETINGS" | python3 -c "
import sys, json, os, re

data = json.load(sys.stdin)
items = data.get('items', [])

debriefs_dir = '$DEBRIEFS_DIR'
processed = set()
if os.path.isdir(debriefs_dir):
    for f in os.listdir(debriefs_dir):
        if f.endswith('.md'):
            try:
                with open(os.path.join(debriefs_dir, f)) as fh:
                    content = fh.read(500)
                    match = re.search(r'fathom_id:\s*(\d+)', content)
                    if match:
                        processed.add(match.group(1))
            except:
                pass

new = [m for m in items if str(m['recording_id']) not in processed]
print(json.dumps({'items': new, 'total_new': len(new)}))
"
    ;;

  *)
    echo "Usage: fathom-api.sh meetings [limit] | transcript <recording_id> | summary <recording_id> | new-since [limit]"
    exit 1
    ;;
esac
