#!/bin/bash
# ==============================================
# Medicube Monitor - Setup Script
# ==============================================
# This script sets up the monitor to run automatically
# every 24 hours on your Linux server.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
# ==============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(which python3)"
VENV_DIR="${SCRIPT_DIR}/venv"

echo "=============================================="
echo "  Medicube Product Monitor - Auto Setup"
echo "=============================================="
echo ""

# Step 1: Create virtual environment
echo "[1/5] Creating Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    echo "  Created venv at: $VENV_DIR"
else
    echo "  venv already exists"
fi

# Step 2: Install dependencies
echo "[2/5] Installing dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
echo "  Dependencies installed"

# Step 3: Create data directory
echo "[3/5] Creating data directory..."
mkdir -p "$SCRIPT_DIR/data"
echo "  Data directory ready"

# Step 4: Setup cron job (every 24 hours at 9:00 AM KST = 0:00 UTC)
echo "[4/5] Setting up cron job..."

CRON_CMD="0 0 * * * cd $SCRIPT_DIR && $VENV_DIR/bin/python monitor.py --check >> $SCRIPT_DIR/data/cron.log 2>&1"
CRON_MARKER="# medicube-monitor"

# Remove old cron entry if exists
crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | crontab - 2>/dev/null || true

# Add new cron entry
(crontab -l 2>/dev/null; echo "$CRON_CMD $CRON_MARKER") | crontab -
echo "  Cron job installed (runs daily at 00:00 UTC / 09:00 KST)"

# Step 5: Setup systemd service (optional, for daemon mode)
echo "[5/5] Creating systemd service (optional)..."

SERVICE_FILE="/etc/systemd/system/medicube-monitor.service"

if [ "$(id -u)" = "0" ] || command -v sudo &>/dev/null; then
    SUDO_CMD=""
    if [ "$(id -u)" != "0" ]; then
        SUDO_CMD="sudo"
    fi

    $SUDO_CMD tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Medicube Product Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$SCRIPT_DIR
ExecStart=$VENV_DIR/bin/python monitor.py --daemon --interval 24
Restart=always
RestartSec=300
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    $SUDO_CMD systemctl daemon-reload
    echo "  Systemd service created: medicube-monitor.service"
    echo ""
    echo "  To use systemd daemon (alternative to cron):"
    echo "    sudo systemctl enable medicube-monitor"
    echo "    sudo systemctl start medicube-monitor"
    echo "    sudo systemctl status medicube-monitor"
else
    echo "  Skipped (no root/sudo access). Using cron instead."
fi

echo ""
echo "=============================================="
echo "  Setup complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Send /start to @KoreanEonni_bot in Telegram"
echo "  2. Run: $VENV_DIR/bin/python monitor.py --setup"
echo "  3. The monitor will check every 24h automatically via cron"
echo ""
echo "Manual commands:"
echo "  Check now:    $VENV_DIR/bin/python monitor.py --check"
echo "  View logs:    tail -f $SCRIPT_DIR/data/monitor.log"
echo "  Cron log:     tail -f $SCRIPT_DIR/data/cron.log"
echo ""
