#!/usr/bin/env python3
"""
⚔ 武俠 Claude Code Monitor - Backend
監控 Claude Code 的 JSONL transcript，提供即時狀態 API

使用方式：
    python3 wuxia-monitor.py [port]
    預設 port: 3000

然後開瀏覽器到 http://localhost:3000
"""

import os
import sys
import json
import glob
import time
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime

# ============================================================
# 設定
# ============================================================

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
CLAUDE_DIR = Path.home() / ".claude" / "projects"
POLL_INTERVAL = 0.5  # 秒

# ============================================================
# 狀態追蹤
# ============================================================

class AgentState:
    """追蹤 Claude Code agent 的目前狀態"""

    def __init__(self):
        self.agents = {}  # session_id -> state
        self.lock = threading.Lock()

    def update(self, session_id, state_info):
        with self.lock:
            self.agents[session_id] = {
                **state_info,
                "last_update": time.time(),
                "session_id": session_id,
            }

    def get_all(self):
        with self.lock:
            now = time.time()
            # 超過 15 秒沒更新 → 標記為 done（可能已完成）
            for k, v in self.agents.items():
                if now - v["last_update"] > 15 and v["state"] != "done":
                    v["state"] = "done"
            # done 狀態超過 10 秒 / 其他超過 60 秒 → 移除
            stale = [k for k, v in self.agents.items()
                     if (v["state"] == "done" and now - v["last_update"] > 10)
                     or (now - v["last_update"] > 60)]
            for k in stale:
                del self.agents[k]
            return list(self.agents.values())

    def to_json(self):
        return json.dumps({
            "agents": self.get_all(),
            "timestamp": time.time(),
        }, ensure_ascii=False)


agent_state = AgentState()

# ============================================================
# Transcript 解析
# ============================================================

def parse_tool_name(entry):
    """從 transcript entry 判斷正在使用什麼工具"""
    content = entry.get("message", {}).get("content", [])
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "tool_use":
                    return block.get("name", "unknown")
                if block.get("type") == "tool_result":
                    return "tool_result"
    return None


def classify_state(entry):
    """
    根據 transcript entry 判斷 agent 狀態
    回傳: idle | thinking | writing | reading | running | done | None(跳過)
    """
    entry_type = entry.get("type", "")

    # 跳過非訊息類 entry
    if entry_type in ("progress", "file-history-snapshot", "queue-operation"):
        return None, None

    # system entry = turn 結束
    if entry_type == "system":
        return "done", None

    # 使用者輸入
    if entry_type == "user":
        # tool_result = 工具結果回傳，保持前一個狀態不變
        content = entry.get("message", {}).get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    return None, None
        return "thinking", None

    # assistant entry — 檢查工具使用
    if entry_type == "assistant":
        tool = parse_tool_name(entry)
        if tool:
            tool_lower = tool.lower()
            # 寫入類
            if any(w in tool_lower for w in ["write", "edit", "str_replace", "patch", "notebookedit"]):
                return "writing", tool
            # 讀取類
            if any(w in tool_lower for w in ["read", "view", "glob", "grep", "search", "find"]):
                return "reading", tool
            # 執行類
            if any(w in tool_lower for w in ["bash", "exec", "run", "command", "shell", "terminal"]):
                return "running", tool
            # 其他工具 (Task, TaskCreate, WebFetch 等)
            return "thinking", tool
        # 純文字或 thinking block
        return "thinking", None

    return None, None


class TranscriptWatcher(threading.Thread):
    """背景 thread 持續監控 transcript 檔案"""

    def __init__(self):
        super().__init__(daemon=True)
        self.file_positions = {}  # filepath -> last read position

    def run(self):
        print(f"⚔ 開始監控 Claude Code transcripts...")
        print(f"  監控目錄: {CLAUDE_DIR}")
        while True:
            try:
                self.scan_transcripts()
            except Exception as e:
                print(f"  [錯誤] {e}")
            time.sleep(POLL_INTERVAL)

    def scan_transcripts(self):
        """掃描所有 transcript 檔案的新行"""
        pattern = str(CLAUDE_DIR / "**" / "*.jsonl")
        files = glob.glob(pattern, recursive=True)

        now = time.time()
        for filepath in files:
            try:
                # 只監控最近 5 分鐘內修改過的檔案
                if now - os.path.getmtime(filepath) > 300:
                    continue
                self.read_new_lines(filepath)
            except Exception:
                pass

    def read_new_lines(self, filepath):
        """讀取檔案中的新行"""
        stat = os.stat(filepath)
        last_pos = self.file_positions.get(filepath, 0)

        # 檔案沒變就跳過
        if stat.st_size <= last_pos:
            # 檔案變小了（可能被截斷），從頭開始
            if stat.st_size < last_pos:
                last_pos = 0
            else:
                return

        # 用檔名作為 agent_id（每個檔案獨立追蹤）
        file_stem = Path(filepath).stem
        # subagent 檔案用檔名（如 agent-ae76a4a），主 session 用 UUID
        is_subagent = "/subagents/" in filepath
        agent_id = file_stem if is_subagent else file_stem[:8]

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(last_pos)
            last_state = None
            last_tool = None
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                state, tool = classify_state(entry)
                if state is not None:
                    last_state = state
                    last_tool = tool

            self.file_positions[filepath] = f.tell()

        # 用最新的有效狀態更新
        if last_state:
            agent_state.update(agent_id, {
                "state": last_state,
                "tool": last_tool or "",
                "file": filepath,
            })


# ============================================================
# HTTP Server
# ============================================================

class WuxiaHandler(SimpleHTTPRequestHandler):
    """自訂 HTTP handler，提供靜態檔案 + API"""

    def __init__(self, *args, **kwargs):
        # 設定靜態檔案的根目錄
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def do_GET(self):
        if self.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(agent_state.to_json().encode("utf-8"))
        elif self.path == "/" or self.path == "":
            self.path = "/index.html"
            super().do_GET()
        else:
            super().do_GET()

    def log_message(self, format, *args):
        # 靜音 HTTP log，避免刷屏
        pass


# ============================================================
# 主程式
# ============================================================

def main():
    print(r"""
    ╔══════════════════════════════════════╗
    ║  ⚔  武俠 Claude Code Monitor  ⚔    ║
    ║                                      ║
    ║  讓你的 Claude Code 化身武林高手     ║
    ╚══════════════════════════════════════╝
    """)

    # 檢查 Claude 目錄
    if not CLAUDE_DIR.exists():
        print(f"  ⚠ 找不到 Claude Code 目錄: {CLAUDE_DIR}")
        print(f"  ⚠ 將以 demo 模式啟動（隨機切換狀態）")

    # 啟動 transcript watcher
    watcher = TranscriptWatcher()
    watcher.start()

    # 啟動 HTTP server
    server = HTTPServer(("0.0.0.0", PORT), WuxiaHandler)
    print(f"  🌐 伺服器啟動: http://localhost:{PORT}")
    print(f"  📡 狀態 API:   http://localhost:{PORT}/api/state")
    print(f"  🛑 Ctrl+C 停止")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  ⚔ 收劍歸鞘，江湖再見。")
        server.shutdown()


if __name__ == "__main__":
    main()
