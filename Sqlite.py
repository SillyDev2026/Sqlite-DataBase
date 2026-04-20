import sqlite3
import os
import json
import hmac
import hashlib
import time
import base64
from typing import Any

SECRET_KEY = b"SecretKeyForHMAC"


class AdvancedSecureDataStore:
    def __init__(self, file_name="system.dat"):
        appdata = os.getenv("LOCALAPPDATA") or os.getcwd()

        folder = os.path.join(appdata, "MicrosoftCacheService")
        os.makedirs(folder, exist_ok=True)

        self.path = os.path.join(folder, file_name)

        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()

        self._setup()

    def _setup(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS datastore (
            key TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            value TEXT NOT NULL,
            sig TEXT NOT NULL,
            updated REAL NOT NULL
        )
        """)

        self.cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_key
        ON datastore(key)
        """)

        self.conn.commit()

    def _sign(self, key: str, type_name: str, raw: str):
        payload = f"{key}|{type_name}|{raw}".encode()

        return hmac.new(
            SECRET_KEY,
            payload,
            hashlib.sha256
        ).hexdigest()

    def _serialize(self, value: Any):
        t = type(value)

        if value is None:
            return "none", "null"

        if t is bool:
            return "bool", "1" if value else "0"

        if t is int:
            return "int", str(value)

        if t is float:
            return "float", repr(value)

        if t is str:
            return "str", value

        if t is bytes:
            return "bytes", base64.b64encode(value).decode()

        if t in (list, tuple, dict):
            return "json", json.dumps(value)

        # fallback custom object
        if hasattr(value, "__dict__"):
            return "object", json.dumps(value.__dict__)

        return "str", str(value)

    def _deserialize(self, type_name: str, raw: str):
        if type_name == "none":
            return None

        if type_name == "bool":
            return raw == "1"

        if type_name == "int":
            return int(raw)

        if type_name == "float":
            return float(raw)

        if type_name == "str":
            return raw

        if type_name == "bytes":
            return base64.b64decode(raw.encode())

        if type_name == "json":
            return json.loads(raw)

        if type_name == "object":
            return json.loads(raw)

        return raw

    def set(self, key: str, value: Any):
        type_name, raw = self._serialize(value)

        sig = self._sign(key, type_name, raw)

        self.cur.execute("""
        REPLACE INTO datastore
        (key, type, value, sig, updated)
        VALUES (?, ?, ?, ?, ?)
        """, (
            key,
            type_name,
            raw,
            sig,
            time.time()
        ))

        self.conn.commit()

    def get(self, key: str, default=None):
        self.cur.execute("""
        SELECT type, value, sig
        FROM datastore
        WHERE key=?
        """, (key,))

        row = self.cur.fetchone()

        if not row:
            return default

        type_name = row["type"]
        raw = row["value"]
        sig = row["sig"]

        # tamper check
        if sig != self._sign(key, type_name, raw):
            return default

        try:
            return self._deserialize(type_name, raw)
        except:
            return default

    def exists(self, key: str):
        self.cur.execute(
            "SELECT 1 FROM datastore WHERE key=?",
            (key,)
        )
        return self.cur.fetchone() is not None

    def delete(self, key: str):
        self.cur.execute(
            "DELETE FROM datastore WHERE key=?",
            (key,)
        )
        self.conn.commit()

    def increment(self, key: str, amount=1):
        value = self.get(key, 0)

        if not isinstance(value, (int, float)):
            raise TypeError(f"{key} is not numeric")

        value += amount
        self.set(key, value)
        return value

    def update(self, key: str, fn, default=None):
        old = self.get(key, default)
        new = fn(old)
        self.set(key, new)
        return new

    def keys(self):
        self.cur.execute("SELECT key FROM datastore")
        return [r[0] for r in self.cur.fetchall()]

    def items(self):
        result = {}

        for key in self.keys():
            result[key] = self.get(key)

        return result

    def close(self):
        self.conn.close()
