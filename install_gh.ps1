# Install gh CLI on Windows (PowerShell as Administrator)
# Run: Right-click -> Run as Administrator
winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements

# Verify
gh --version
