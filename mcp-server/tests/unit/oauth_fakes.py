"""Dict-backed fake Firestore for OAuth store tests — now with transactions.

Supports document get/set/update/delete, equality where-chains, AND a
transaction protocol with OPTIMISTIC CONCURRENCY that MODELS production
Firestore: each document carries a hidden version (absent documents are
version 0, so creating one a transaction read also conflicts); a transaction
records the versions it read and, at commit, aborts with a conflict if any of
them changed. `run_transaction` (stores.py) then retries. A `barrier` hook
lets a test force two transactions to both read before either commits, so
"exactly one winner" is a real, reproducible assertion — not a mock of the
outcome (T P0-3).

Model disclosure: production server-client transactions take READ LOCKS
instead of validating versions — a competing write waits rather than
aborting the reader — so "the tombstone commits inside the window" here
corresponds to "the tombstone waits until after the commit" there; both
orderings are covered by the round-3 suite. Like the real client, a
transaction refuses a read after its first buffered write.
"""

from typing import Any, Callable, Dict, Optional

# Production defines the conflict type; the fake raises the same class so
# stores.run_transaction retries identically (never a test→prod import cycle).
from verifimind_mcp.oauth.stores import TransactionConflict


class FakeSnapshot:
    def __init__(self, ref, data, version):
        self.reference = ref
        self._data = data
        self._version = version

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return dict(self._data) if self._data is not None else None


class FakeDocRef:
    def __init__(self, store, doc_id):
        self._store = store
        self._id = doc_id

    def get(self):
        return self._store._snapshot(self._id)

    def set(self, data):
        self._store._write(self._id, dict(data))

    def update(self, fields):
        current = self._store._raw(self._id)
        if current is None:
            raise KeyError(self._id)
        merged = dict(current)
        merged.update(fields)
        self._store._write(self._id, merged)

    def delete(self):
        self._store._remove(self._id)


class FakeQuery:
    def __init__(self, store, filters, limit=None):
        self._store = store
        self._filters = filters
        self._limit = limit

    def where(self, field, op, value):
        assert op == "=="
        return FakeQuery(self._store, self._filters + [(field, value)], self._limit)

    def limit(self, n):
        return FakeQuery(self._store, self._filters, n)

    def get(self):
        results = []
        for doc_id, (data, _v) in list(self._store._docs.items()):
            if all(data.get(f) == v for f, v in self._filters):
                results.append(
                    FakeSnapshot(FakeDocRef(self._store, doc_id), data, _v)
                )
            if self._limit and len(results) >= self._limit:
                break
        return results

    def stream(self):
        return iter(self.get())


class _Collection:
    def __init__(self, store):
        self._store = store

    def document(self, doc_id):
        return FakeDocRef(self._store, doc_id)

    def where(self, field, op, value):
        return FakeQuery(self._store, []).where(field, op, value)


class _Store:
    """One collection's documents, each as (data, version)."""

    def __init__(self):
        self._docs: Dict[str, tuple] = {}

    def _snapshot(self, doc_id):
        entry = self._docs.get(doc_id)
        if entry is None:
            return FakeSnapshot(FakeDocRef(self, doc_id), None, 0)
        data, version = entry
        return FakeSnapshot(FakeDocRef(self, doc_id), dict(data), version)

    def _raw(self, doc_id):
        entry = self._docs.get(doc_id)
        return dict(entry[0]) if entry else None

    def _version(self, doc_id):
        entry = self._docs.get(doc_id)
        return entry[1] if entry else 0

    def _write(self, doc_id, data):
        version = self._version(doc_id) + 1
        self._docs[doc_id] = (dict(data), version)

    def _remove(self, doc_id):
        self._docs.pop(doc_id, None)


class FakeTransaction:
    """Optimistic-concurrency transaction: buffers writes, records read
    versions, and commits atomically iff no read doc changed."""

    def __init__(self, db, barrier: Optional[Callable[[], None]] = None):
        self._db = db
        self._reads: Dict[tuple, int] = {}
        self._writes: list = []
        self._barrier = barrier

    def get_dict(self, collection: str, doc_id: str) -> Optional[dict]:
        if self._writes:
            # The real client raises ReadAfterWriteError here (a transaction
            # must do ALL its reads before its first write); a fake that
            # tolerated it would green a reorder that 500s in production
            # (S160 Lens C).
            raise RuntimeError("read after write inside a transaction")
        store = self._db._collection_store(collection)
        snap = store._snapshot(doc_id)
        self._reads[(collection, doc_id)] = store._version(doc_id)
        return snap.to_dict()

    def set(self, collection: str, doc_id: str, data: dict) -> None:
        self._writes.append(("set", collection, doc_id, dict(data)))

    def update(self, collection: str, doc_id: str, fields: dict) -> None:
        self._writes.append(("update", collection, doc_id, dict(fields)))

    def delete(self, collection: str, doc_id: str) -> None:
        self._writes.append(("delete", collection, doc_id, None))

    def _commit(self):
        if self._barrier:
            self._barrier()  # let a peer transaction read first, in tests
        for (collection, doc_id), version in self._reads.items():
            if self._db._collection_store(collection)._version(doc_id) != version:
                raise TransactionConflict((collection, doc_id))
        for op, collection, doc_id, payload in self._writes:
            store = self._db._collection_store(collection)
            if op == "set":
                store._write(doc_id, payload)
            elif op == "update":
                current = store._raw(doc_id) or {}
                current.update(payload)
                store._write(doc_id, current)
            elif op == "delete":
                store._remove(doc_id)


class FakeFirestore:
    is_fake = True

    def __init__(self):
        self._collections: Dict[str, _Store] = {}
        # Per-instance test barrier for the NEXT transaction only.
        self._next_barrier: Optional[Callable[[], None]] = None

    def _collection_store(self, name: str) -> _Store:
        return self._collections.setdefault(name, _Store())

    def collection(self, name: str):
        return _Collection(self._collection_store(name))

    def new_transaction(self) -> FakeTransaction:
        barrier = self._next_barrier
        self._next_barrier = None
        return FakeTransaction(self, barrier)

    # Convenience for tests: read a raw stored dict.
    @property
    def data(self) -> Dict[str, Dict[str, dict]]:
        return {
            name: {doc_id: dict(entry[0]) for doc_id, entry in store._docs.items()}
            for name, store in self._collections.items()
        }
