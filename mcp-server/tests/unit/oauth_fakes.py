"""Dict-backed fake Firestore for OAuth store tests.

Supports the exact API surface the stores use: collection().document()
get/set/update/delete, equality where-chains with get(), and snapshot
``.reference`` for bulk updates. One shared implementation so every suite
decodes storage behavior identically.
"""

from typing import Any, Dict


class FakeSnapshot:
    def __init__(self, ref, data):
        self.reference = ref
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return dict(self._data) if self._data is not None else None


class FakeDocRef:
    def __init__(self, store: Dict[str, dict], doc_id: str):
        self._store = store
        self._id = doc_id

    def get(self):
        return FakeSnapshot(self, self._store.get(self._id))

    def set(self, data: dict):
        self._store[self._id] = dict(data)

    def update(self, fields: dict):
        if self._id not in self._store:
            raise KeyError(self._id)
        self._store[self._id].update(fields)

    def delete(self):
        self._store.pop(self._id, None)


class FakeQuery:
    def __init__(self, store: Dict[str, dict], filters):
        self._store = store
        self._filters = filters
        self._limit = None

    def where(self, field, op, value):
        assert op == "=="
        return FakeQuery(self._store, self._filters + [(field, value)])

    def limit(self, n):
        query = FakeQuery(self._store, self._filters)
        query._limit = n
        return query

    def get(self):
        results = []
        for doc_id, data in list(self._store.items()):
            if all(data.get(f) == v for f, v in self._filters):
                results.append(FakeSnapshot(FakeDocRef(self._store, doc_id), data))
            if self._limit and len(results) >= self._limit:
                break
        return results


class FakeCollection:
    def __init__(self, store: Dict[str, dict]):
        self._store = store

    def document(self, doc_id: str):
        return FakeDocRef(self._store, doc_id)

    def where(self, field, op, value):
        return FakeQuery(self._store, []).where(field, op, value)


class FakeFirestore:
    def __init__(self):
        self.data: Dict[str, Dict[str, dict]] = {}

    def collection(self, name: str):
        return FakeCollection(self.data.setdefault(name, {}))
