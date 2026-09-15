"""Single source for the registration-gate activation date.

Terms and the Privacy Policy both disclose the date on which the execution
tools begin requiring a free registered UUID. One constant feeds every
carrier so the two policies (and their Bahasa Malaysia mirror) cannot drift.

RELEASE-IDENTITY EDIT POINT: the ISO date below is finalized in the release
identity commit (like SERVER_VERSION). The policy-notice test enforces that
it falls at least 14 days after the policies' published/effective date —
the Terms v2.4 advance-notice promise, machine-checked.
"""

from datetime import date

# Proposed at draft time; finalized at release identity. Must be >= the
# policy publication date + 14 days (test-enforced).
REGISTRATION_GATE_EFFECTIVE_DATE = "2026-09-30"

_MONTHS = (
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
)


def _parse(iso: str) -> date:
    return date.fromisoformat(iso)


def _human_en(iso: str) -> str:
    d = _parse(iso)
    return f"{_MONTHS[d.month - 1]} {d.day}, {d.year}"


def _human_ms(iso: str) -> str:
    # Malay month names match English for September etc. where they differ,
    # spell them out explicitly.
    ms_months = (
        "Januari", "Februari", "Mac", "April", "Mei", "Jun", "Julai",
        "Ogos", "September", "Oktober", "November", "Disember",
    )
    d = _parse(iso)
    return f"{d.day} {ms_months[d.month - 1]} {d.year}"


REGISTRATION_GATE_EFFECTIVE_HUMAN_EN = _human_en(REGISTRATION_GATE_EFFECTIVE_DATE)
REGISTRATION_GATE_EFFECTIVE_HUMAN_MS = _human_ms(REGISTRATION_GATE_EFFECTIVE_DATE)
