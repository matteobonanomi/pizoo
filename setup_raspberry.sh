#!/bin/bash

# ----- CONFIGURAZIONI PERSONALIZZABILI -----
NEW_HOSTNAME="raspberry_matteo"
WIFI_SSID="NOME_WIFI"
WIFI_PSK="PASSWORD_WIFI"
PROJECT_DIR="/home/pi/progetto"
VENV_NAME="venv"
# -------------------------------------------

echo "📡 Configurazione Wi-Fi..."
sudo tee /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null <<EOF
country=IT
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="$WIFI_SSID"
    psk="$WIFI_PSK"
    scan_ssid=1
}
EOF
sudo chmod 600 /etc/wpa_supplicant/wpa_supplicant.conf
sudo rfkill unblock wifi
sudo wpa_cli -i wlan0 reconfigure
echo "✅ Wi-Fi configurato"

echo "🔧 Cambio hostname in $NEW_HOSTNAME..."
echo "$NEW_HOSTNAME" | sudo tee /etc/hostname
sudo sed -i "s/127.0.1.1.*/127.0.1.1\t$NEW_HOSTNAME/" /etc/hosts
sudo hostnamectl set-hostname "$NEW_HOSTNAME"

echo "🛡️ Abilitazione SSH..."
sudo systemctl enable ssh
sudo systemctl start ssh

echo "⬆️ Aggiornamento pacchetti..."
sudo apt update && sudo apt upgrade -y

echo "🌐 Installazione avahi-daemon per mDNS..."
sudo apt install -y avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

echo "🐍 Setup ambiente virtuale Python..."
sudo apt install -y python3-venv
mkdir -p "$PROJECT_DIR"
python3 -m venv "$PROJECT_DIR/$VENV_NAME"

echo "🧹 Pulizia: rimozione script..."
sudo rm -- "$0"

echo "✅ Setup completato! Riavvio in corso..."
sudo reboot
