"""Shared emergency boundary for unauthenticated legacy UUID signals.

A caller-supplied UUID is an identifier, not proof that the caller controls the
associated account.  Until OAuth subject binding replaces that legacy trust
model, runtime code must not use UUID headers or tool arguments to read,
classify, attribute, or mutate UUID-linked state.

This is deliberately a hard-coded source invariant rather than an environment
flag.  Re-enabling the behavior requires a reviewed code change with new
authentication contracts.
"""

LEGACY_UUID_INCIDENT_REFERENCE = "VM-IR-2026-09-15-LEGACY-AUTH-01"
TRUST_UNAUTHENTICATED_UUID_INPUT = False
