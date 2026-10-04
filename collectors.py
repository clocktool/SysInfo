import os
import sys
import socket
import platform
import subprocess
import uuid
from datetime import datetime

import psutil
import requests


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def get_local_ips():
    """只返回有意义的本地 IP：
       IPv4: 排除 127.* 和 169.254.*
       IPv6: 排除 ::1 和 fe80::
       带上网卡名称，方便区分多网卡
    """
    result = {"ipv4": [], "ipv6": []}

    def is_bad_v4(ip):
        if ip.startswith("127."):
            return True
        if ip.startswith("169.254."):
            return True
        return False

    def is_bad_v6(ip):
        low = ip.lower()
        if low == "::1":
            return True
        if low.startswith("fe80"):
            return True
        return False

    try:
        for name, addrs in psutil.net_if_addrs().items():
            for a in addrs:
                if a.family == socket.AF_INET:
                    if not is_bad_v4(a.address):
                        result["ipv4"].append({
                            "iface": name,
                            "addr": a.address,
                        })
                elif a.family == socket.AF_INET6:
                    # 去掉 IPv6 后面的 %网卡 后缀（如 fe80::1%eth0）
                    addr = a.address.split("%")[0]
                    if not is_bad_v6(addr):
                        result["ipv6"].append({
                            "iface": name,
                            "addr": addr,
                        })
    except Exception:
        pass

    return result


def get_mac():
    try:
        mac_int = uuid.getnode()
        mac_hex = ":".join(f"{(mac_int >> i) & 0xff:02x}" for i in range(40, -1, -8))
        return mac_hex
    except Exception:
        return None


def get_public_ip(timeout=5):
    """多个 API 尝试，兼容国内网络"""
    apis = [
        ("https://api.ipify.org?format=json", lambda d: d.get("ip")),
        ("https://ipapi.co/json/", lambda d: d.get("ip")),
        ("https://ip.seeip.org/jsonip", lambda d: d.get("ip")),
        ("http://ip-api.com/json/?fields=query", lambda d: d.get("query")),
    ]
    for url, parser in apis:
        try:
            r = requests.get(url, timeout=timeout,
                             headers={"User-Agent": "Mozilla/5.0"})
            data = r.json()
            ip = parser(data)
            if ip:
                return ip
        except Exception:
            continue
    return None


def get_public_ipv6(timeout=3):
    apis = [
        "https://api6.ipify.org?format=json",
        "https://v6.ident.me/",
    ]
    for url in apis:
        try:
            r = requests.get(url, timeout=timeout,
                             headers={"User-Agent": "Mozilla/5.0"})
            text = r.text.strip()
            # 有的返回 json，有的返回纯文本
            if text.startswith("{"):
                import json as _json
                data = _json.loads(text)
                ip = data.get("ip") or data.get("IPv6")
            else:
                ip = text
            if ip and ":" in ip:
                return ip
        except Exception:
            continue
    return None


def get_ip_geo(timeout=5):
    """多 API fallback，统一成同一套字段"""
    apis = [
        ("http://ip-api.com/json/?fields=66846719&lang=zh-CN", lambda d: {
            "status": d.get("status"),
            "country": d.get("country"),
            "countryCode": d.get("countryCode"),
            "regionName": d.get("regionName"),
            "city": d.get("city"),
            "zip": d.get("zip"),
            "lat": d.get("lat"),
            "lon": d.get("lon"),
            "timezone": d.get("timezone"),
            "isp": d.get("isp"),
            "org": d.get("org"),
            "as": d.get("as"),
            "query": d.get("query"),
        }),
        ("https://ipapi.co/json/", lambda d: {
            "status": "success" if d.get("ip") else "fail",
            "country": d.get("country_name"),
            "countryCode": d.get("country_code"),
            "regionName": d.get("region"),
            "city": d.get("city"),
            "zip": d.get("postal"),
            "lat": d.get("latitude"),
            "lon": d.get("longitude"),
            "timezone": d.get("timezone"),
            "isp": d.get("org"),
            "org": d.get("org"),
            "as": d.get("asn"),
            "query": d.get("ip"),
        }),
        ("https://ipwho.is/", lambda d: {
            "status": "success" if d.get("ip") else "fail",
            "country": d.get("country"),
            "countryCode": d.get("country_code"),
            "regionName": d.get("region"),
            "city": d.get("city"),
            "zip": d.get("postal"),
            "lat": d.get("latitude"),
            "lon": d.get("longitude"),
            "timezone": (d.get("timezone") or {}).get("id"),
            "isp": (d.get("connection") or {}).get("isp"),
            "org": (d.get("connection") or {}).get("org"),
            "as": (d.get("connection") or {}).get("asn"),
            "query": d.get("ip"),
        }),
    ]
    for url, mapper in apis:
        try:
            r = requests.get(url, timeout=timeout,
                             headers={"User-Agent": "Mozilla/5.0"})
            data = r.json()
            mapped = mapper(data)
            if mapped and mapped.get("country"):
                return mapped
        except Exception:
            continue
    return {}


def get_gateway_and_dns():
    """从 ipconfig 里解析网关和 DNS（优先 IPv4，过滤 link-local）"""
    gateway = None
    dns_servers = []
    try:
        out = subprocess.run(
            ["ipconfig", "/all"],
            capture_output=True, text=True,
            encoding="gbk", errors="ignore", timeout=5
        ).stdout

        # 网关
        gw_candidates = []
        for line in out.splitlines():
            if "Default Gateway" in line or "默认网关" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    gw = parts[1].strip()
                    if gw and gw.lower() != "none":
                        gw_candidates.append(gw)
        # 优先非 fe80 开头的 IPv4
        ipv4_gws = [g for g in gw_candidates if not g.lower().startswith("fe80")]
        gateway = ipv4_gws[0] if ipv4_gws else (gw_candidates[0] if gw_candidates else None)

        # DNS
        dns_list = []
        in_dns = False
        for line in out.splitlines():
            if "DNS Servers" in line or "DNS 服务器" in line:
                in_dns = True
                parts = line.split(":")
                if len(parts) >= 2 and parts[1].strip():
                    dns_list.append(parts[1].strip())
            elif in_dns:
                if line.startswith(" ") and line.strip():
                    dns_list.append(line.strip())
                else:
                    in_dns = False

        # 过滤 link-local IPv6
        dns_servers = [d for d in dns_list if not d.lower().startswith("fe80")]
    except Exception:
        pass

    return gateway, dns_servers


def get_system_info():
    vm = psutil.virtual_memory()
    disks = []
    for p in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(p.mountpoint)
            disks.append({
                "mount": p.mountpoint,
                "fstype": p.fstype,
                "total_gb": round(usage.total / 1e9, 1),
                "used_gb": round(usage.used / 1e9, 1),
                "percent": usage.percent,
            })
        except Exception:
            pass

    battery = None
    try:
        b = psutil.sensors_battery()
        if b:
            battery = {
                "percent": round(b.percent, 1),
                "plugged": b.power_plugged,
                "secsleft": b.secsleft if b.secsleft != psutil.POWER_TIME_UNLIMITED else None,
            }
    except Exception:
        pass

    return {
        "os": platform.platform(),
        "os_version": platform.version(),
        "hostname": socket.gethostname(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_logical": psutil.cpu_count(logical=True),
        "cpu_physical": psutil.cpu_count(logical=False),
        "cpu_freq_mhz": _safe(lambda: round(psutil.cpu_freq().current, 0)),
        "ram_total_gb": round(vm.total / 1e9, 2),
        "ram_used_gb": round(vm.used / 1e9, 2),
        "ram_percent": vm.percent,
        "disks": disks,
        "battery": battery,
        "python_version": sys.version.split()[0],
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_network_info():
    gateway, dns_servers = get_gateway_and_dns()
    return {
        "local_ips": get_local_ips(),
        "mac": get_mac(),
        "public_ipv4": get_public_ip(),
        "public_ipv6": get_public_ipv6(),
        "gateway": gateway,
        "dns_servers": dns_servers,
    }


def collect_all():
    return {
        "system": get_system_info(),
        "network": get_network_info(),
        "geo": get_ip_geo(),
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(collect_all(), indent=2, ensure_ascii=False))