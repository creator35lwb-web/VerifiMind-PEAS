"""Unit-suite fixtures (v0.5.60).

The Trinity completion retry and shared-provider stagger sleep REAL seconds in
production (provider-stated waits up to 15.5s; 2s stagger on every
same-provider run). Left unpatched, every mocked Trinity test would pay those
sleeps and the suite would slow by minutes. This autouse fixture makes them
instant through the explicit `trinity_retry._sleep` seam; tests that need to
OBSERVE the sleep values (test_v0560_trinity_completion) override the same
seam with a recorder, which wins because test-requested fixtures apply after
autouse ones.
"""

import pytest

from verifimind_mcp.utils import trinity_retry


@pytest.fixture(autouse=True)
def _instant_trinity_sleeps(monkeypatch):
    async def _instant(_seconds):
        return None

    monkeypatch.setattr(trinity_retry, "_sleep", _instant)
