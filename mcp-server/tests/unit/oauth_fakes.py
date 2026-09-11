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

A commit is ALL-OR-NOTHING: every write's gate is checked before any write is
applied (T S165), as one Commit RPC would. What the fake still cannot model
is server-side serializability under real concurrency (T S161 F-9): runtime
race authority belongs to the emulator or isolated Firestore.
"""

from typing import Any, Callable, Dict, Optional

# The real client raises AlreadyExists from DocumentReference.create() on an
# existing document and NotFound from update() on a missing one; the fake
# raises the same classes so registration's atomic email claim — and the
# backend-failure boundary around it — behave identically (T S158 / S162).
from google.api_core.exceptions import AlreadyExists, NotFound

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

    @property
    def id(self):
        return self.reference._id

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

    def create(self, data):
        """Create-if-absent, like the real client: exactly one creator wins.
        The write gate runs BEFORE the existence check, as the real commit
        does: when writes are down, create() fails with the backend error
        whether or not the document exists (S162, fake fidelity). It runs
        EXACTLY ONCE — the real client sends one commit RPC per logical write,
        so a one-shot fault injection must fire once here too (T S159 R6-05)."""
        self._store._write_gate()
        if self._store._raw(self._id) is not None:
            raise AlreadyExists(f"document {self._id} already exists")
        self._store._apply_write(self._id, dict(data))

    def update(self, fields):
        self._store._write_gate()
        current = self._store._raw(self._id)
        if current is None:
            # The real client raises NotFound (a backend-failure class), never
            # KeyError — a boundary that keys on is_backend_failure must see
            # the same shape here (S162, Lens A).
            raise NotFound(f"document {self._id} does not exist")
        merged = dict(current)
        merged.update(fields)
        self._store._apply_write(self._id, merged)

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
        # Per-document version that SURVIVES a delete (S168 Lens B): the real
        # server's optimistic check compares update times, so a document
        # deleted and re-created after a transaction read it conflicts that
        # transaction's commit. A counter kept in the document tuple reset to
        # zero on delete and let a delete-then-recreate slip past a read.
        self._versions: Dict[str, int] = {}

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
        return self._versions.get(doc_id, 0)

    def _write_gate(self):
        """Every logical write passes here EXACTLY ONCE. Tests model a
        writes-down outage by replacing it with a raiser, so create/set/update/
        delete — inside and outside transactions — fail exactly as the real
        commit RPC would, and a one-shot injection fires once per write
        (T S159 R6-05)."""
        return None

    def _apply_write(self, doc_id, data):
        """Ungated store mutation, for callers that already passed the gate."""
        version = self._version(doc_id) + 1
        self._versions[doc_id] = version
        self._docs[doc_id] = (dict(data), version)

    def _apply_remove(self, doc_id):
        if doc_id in self._docs:
            self._versions[doc_id] = self._version(doc_id) + 1   # a delete is a change a reader must see
        self._docs.pop(doc_id, None)

    def _write(self, doc_id, data):
        self._write_gate()
        self._apply_write(doc_id, data)

    def _remove(self, doc_id):
        self._write_gate()
        self._apply_remove(doc_id)


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

    def where_ids(self, collection: str, field: str, value) -> list:
        """A query evaluated THROUGH the transaction, like the real client's
        ``Query.get(transaction=...)``: every matched document joins the read
        set (a change to one of them before commit conflicts this
        transaction). A document created after the read is NOT detected here
        — the real server has no predicate locks either; closure against such
        a writer comes from this transaction's read set including every key
        that writer can touch (the caller's seed, read one by one), and from
        that writer reading a document this transaction writes (T S167
        R9-02)."""
        if self._writes:
            raise RuntimeError("read after write inside a transaction")
        store = self._db._collection_store(collection)
        ids = []
        for doc_id, (data, _v) in list(store._docs.items()):
            if data.get(field) == value:
                self._reads[(collection, doc_id)] = store._version(doc_id)
                ids.append(doc_id)
        return ids

    def _commit(self):
        if self._barrier:
            self._barrier()  # let a peer transaction read first, in tests
        for (collection, doc_id), version in self._reads.items():
            if self._db._collection_store(collection)._version(doc_id) != version:
                raise TransactionConflict((collection, doc_id))
        # Phase 1 — every buffered write passes its store's commit gate BEFORE
        # anything is applied. The real client sends a transaction's writes in
        # ONE Commit RPC, so a transaction never half-lands; a fake that applied
        # writes one by one let a later gate failure leave earlier writes
        # persisted (T S165 / CS round 7 F-9). One gate call per logical write,
        # as before (T S159 R6-05).
        for op, collection, doc_id, payload in self._writes:
            self._db._collection_store(collection)._write_gate()
        # Phase 2 — apply, ungated.
        for op, collection, doc_id, payload in self._writes:
            store = self._db._collection_store(collection)
            if op == "set":
                store._apply_write(doc_id, payload)
            elif op == "update":
                current = store._raw(doc_id) or {}
                current.update(payload)
                store._apply_write(doc_id, current)
            elif op == "delete":
                store._apply_remove(doc_id)


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
