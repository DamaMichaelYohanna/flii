#!/bin/bash
set -e

echo "==> Installing Python dependencies..."
python3 -m pip install -r requirements.txt

echo "==> Collecting static assets into staticfiles_build/static..."
python3 manage.py collectstatic --noinput --clear

echo "==> Ensuring Vercel static asset routing compatibility..."
mkdir -p staticfiles_build/static/images
mkdir -p staticfiles_build/images

# Mirror static images into root and static subfolders of staticfiles_build
if [ -d "static/images" ]; then
    cp -r static/images/* staticfiles_build/static/images/ 2>/dev/null || true
    cp -r static/images/* staticfiles_build/images/ 2>/dev/null || true
fi

# Ensure all staticfiles are available in both structures
if [ -d "staticfiles" ]; then
    cp -r staticfiles/* staticfiles_build/static/ 2>/dev/null || true
    cp -r staticfiles/* staticfiles_build/ 2>/dev/null || true
fi

echo "==> Verified static assets output in staticfiles_build:"
ls -la staticfiles_build/static/images/ || true

echo "==> Build finished successfully!"
