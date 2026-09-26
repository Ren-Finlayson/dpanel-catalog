#!/usr/bin/env sh
# Build the catalogue into dist/ and sign each index with minisign.
# Plain shell on purpose: runs the same on GitHub Actions, Forgejo/Gitea Actions or a laptop.
#
# Requires: python3 with PyYAML, minisign, git.
# Env:
#   CATALOG_BASE_URL     public URL dPanel will use as base.app_repo_url (required)
#   MINISIGN_SECRET_KEY  contents of the minisign secret key file (required). Generate the CI key
#                        with `minisign -G -W` (no password): the CI secret store is its protection.
#   CATALOG_MODES        dPanel base.mode values to publish for (default: "stable dev")
set -eu

: "${CATALOG_BASE_URL:?set CATALOG_BASE_URL}"
: "${MINISIGN_SECRET_KEY:?set MINISIGN_SECRET_KEY}"
cd "$(dirname "$0")/.."

# The catalogue timestamp must only go up (dPanel rejects older indexes), so use the commit time.
SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(git log -1 --format=%ct)}"
export SOURCE_DATE_EPOCH

keyfile="$(mktemp)"
trap 'rm -f "$keyfile"' EXIT
printf '%s\n' "$MINISIGN_SECRET_KEY" > "$keyfile"

rm -rf dist
for mode in ${CATALOG_MODES:-stable dev}; do
    python3 tools/build.py --base-url "$CATALOG_BASE_URL" --mode "$mode"
    minisign -S -s "$keyfile" -m "dist/$mode/1panel.json.zip" -t "dPanel catalog $mode $SOURCE_DATE_EPOCH"
done
echo "signed catalogue ready in dist/"
