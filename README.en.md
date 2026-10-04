# Device Info Inspector

A Windows desktop tool that **locally collects and displays** device, system, network, and browser information.  
It supports both a **Web UI (pywebview)** and a **tkinter fallback UI**, with **automatic downgrade** for maximum compatibility.

English | [简体中文](README.md)

> All data is collected and displayed locally, **nothing is uploaded to any server**. Some information relies on third-party public APIs (IP geolocation, etc.).

---

## Screenshots

![Main UI](screenshots/main.png)

---

## Features

- **System Info**: OS, hostname, CPU model and core count, RAM, disk partitions, battery status
- **Network Info**: Public IPv4/IPv6, local IPv4/IPv6, MAC address, gateway, DNS servers
- **IP Geolocation**: Country / region / city, latitude & longitude, timezone, ISP, organization, AS
- **Browser Fingerprint**: Canvas, WebGL vendor/renderer, audio fingerprint, font count, User-Agent
- **Browser Environment**: Language, platform, screen resolution, pixel ratio, CPU cores, device memory, touch support, Cookie, DNT
- **Dual Backend**: Uses Web UI when WebView2 is available, otherwise falls back to tkinter
- **One-Click Copy**: Each data item has a copy button at the top-right (shown on hover)
- **Multi-API Fallback**: Public IP and geolocation are queried through multiple APIs to improve reliability

---

## Quick Start

### Option 1: Download exe (Recommended)

Download the latest `SysInfo.exe` from [Releases](https://github.com/clocktool/SysInfo/releases), then **double-click to run**.

> System requirement: Windows 10 / 11 (64-bit)

### Option 2: Run from Source

```bash
git clone https://github.com/clocktool/SysInfo.git
cd SysInfo
pip install -r requirements.txt
python launcher.py
```

---

## Dependencies

- **Python** >= 3.10 (3.11 / 3.12 / 3.14 recommended)
- [pywebview](https://pywebview.flowrl.com/) == 4.4.1 — Web UI
- [psutil](https://github.com/giampaolo/psutil) — System information collection
- [requests](https://requests.readthedocs.io/) — IP query APIs

Install:

```bash
pip install -r requirements.txt
```

---

## Project Structure

```text
SysInfo/
├── launcher.py           # Launcher: choose backend
├── backend_web.py        # Web backend (pywebview + local HTTP server)
├── backend_lite.py       # tkinter fallback backend
├── collectors.py         # Data collection module
├── web/                  # Frontend assets
│   ├── index.html
│   ├── style.css
│   └── app.js
├── app.ico               # Application icon
├── requirements.txt
├── LICENSE
├── README.md
└── README.en.md
```

---

## Build to exe

```bash
pyinstaller --onefile --windowed --name SysInfo ^
  --icon "app.ico" ^
  --add-data "web;web" ^
  --hidden-import=webview ^
  --hidden-import=webview.platforms.edgechromium ^
  launcher.py
```

After building, the exe is at `dist/SysInfo.exe`.

> Tip: If the icon does not update, rename the exe or move it to another folder (Windows icon cache issue).

---

## Usage

1. Double-click `SysInfo.exe`. The program auto-collects and displays information.
2. Each data item has a **copy button** at the top-right (shown on hover).
3. Click **"Refresh"** at the top-right to re-collect.

---

## FAQ

### Q1: Public IP shows "None"?

Possible reasons: blocked by network, or API rate-limited. The program **automatically tries multiple APIs**, but failures can still happen.

- Check your network
- Retry later
- Or add more APIs in `collectors.py`

### Q2: Opens to 404?

The `web/` folder was not packaged correctly. Rebuild with `--add-data "web;web"`.

### Q3: Why are some local IPs missing?

Some IPs (`127.0.0.1`, `169.254.x.x`, `fe80::`, etc.) are **loopback / APIPA / link-local addresses** and **do not represent real network addresses**. They are automatically filtered.

### Q4: What is WebView2? Do I need to install it?

**WebView2 Runtime** is Microsoft's browser engine component used to render the Web UI.

- **Windows 11**: Bundled with the system
- **Windows 10**: Most installations have it via Windows Update

If not installed, the program **automatically falls back to the tkinter UI**, with no functional loss.

---

## Development

To add a new data field:

1. **Collector**: Modify `collect_all()` in `collectors.py`, add a key to the returned dict
2. **Web UI**: Modify `render()` in `web/app.js`, add a corresponding `item(...)`
3. **tkinter UI**: Modify `_render()` in `backend_lite.py`, add a corresponding row

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Credits

- [pywebview](https://pywebview.flowrl.com/) — Lightweight Web UI
- [psutil](https://github.com/giampaolo/psutil) — System information
- [Font Awesome](https://fontawesome.com/) — Icons
- [ip-api.com](http://ip-api.com/) / [ipapi.co](https://ipapi.co/) — IP geolocation

---

If this project helps you, please consider giving it a Star.
