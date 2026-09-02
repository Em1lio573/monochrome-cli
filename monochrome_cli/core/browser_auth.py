import asyncio
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from monochrome_cli.config import config


class BrowserAuth:
    """
    Background browser manager to automatically obtain and refresh
    Cloudflare Turnstile JWT tokens for Super High Quality (Lossless 24-bit CENC) downloads.
    """

    @classmethod
    def is_jwt_valid(cls, jwt: Optional[str]) -> bool:
        if not jwt or not jwt.strip():
            return False
        try:
            # Check JWT expiration
            parts = jwt.split(".")
            if len(parts) < 2:
                return False
            import base64
            padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
            exp = payload.get("exp", 0)
            return time.time() < (exp - 60)
        except Exception:
            return True

    @classmethod
    def get_valid_jwt(cls, force_refresh: bool = False) -> Optional[str]:
        current_jwt = config.turnstile_jwt
        if not force_refresh and cls.is_jwt_valid(current_jwt):
            return current_jwt

        # Attempt to obtain JWT via background browser
        jwt = cls._solve_turnstile_background()
        if jwt:
            config.turnstile_jwt = jwt
            return jwt

        return None

    @classmethod
    def _find_chrome_executable(cls) -> Optional[str]:
        candidates = [
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
            "brave-browser",
        ]
        for name in candidates:
            path = shutil.which(name)
            if path:
                return path
        return None

    @classmethod
    def _solve_turnstile_background(cls) -> Optional[str]:
        chrome_bin = cls._find_chrome_executable()
        if not chrome_bin:
            return None

        port = 9288
        proc = None
        try:
            cmd = [
                chrome_bin,
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                f"--remote-debugging-port={port}",
                "https://monochrome.tf",
            ]
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)

            # Query DevTools HTTP endpoint
            req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=4)
            tabs = json.loads(req.read().decode())
            ws_url = None
            for t in tabs:
                if "monochrome.tf" in t.get("url", ""):
                    ws_url = t.get("webSocketDebuggerUrl")
                    break
            if not ws_url and tabs:
                ws_url = tabs[0].get("webSocketDebuggerUrl")

            if not ws_url:
                return None

            return asyncio.run(cls._cdp_extract_jwt(ws_url))
        except Exception:
            return None
        finally:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except Exception:
                    pass

    @classmethod
    async def _cdp_extract_jwt(cls, ws_url: str) -> Optional[str]:
        try:
            import websockets
        except ImportError:
            return None

        try:
            async with websockets.connect(ws_url) as ws:
                await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
                await asyncio.sleep(2)

                # Check localStorage for token
                expr = "localStorage.getItem(\"unified-playback-turnstile-jwt\")"
                await ws.send(json.dumps({
                    "id": 2,
                    "method": "Runtime.evaluate",
                    "params": {"expression": expr, "returnByValue": True}
                }))

                for _ in range(15):
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if data.get("id") == 2:
                        res = data.get("result", {}).get("result", {}).get("value")
                        if res and isinstance(res, str) and len(res) > 20:
                            return res
                        break
        except Exception:
            return None

        return None\n