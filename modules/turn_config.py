"""Cloudflare Realtime TURN credential helper.

Keep long-lived TURN key material in Streamlit server-side secrets. The app
requests short-lived ICE credentials at runtime.
"""
import json
import urllib.error
import urllib.request

import streamlit as st


def get_ice_servers():
    """Return Cloudflare STUN/TURN servers, falling back to public STUN."""
    key_id = st.secrets.get("CLOUDFLARE_TURN_KEY_ID", "")
    key_token = st.secrets.get("CLOUDFLARE_TURN_KEY_API_TOKEN", "")

    if not key_id or not key_token:
        return [{"urls": ["stun:stun.cloudflare.com:3478"]}], False, "TURN is not configured. Using STUN only."

    endpoint = (
        "https://rtc.live.cloudflare.com/v1/turn/keys/"
        f"{key_id}/credentials/generate-ice-servers"
    )
    payload = json.dumps({"ttl": 86400}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {key_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
        ice_servers = data.get("iceServers", [])
        cleaned = []
        for server in ice_servers:
            urls = server.get("urls", [])
            if isinstance(urls, str):
                urls = [urls]
            urls = [url for url in urls if ":53" not in url]
            if not urls:
                continue
            item = {"urls": urls}
            if server.get("username"):
                item["username"] = server["username"]
            if server.get("credential"):
                item["credential"] = server["credential"]
            cleaned.append(item)

        has_turn = any(
            any(url.startswith(("turn:", "turns:")) for url in item["urls"])
            for item in cleaned
        )
        if not has_turn:
            raise RuntimeError("No usable TURN relay URLs returned.")
        return cleaned, True, "Cloudflare TURN credentials loaded."
    except (urllib.error.URLError, TimeoutError, ValueError, RuntimeError) as exc:
        return [{"urls": ["stun:stun.cloudflare.com:3478"]}], False, (
            f"Could not obtain TURN credentials ({type(exc).__name__}). Using STUN only."
        )
