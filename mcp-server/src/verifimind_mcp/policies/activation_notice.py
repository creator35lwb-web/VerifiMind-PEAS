"""Single source for the registration-gate activation date.

Terms and the Privacy Policy both disclose when the four execution tools begin
requiring a free registered account. One constant feeds every carrier, so the
two policies (and the Privacy Policy's Bahasa Malaysia mirror) cannot drift.

Two states, both rendered from this module:

* ``REGISTRATION_GATE_EFFECTIVE_DATE = None`` — no activation date is
  announced. Every carrier renders the standing promise: the requirement takes
  effect on a date announced on the policy pages at least ``NOTICE_DAYS`` days
  in advance, and not before.
* an ISO date — announced. Every carrier renders that date.

RELEASE-IDENTITY EDIT POINT: the activation release's identity commit sets the
ISO date here (like SERVER_VERSION), together with the policy revision that
announces it. The policy-notice tests enforce that an announced date falls at
least ``NOTICE_DAYS`` days after that revision's published/effective date and
that every carrier renders the current state.
"""

from datetime import date, timedelta

# The advance notice both policies promise before a material adverse change
# takes effect; the registration requirement is announced under the same term.
NOTICE_DAYS = 14

# None = to be announced. v0.5.63 (Privacy v2.6, Terms v2.5) announced
# 2026-10-20; v0.5.65 (Privacy v2.7, Terms v2.6) replaced that fixed date with
# the standing promise below, because the lane that enforces the requirement
# had no proof-complete date to announce.
REGISTRATION_GATE_EFFECTIVE_DATE: str | None = None

_MONTHS = (
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
)
# Malay month names coincide with English only where they do (April,
# September, November); the rest are spelled out explicitly.
_MONTHS_MS = (
    "Januari", "Februari", "Mac", "April", "Mei", "Jun", "Julai",
    "Ogos", "September", "Oktober", "November", "Disember",
)

TO_BE_ANNOUNCED_EN = (
    "a date that will be announced on this page "
    f"at least {NOTICE_DAYS} days in advance"
)
TO_BE_ANNOUNCED_MS = (
    "tarikh yang akan diumumkan di halaman ini "
    f"sekurang-kurangnya {NOTICE_DAYS} hari lebih awal"
)


def _parse(iso: str) -> date:
    return date.fromisoformat(iso)


def _human_en(iso: str) -> str:
    d = _parse(iso)
    return f"{_MONTHS[d.month - 1]} {d.day}, {d.year}"


def _human_ms(iso: str) -> str:
    d = _parse(iso)
    return f"{d.day} {_MONTHS_MS[d.month - 1]} {d.year}"


def gate_when_en(iso: str | None) -> str:
    """The English ``from ...`` phrase every carrier uses for the gate's start."""
    return f"from {_human_en(iso)}" if iso else f"from {TO_BE_ANNOUNCED_EN}"


def gate_when_ms(iso: str | None) -> str:
    """The Bahasa Malaysia ``mulai ...`` phrase for the same carriers."""
    return f"mulai {_human_ms(iso)}" if iso else f"mulai {TO_BE_ANNOUNCED_MS}"


def sentence_case(phrase: str) -> str:
    """Capitalise a phrase that opens a sentence (``from`` -> ``From``)."""
    return phrase[:1].upper() + phrase[1:]


def notice_period_honored(iso: str | None, *published: str) -> bool:
    """Whether an announced date keeps the ``NOTICE_DAYS`` promise.

    ``None`` (nothing announced) honours it trivially. An announced date must
    fall at least ``NOTICE_DAYS`` days after EVERY published/effective date of
    the policies that announce it. A call without any published date is a
    programming error, never a vacuous pass.
    """
    if not published:
        raise ValueError("notice_period_honored needs at least one published date")
    if iso is None:
        return True
    gate_day = _parse(iso)
    return all(
        gate_day >= _parse(day) + timedelta(days=NOTICE_DAYS) for day in published
    )


REGISTRATION_GATE_WHEN_EN = gate_when_en(REGISTRATION_GATE_EFFECTIVE_DATE)
REGISTRATION_GATE_WHEN_MS = gate_when_ms(REGISTRATION_GATE_EFFECTIVE_DATE)
