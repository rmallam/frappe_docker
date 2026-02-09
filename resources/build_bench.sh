#!/bin/bash
set -ex

# This script initializes the Frappe Bench and installs apps.
# It is designed to run inside the Docker builder container.

BENCH_DIR="/home/frappe/frappe-bench"

# 1. Setup Git
git config --global user.email "frappe@example.com"
git config --global user.name "frappe"
git config --global --add safe.directory '*'

# 2. Ensure clean start
echo "Cleaning target directory: $BENCH_DIR"
rm -rf "$BENCH_DIR"

# 3. Initialize Bench
echo "Starting bench init..."
bench init \
    --frappe-branch="${FRAPPE_BRANCH:-version-15}" \
    --frappe-path="${FRAPPE_PATH:-https://github.com/frappe/frappe}" \
    --no-procfile \
    --no-backups \
    --skip-redis-config-generation \
    --verbose \
    "$BENCH_DIR"

# 4. Enter bench directory
cd "$BENCH_DIR"

# 5. Fetch Apps
echo "Starting app discovery..."
export GITHUB_TOKEN="${GH_BUILD_KEY}"
APPS_LIST=$(get_apps --org "${GITHUB_ORG}" --apps "${APPS} ${ERPNEXT_REPO}")

if [ -n "$APPS_LIST" ]; then
    echo "Identified unique apps to install: $APPS_LIST"
    for app in $APPS_LIST; do
        echo "Installing app: $app"
        # Always use --resolve-deps to ensure dependencies are pulled
        bench get-app --resolve-deps "$app"
    done
else
    echo "No custom apps to install."
fi

# 6. Build Assets
echo "Finalizing site config and building assets..."
echo "{}" > sites/common_site_config.json
bench build

# 7. Final Cleanup
echo "Cleaning up build artifacts..."
rm -rf apps/*/.git
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

echo "Build script completed successfully!"
