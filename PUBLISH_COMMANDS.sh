#!/bin/bash
# Commands to publish ai-proxy-core to PyPI

echo "=== Publishing ai-proxy-core to PyPI ==="
echo ""
echo "1. First, make sure you have PyPI accounts:"
echo "   - Production: https://pypi.org/account/register/"
echo "   - Test: https://test.pypi.org/account/register/"
echo ""
echo "2. Create API tokens:"
echo "   - Go to Account Settings → API tokens"
echo "   - Create a token (save it securely!)"
echo ""
echo "3. Configure authentication (choose one method):"
echo ""
echo "   Method A: Using .pypirc file"
echo "   Create ~/.pypirc with:"
cat << 'EOF'

[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE

[testpypi]
username = __token__
password = pypi-YOUR-TEST-TOKEN-HERE
EOF

echo ""
echo "   Method B: Using environment variables"
echo "   export TWINE_USERNAME=__token__"
echo "   export TWINE_PASSWORD=pypi-YOUR-TOKEN-HERE"
echo ""
echo "4. Upload to TestPyPI first (recommended):"
echo "   python -m twine upload --repository testpypi dist/*"
echo ""
echo "5. Test installation from TestPyPI:"
echo "   pip install -i https://test.pypi.org/simple/ ai-proxy-core==0.1.1"
echo ""
echo "6. If everything works, upload to PyPI:"
echo "   python -m twine upload dist/*"
echo ""
echo "7. Now anyone can install with:"
echo "   pip install ai-proxy-core"
echo ""
echo "=== Your package is ready in: dist/ ==="
ls -la dist/