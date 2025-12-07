#!/usr/bin/env bash

main() {
	cd "$(dirname "$0")"
	cd ../

	# Check if uv is installed
	if ! command -v uv >/dev/null 2>&1; then
	    echo "Uv is not installed. Installing (system-wide)..."
	    # Run the install script
	    curl -sSL https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin bash
	    echo "Installation complete. Please restart this script to continue."
	    exit 1
	fi

	# Run your Python program using uv
	uv run python3 src/main.py
}

mkdir -p /var/log/sapphire/
main > >(tee -a /var/log/sapphire/out.log) 2> >(tee -a /var/log/sapphire/err.log | tee -a /var/log/sapphire/out.log >&2)