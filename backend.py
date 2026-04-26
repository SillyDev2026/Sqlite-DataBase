from Pipeline import Pipeline
from Sqlite import AdvancedSecureDataStore


class Backend:
    def __init__(self, file_name="system.dat"):
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
        self.data.delete(key)
        return True

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def _run(self, key, op, default):
        pipe = self.pipeline()

        pipe.step(lambda _, c: c["db"].get(key, default))
        pipe.step(lambda v, c: op(v))
        pipe.step(lambda v, c: (c["db"].set(key, v), v)[1])

        try:
            result, _ = pipe.run(None)
        except Exception:
            return default

        return result if result is not None else default

    def increment(self, key, amount=1, default=0):
        return self._run(key, lambda v: v + amount, default)

    def decrement(self, key, amount=1, default=0):
        return self._run(key, lambda v: v - amount, default)

    def multiply(self, key, amount=2, default=0):
        return self._run(key, lambda v: v * amount, default)

    def divide(self, key, amount=2, default=0):
        return self._run(key, lambda v: v if amount == 0 else v / amount, default)

    def append(self, key, value, default=None):
        if default is None:
            default = []
        return self._run(key, lambda arr: arr + [value], default)

    def remove(self, key, value, default=None):
        if default is None:
            default = []
        return self._run(key, lambda arr: [x for x in arr if x != value], default)

    def update(self, key, fn, default=None):
        pipe = self.pipeline()

        pipe.step(lambda _, c: c["db"].get(key, default))
        pipe.step(lambda v, c: fn(v))
        pipe.step(lambda v, c: (c["db"].set(key, v), v)[1])

        try:
            result, _ = pipe.run(None)
        except Exception:
            return default

        return result

    def close(self):
        if self.closed:
            return
        self.data.close()
        self.closed = True
