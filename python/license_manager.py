"""
license_manager.py
------------------
Core licensing logic for Black Copper Label Studio.
Uses HMAC-SHA256 to create verifiable, machine-bound license files.

Developer (Irfan Ahmad) uses keygen_tool.py to generate license.bc files.
Clients place license.bc in the same folder as the application .exe.
"""

import hashlib
import json
import os
import sys
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# Internal secret (split to make simple string search harder)
# ─────────────────────────────────────────────────────────────────────────────
_P = ["B", "L", "4", "C", "K", "-", "C", "0", "P", "P", "3", "R", "-", "S", "T", "U", "D", "I", "0", "-", "2", "0", "2", "5"]
_SECRET = "".join(_P)


# ─────────────────────────────────────────────────────────────────────────────
# Machine Identification
# ─────────────────────────────────────────────────────────────────────────────

def get_machine_id() -> str:
    """Return a 16-char uppercase hex ID for this computer.

    Primary:  Windows motherboard UUID via wmic (most stable, survives reboots/
              driver changes).
    Fallback: MAC address.
    """
    raw: str | None = None

    # --- Windows BIOS UUID (primary) ---
    try:
        import subprocess
        result = subprocess.run(
            ["wmic", "csproduct", "get", "UUID", "/value"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if "=" in line and "UUID" in line:
                val = line.split("=", 1)[1].strip()
                if val and val not in ("", "(null)", "To be filled by O.E.M.", "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF"):
                    raw = val
                    break
    except Exception:
        pass

    # --- MAC address fallback ---
    if not raw:
        import uuid as _uuid
        raw = str(_uuid.getnode())

    return hashlib.sha256(f"BCSTUDIO-{raw}".encode()).hexdigest()[:16].upper()


# ─────────────────────────────────────────────────────────────────────────────
# Signature helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sign(machine_id: str, client_name: str, expiry: str) -> str:
    """Compute a 24-char HMAC-SHA256 hex signature."""
    import hmac
    payload = f"{machine_id}||{client_name}||{expiry}"
    sig = hmac.new(_SECRET.encode(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return sig[:24].upper()


def _format_key(sig24: str) -> str:
    """Format 24-char signature as XXXXXX-XXXXXX-XXXXXX-XXXXXX key."""
    return f"{sig24[:6]}-{sig24[6:12]}-{sig24[12:18]}-{sig24[18:24]}"


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_license(machine_id: str, client_name: str, expiry: str = "lifetime") -> dict:
    """Create and return a license dict.  Call from keygen_tool.py only.

    Args:
        machine_id:   16-char ID obtained from get_machine_id() on the client PC.
        client_name:  Client's name / company (stored in the license).
        expiry:       "lifetime"  OR  "YYYY-MM-DD" for annual/timed licenses.

    Returns:
        dict that can be saved as JSON → license.bc
    """
    sig = _sign(machine_id, client_name, expiry)
    return {
        "product": "Black Copper Label Studio",
        "machine_id": machine_id,
        "client_name": client_name,
        "expiry": expiry,
        "key": _format_key(sig),
        "issued": datetime.now().strftime("%Y-%m-%d"),
    }


def get_license_path() -> str:
    """Return path to license.bc (same directory as the .exe or script)."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "license.bc")


def load_license() -> dict | None:
    """Load and parse license.bc.  Returns None if missing or corrupt."""
    path = get_license_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def validate_license(lic: dict | None) -> tuple[bool, str]:
    """Validate a loaded license dict.

    Returns:
        (True,  client_name)  on success
        (False, error_reason) on failure
    """
    if not lic:
        return False, "No license file found."

    try:
        machine_id  = lic.get("machine_id", "")
        client_name = lic.get("client_name", "Unknown")
        expiry      = lic.get("expiry", "")
        key         = lic.get("key", "")

        # 1. Machine check
        if machine_id != get_machine_id():
            return False, "License is not valid for this computer."

        # 2. Signature check
        expected = _format_key(_sign(machine_id, client_name, expiry))
        if key != expected:
            return False, "License key is invalid or has been tampered with."

        # 3. Expiry check
        if expiry != "lifetime":
            exp_date = datetime.strptime(expiry, "%Y-%m-%d")
            if datetime.now() > exp_date:
                return False, f"License expired on {expiry}. Please renew."

        return True, client_name

    except Exception as exc:
        return False, f"License error: {exc}"


def save_license(lic_dict: dict, path: str | None = None) -> None:
    """Write license dict to disk as JSON."""
    dest = path or get_license_path()
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(lic_dict, fh, indent=2)
