#!/bin/bash
echo "Creating ~/.pypirc file for PyPI authentication"
echo ""
echo "Paste this into ~/.pypirc and replace YOUR-TOKEN with your actual token:"
echo ""
cat << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TOKEN-HERE
EOF

echo ""
echo "Then run: python -m twine upload dist/*"