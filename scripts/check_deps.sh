#!/bin/bash
# scripts/check_deps.sh
echo " Scanning dependencies for known vulnerabilities..."
uv run pip-audit --desc --strict

if [ $? -ne 0 ]; then
    echo "❌ Vulnerabilities found! Please update your dependencies."
    exit 1
else
    echo "✅ No known vulnerabilities found."
fi