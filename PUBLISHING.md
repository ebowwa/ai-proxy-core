# Publishing ai-proxy-core to PyPI

## First Time Setup

1. Create accounts:
   - [PyPI](https://pypi.org/account/register/)
   - [TestPyPI](https://test.pypi.org/account/register/) (for testing)

2. Install publishing tools:
   ```bash
   pip install build twine
   ```

3. Create API tokens:
   - Go to [PyPI Account Settings](https://pypi.org/manage/account/)
   - Create an API token
   - Save it securely

## Publishing Process

### 1. Update Version

Edit `pyproject.toml` and bump the version:
```toml
version = "0.1.2"  # Increment this
```

### 2. Build Package

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build package
python -m build
```

### 3. Test on TestPyPI (Optional)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install -i https://test.pypi.org/simple/ ai-proxy-core
```

### 4. Publish to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*

# Now anyone can install with:
# pip install ai-proxy-core
```

## Using Token Authentication

Create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE

[testpypi]
username = __token__
password = pypi-YOUR-TEST-TOKEN-HERE
```

## Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:
```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        python -m twine upload dist/*
```

## After Publishing

Update Starstride's requirements.txt:
```
# Instead of:
ai-proxy-core @ git+https://github.com/ebowwa/ai-proxy-core.git

# Use:
ai-proxy-core>=0.1.1
```

Benefits:
- Easy updates: `pip install --upgrade ai-proxy-core`
- Version pinning: `ai-proxy-core==0.1.1`
- No git cloning needed
- Faster installation
- PyPI handles caching