#!/bin/bash
# Release script - bump version, build, publish to PyPI, and push to git

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep -o 'version = "[^"]*"' pyproject.toml | cut -d'"' -f2)

# Check if version argument provided
if [ $# -eq 0 ]; then
    echo "Current version: $CURRENT_VERSION"
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh 0.1.8"
    exit 1
fi

VERSION=$1

# Validate version format
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format X.Y.Z (e.g., 0.1.8)"
    exit 1
fi

echo "🚀 Releasing version $VERSION (from $CURRENT_VERSION)"

# Get release description
echo "📝 Enter a brief description for this release:"
read -r DESCRIPTION

# Update CHANGELOG.md
echo "📋 Updating CHANGELOG..."
DATE=$(date +%Y-%m-%d)
CHANGELOG_ENTRY="## [$VERSION] - $DATE\n- $DESCRIPTION\n"

# Insert new entry after the # Changelog header
sed -i '' "/^# Changelog/a\\
\\
$CHANGELOG_ENTRY" CHANGELOG.md

# Update version in all files
echo "📝 Updating version numbers..."
sed -i '' "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml
sed -i '' "s/version=\".*\"/version=\"$VERSION\"/" setup.py
sed -i '' "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" ai_proxy_core/__init__.py

# Clean build artifacts
echo "🧹 Cleaning old builds..."
rm -rf dist/ build/ *.egg-info/

# Build package
echo "📦 Building package..."
python setup.py sdist bdist_wheel

# Upload to PyPI
echo "⬆️  Uploading to PyPI..."
twine upload dist/*

# Git commit and tag
echo "📝 Committing changes..."
git add pyproject.toml setup.py ai_proxy_core/__init__.py CHANGELOG.md
git commit -m "chore: bump version to $VERSION

- $DESCRIPTION"

# Create and push tag
echo "🏷️  Creating git tag..."
git tag -a "v$VERSION" -m "Release version $VERSION"

# Push to git
echo "🚀 Pushing to GitHub..."
git push origin main
git push origin "v$VERSION"

echo "✅ Release $VERSION complete!"