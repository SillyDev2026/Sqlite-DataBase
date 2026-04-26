from Pipeline import Pipeline
from Sqlite import AdvancedSecureDataStore


class Backend:
    def __init__(self, file_name="data.db"):
        self.data = AdvancedSecureDataStore(file_name)
        self.closed = False

    def pipeline(self):
        pipe = Pipeline()
        pipe.context = {
            "db": self.data,
            "backend": self
        }
        return pipe

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        if self.closed:
            return value

        self.data.set(key, value)
        return value

    def exists(self, key):
        return self.data.exists(key)

    def delete(self, key):
        if self.closed:
            return False

        self.data.delete(key)
        return True

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def lock(self, key, ttl=120):
        """
        Claims session lock.
        Returns True if locked.
        Returns False if another server owns it.
        """
        return self.data.lock_session(key, ttl)

    def unlock(self, key):
        """
        Releases lock if owned by this server.
        """
        self.data.unlock_session(key)

    def is_locked(self, key):
        """
        Returns True if any active lock exists.
        """
        return self.data.is_locked(key)

    def refresh_lock(self, key, ttl=120):
        """
        Refresh lock expiration if already owner.
        """
        return self.data.lock_session(key, ttl)

    def session_get(self, key, default=None, ttl=120):
        """
        Locks then loads data.
        """
        if not self.lock(key, ttl):
            return None

        return self.get(key, default)

    def session_save(self, key, value, ttl=120):
        """
        Save while refreshing lock.
        """
        if not self.refresh_lock(key, ttl):
            return False

        self.set(key, value)
        return True

    def session_release(self, key, value=None):
        """
        Optional save then unlock.
        """
        if value is not None:
            self.set(key, value)

        self.unlock(key)
        return True

    def _ensure_number(self, value, default):
        return value if isinstance(value, (int, float)) else default

    def increment(self, key, amount=1, default=0):
        value = self._ensure_number(
            self.data.get(key, default),
            default
        )

        value += amount
        self.data.set(key, value)

        return value

    def decrement(self, key, amount=1, default=0):
        return self.increment(key, -amount, default)

    def multiply(self, key, amount=2, default=0):
        value = self._ensure_number(
            self.data.get(key, default),
            default
        )

        value *= amount
        self.data.set(key, value)

        return value

    def divide(self, key, amount=2, default=0):
        if amount == 0:
            return default

        value = self._ensure_number(
            self.data.get(key, default),
            default
        )

        value = value / amount
        self.data.set(key, value)

        return value

    def append(self, key, value, default=None):
        arr = self.data.get(key, default or [])

        if not isinstance(arr, list):
            arr = []

        arr.append(value)
        self.data.set(key, arr)

        return arr

    def remove(self, key, value, default=None):
        arr = self.data.get(key, default or [])

        if not isinstance(arr, list):
            arr = []

        arr = [x for x in arr if x != value]
        self.data.set(key, arr)

        return arr

    def update(self, key, fn, default=None):
        value = self.data.get(key, default)
        new_value = fn(value)

        self.data.set(key, new_value)

        return new_value

    def close(self):
        if self.closed:
            return

        self.closed = True
        self.data.close()
