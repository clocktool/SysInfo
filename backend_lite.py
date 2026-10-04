import os
import sys
import ctypes
import threading
import tkinter as tk
from tkinter import ttk

from collectors import collect_all


# ============ DPI Aware ============
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


# ============ 路径 ============
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_resource_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
RESOURCE_DIR = get_resource_dir()


# ============ UI ============
class App:
    def __init__(self, root):
        self.root = root
        root.title("设备信息查询器（兼容版）")

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        w = min(960, int(sw * 0.7))
        h = min(760, int(sh * 0.85))
        root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        root.minsize(720, 560)

        self._build_ui()

        # 图标
        try:
            ico_path = os.path.join(RESOURCE_DIR, "app.ico")
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except Exception:
            pass

        # 自动开始采集
        self.root.after(100, self.refresh)

    def _build_ui(self):
        # 顶部工具栏
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=(10, 4))

        ttk.Label(top, text="设备信息查询器",
                  font=("Microsoft YaHei UI", 14, "bold")).pack(side="left")

        ttk.Button(top, text="重新扫描",
                   command=self.refresh).pack(side="right")

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(top, textvariable=self.status_var,
                  foreground="#666").pack(side="right", padx=(0, 12))

        # 内容：可滚动
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        self.canvas = canvas

    def refresh(self):
        self.status_var.set("正在采集…")
        self.root.update_idletasks()

        def work():
            try:
                data = collect_all()
            except Exception as e:
                data = {"error": str(e)}
            self.root.after(0, lambda: self._render(data))

        threading.Thread(target=work, daemon=True).start()

    def _render(self, data):
        # 清空
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        if "error" in data:
            ttk.Label(self.scroll_frame,
                      text=f"采集失败: {data['error']}",
                      foreground="red").pack(pady=20)
            self.status_var.set("失败")
            return

        # 系统信息
        self._section("系统信息", [
            ("操作系统", data["system"]["os"]),
            ("主机名", data["system"]["hostname"]),
            ("架构", data["system"]["machine"]),
            ("CPU", data["system"]["processor"]),
            ("CPU 核心",
             f"{data['system']['cpu_logical']} 逻辑 / {data['system']['cpu_physical']} 物理"),
            ("内存",
             f"{data['system']['ram_used_gb']} / {data['system']['ram_total_gb']} GB "
             f"({data['system']['ram_percent']}%)"),
            ("Python", data["system"]["python_version"]),
            ("启动时间", data["system"]["boot_time"]),
        ])

        # 硬件
        hw = []
        for d in data["system"]["disks"]:
            hw.append((f"{d['mount']} ({d['fstype']})",
                       f"{d['used_gb']} / {d['total_gb']} GB ({d['percent']}%)"))
        if data["system"]["battery"]:
            b = data["system"]["battery"]
            hw.append(("电池电量", f"{b['percent']}%"))
            hw.append(("电池状态", "充电中" if b["plugged"] else "使用中"))
        if hw:
            self._section("硬件", hw)

        # 网络
        net = data["network"]
        local_v4 = ", ".join(x["addr"] for x in net["local_ips"]["ipv4"]) or "无"
        local_v6 = ", ".join(x["addr"] for x in net["local_ips"]["ipv6"]) or "无"
        self._section("网络地址", [
            ("公网 IPv4", net["public_ipv4"] or "无"),
            ("公网 IPv6", net["public_ipv6"] or "无"),
            ("本地 IPv4", local_v4),
            ("本地 IPv6", local_v6),
            ("MAC 地址", net["mac"] or "未知"),
            ("网关", net["gateway"] or "未知"),
            ("DNS", ", ".join(net["dns_servers"]) or "未知"),
        ])

        # 地理
        geo = data.get("geo") or {}
        if geo.get("country"):
            self._section("IP 地理位置", [
                ("国家 / 地区",
                 f"{geo.get('country')} ({geo.get('countryCode', '')})"),
                ("地区", geo.get("regionName", "")),
                ("城市", geo.get("city", "")),
                ("纬度 / 经度", f"{geo.get('lat')}, {geo.get('lon')}"),
                ("时区", geo.get("timezone", "")),
                ("ISP", geo.get("isp", "")),
                ("组织", geo.get("org", "")),
                ("AS", geo.get("as", "")),
            ])

        self.status_var.set(f"采集完成 · {data['collected_at']}")

    def _section(self, title, rows):
        frame = ttk.LabelFrame(self.scroll_frame, text=title)
        frame.pack(fill="x", padx=4, pady=6)

        for k, v in rows:
            row = ttk.Frame(frame)
            row.pack(fill="x", padx=8, pady=2)

            ttk.Label(row, text=k, foreground="#3e6c8f",
                      width=14, anchor="w").pack(side="left")

            value = str(v) if v else "—"
            entry = ttk.Entry(row)
            entry.insert(0, value)
            entry.config(state="readonly")
            entry.pack(side="left", fill="x", expand=True)

            # 复制按钮
            ttk.Button(row, text="复制", width=6,
                       command=lambda v=value: self._copy(v)
                       ).pack(side="right", padx=(4, 0))

    def _copy(self, text):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_var.set(f"已复制: {text[:30]}")
            self.root.after(1500, lambda: self.status_var.set("就绪"))
        except Exception:
            pass


def run_lite():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "winnative" in style.theme_names():
            style.theme_use("winnative")
    except Exception:
        pass
    App(root)
    root.mainloop()
