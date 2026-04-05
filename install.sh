
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

install_homebrew() {
  if command -v brew >/dev/null 2>&1; then
    return
  fi

  echo "Homebrew is not installed. Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

install_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "Python already installed: $(python3 --version)"
    return
  fi

  echo "Python 3 not found. Installing latest Python via Homebrew..."
  brew install python
  echo "Installed Python: $(python3 --version)"
}

install_project() {
  require_command python3

  python3 -m venv .venv
  source .venv/bin/activate

  python -m pip install --upgrade pip setuptools wheel
  pip install --upgrade playwright
  python -m playwright install

  mkdir -p output
}

print_done() {
  echo ""
  echo "Installation complete."
  echo ""
  echo "Activate the environment:"
  echo "source .venv/bin/activate"
  echo ""
  echo "Run all enabled targets:"
  echo "python scrap_feedback.py"
  echo ""
  echo "Run a specific target:"
  echo "python scrap_feedback.py reports"
}

install_homebrew
install_python
install_project
print_done