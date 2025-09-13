#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk


# ---------------- 工具函数 ----------------
def get_lan_ip():
    """获取本机局域网 IPv4（非 127.0.0.1）"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'


# ---------------- 主界面 ----------------
class FlaskServerTk(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Flask IM 服务器控制台")
        self.geometry("650x500")
        self.resizable(False, False)

        self.config_file = Path("config.json")
        self.config = self.load_config()
        self.proc: subprocess.Popen | None = None
        self.reader_thread = None

        # ---------- 界面 ----------
        cfg_frame = ttk.LabelFrame(self, text="配置", padding=10)
        cfg_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(cfg_frame, text="用户数据过期时间：(h)").grid(row=0, column=0, sticky="e")
        self.sb_hours = tk.Spinbox(cfg_frame, from_=0.01, to=8760, increment=0.5)
        self.sb_hours.delete(0, "end")
        self.sb_hours.insert(0, str(self.config.get("expire_hours", 12)))
        self.sb_hours.grid(row=0, column=1, sticky="w")

        self.clear_var = tk.BooleanVar(value=self.config.get("clear_on_start", True))
        self.ck_clear = ttk.Checkbutton(cfg_frame, text="启动前清空 data", variable=self.clear_var)
        self.ck_clear.grid(row=1, column=0, columnspan=2, sticky="w")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        self.btn_start = ttk.Button(btn_frame, text="启动服务器", command=self.start_server)
        self.btn_start.pack(side="left", padx=5)
        self.btn_stop = ttk.Button(btn_frame, text="停止服务器", command=self.stop_server, state="disabled")
        self.btn_stop.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="保存配置", command=self.save_config).pack(side="left", padx=5)

        log_frame = ttk.LabelFrame(self, text="日志", padding=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_text = tk.Text(log_frame, height=15, state="disabled")
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- 配置 ----------
    def load_config(self):
        return json.loads(self.config_file.read_text()) if self.config_file.exists() else {"expire_hours": 12, "clear_on_start": True}

    def save_config(self):
        self.config = {"expire_hours": float(self.sb_hours.get()), "clear_on_start": self.clear_var.get()}
        self.config_file.write_text(json.dumps(self.config, indent=2))
        self.log("配置已保存 → config.json")

    # ---------- 日志 ----------
    def log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{datetime.now():%H:%M:%S}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # ---------- 启停 ----------
    def start_server(self):
        if self.proc and self.proc.poll() is None:
            return
        self.log("正在启动 Flask 服务器…")

        if self.clear_var.get():
            data_dir = Path("data")
            if data_dir.exists():
                import shutil
                shutil.rmtree(data_dir)
                self.log("已清空 data 目录")

        os.environ["EXPIRE_HOURS"] = str(float(self.sb_hours.get()))

        self.proc = subprocess.Popen([sys.executable, "app.py"],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     text=True, bufsize=1)
        self.reader_thread = threading.Thread(target=self._read_proc, daemon=True)
        self.reader_thread.start()

        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.log("Flask 已启动（端口 8888）")

        # >>> 动态获取 IP 并自动打开网页 <<<
        ip = get_lan_ip()
        target = f"http://{ip}:8888"
        threading.Timer(1.5, lambda: self.open_browser(target)).start()
        self.log(f"已自动打开 {target}")

    def open_browser(self, url):
        import webbrowser
        webbrowser.open(url)

    def _read_proc(self):
        for line in iter(self.proc.stdout.readline, ""):
            self.log(line.rstrip())
        self.proc.stdout.close()

    def stop_server(self):
        if self.proc is None:
            return
        self.log("正在停止服务器…")
        self.proc.terminate()
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        self.proc = None
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.log("Flask 已退出")

    # ---------- 关闭 ----------
    def on_close(self):
        if self.proc:
            self.stop_server()
        self.save_config()
        self.destroy()


# -------------------- main --------------------
if __name__ == "__main__":
    app = FlaskServerTk()
    app.mainloop()