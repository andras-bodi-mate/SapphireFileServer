cd ../

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Uv is not installed. Installing..."
    powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
    Write-Host "Installation complete. Please restart this script to continue."
    exit 1
}

uv run python src/main.py