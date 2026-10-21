#!/bin/sh
# Run Vietfox from this checkout.
cd "$(dirname "$0")" || exit 1
exec python3 -m vietfox "$@"
