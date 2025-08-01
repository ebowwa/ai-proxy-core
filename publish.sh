#!/bin/bash
# Replace YOUR-PYPI-TOKEN with your actual token

cd /Users/ebowwa/apps/starstride-001/ai-proxy-core-package

# Method 1: Using environment variables (paste your token here)
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR-TOKEN-HERE

# Upload to PyPI
python -m twine upload dist/*

# After successful upload:
echo ""
echo "✅ Package published! Now available at: https://pypi.org/project/ai-proxy-core/"
echo ""
echo "To install: pip install ai-proxy-core"
echo ""
echo "Update Starstride's requirements.txt to use:"
echo "ai-proxy-core>=0.1.1"