import os
import sys
import json
import threading
import http.server
import socketserver
from functools import partial

from collectors import collect_all

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
WEB_DIR = os.path.join(RESOURCE_DIR, "web")


# ============ 简单 HTTP 服务（提供 API + 静态文件） ============
class ApiHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/api/all":
            try:
                data = collect_all()
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass  # 屏蔽日志


def start_server(port=0):
    """启动本地 HTTP 服务，返回实际端口"""
    # 自检：web/index.html 必须存在
    index_path = os.path.join(WEB_DIR, "index.html")
    if not os.path.exists(index_path):
        raise RuntimeError(f"缺少 web/index.html: {index_path}")

    handler = ApiHandler
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    actual_port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return actual_port, httpd


# ============ 入口 ============
def run_web():
    import webview   # 挪到函数内部，方便启动器捕获失败
    port, httpd = start_server()
    print(f"本地服务端口: {port}")

    url = f"http://127.0.0.1:{port}/index.html"

    window = webview.create_window(
        "设备信息查询器",
        url,
        width=1000,
        height=780,
        min_size=(800, 600),
    )
    webview.start()
    httpd.shutdown()