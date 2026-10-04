import sys
import os
import ctypes


# ============ DPI Aware（tkinter 兼容版需要） ============
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


# ============ WebView2 检测 ============
def has_webview2():
    """
    检测 Windows 上是否安装了 WebView2 Runtime。
    检测失败（非 Windows / 注册表访问失败）时返回 True，
    让流程继续走"尝试高级版"的逻辑。
    """
    try:
        import winreg
    except Exception:
        return True  # 非 Windows，不拦

    keys = [
        r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F1E7E4A0-6F20-4F4E-A54F-C8C0D1E5FBE1}",
        r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F1E7E4A0-6F20-4F4E-A54F-C8C0D1E5FBE1}",
    ]

    for k in keys:
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                key = winreg.OpenKey(hive, k)
                winreg.CloseKey(key)
                return True
            except Exception:
                continue

    # 额外检查：直接找 WebView2 安装目录
    possible_paths = [
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft", "EdgeWebView", "Application"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft", "EdgeWebView", "Application"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "EdgeWebView", "Application"),
    ]
    for p in possible_paths:
        if p and os.path.isdir(p):
            return True

    return False


# ============ 启动器主流程 ============
def main():
    # 1) 先检测 WebView2
    has_wv2 = has_webview2()
    print(f"[launcher] WebView2 可用: {has_wv2}")

    if has_wv2:
        # 2) 尝试高级版
        try:
            print("[launcher] 尝试启动高级版...")
            from backend_web import run_web
            run_web()
            return  # 高级版正常退出
        except Exception as e:
            print(f"[launcher] 高级版启动失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("[launcher] 未检测到 WebView2，跳过高级版")

    # 3) 降级到兼容版（tkinter）
    try:
        print("[launcher] 降级到兼容版（tkinter）...")
        from backend_lite import run_lite
        run_lite()
        return
    except Exception as e:
        print(f"[launcher] 兼容版也失败: {e}")
        import traceback
        traceback.print_exc()

    # 4) 两种都失败 → 弹错误框
    try:
        import tkinter as tk
        import tkinter.messagebox as mb
        r = tk.Tk()
        r.withdraw()
        mb.showerror(
            "启动失败",
            "程序无法启动。\n\n"
            "可能原因：\n"
            "  1. WebView2 Runtime 未安装\n"
            "  2. 系统缺少必要组件\n"
            "  3. 文件夹中缺少 web/ 或 backend_*.py\n\n"
            f"详细错误见控制台输出。"
        )
        r.destroy()
    except Exception:
        pass

    sys.exit(1)


if __name__ == "__main__":
    main()