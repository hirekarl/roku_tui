# Troubleshooting: Connectivity & Discovery

If **roku-tui** cannot find your Roku, or if you're experiencing "Timed Out" errors, follow this guide to resolve common network issues.

## 🔍 Why can't I find my Roku?

The app uses **SSDP (Simple Service Discovery Protocol)** to find Roku devices on your network. This can fail for several reasons:

1.  **Network Isolation**: Your computer and the Roku must be on the same subnet (e.g., both on `192.168.1.x`).
2.  **Mesh Wi-Fi**: Some mesh routers (like Eero or Orbi) isolate wireless devices into different segments, preventing SSDP traffic from crossing over.
3.  **Firewalls**: Ensure your computer allows outbound UDP traffic on port `1900` (the standard SSDP port).
4.  **VPNs**: If you are connected to a VPN, your computer might be looking for devices inside the VPN tunnel instead of your local network.

---

## 🛠️ The Manual Fix: Connection by IP

If auto-discovery fails, the most reliable solution is to connect directly via the Roku's IP address.

### 1. Find your Roku's IP
On your Roku remote (the physical one!):
- Go to **Settings → Network → About**.
- Look for **IP Address** (e.g., `192.168.1.42`).

### 2. Connect manually
Run the app with the `--ip` flag:
```bash
uv run roku-tui --ip 192.168.1.42
```
*Note: This IP is saved in your local history, and future sessions will attempt to reconnect to it automatically.*

---

## ⚙️ Roku System Settings

Ensure your Roku is configured to allow external control:

- Go to **Settings → System → Advanced system settings → External Control**.
- **Network access**: Set this to **Default** or **Permissive**. 
- If it is set to "Disabled," **roku-tui** will not be able to send any commands.

---

## 💤 "Device Not Responding" (Power Issues)

Roku devices have different "power states." If your Roku is a "stick" powered by a USB port on your TV, it may lose power completely when the TV is off. 

- **Result**: You cannot turn the TV *on* using **roku-tui** because the Roku itself is powered down.
- **Solution**: Plug the Roku into a wall outlet using a standard USB power brick so it remains "always on" and listening for commands.
