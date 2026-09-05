"""T S156 gate-truth contract: ``_denial_payload`` is ONE exhaustive decision.

The GitHub Advanced Security ``CodeQL`` check at PR #346 head ``7a0c462``
reported ``py/uninitialized-local-variable`` for ``error`` and ``hint``
(registration_gate.py:206-207): the two denial branches were written as two
independent ``if`` statements whose conditions are logical complements —
exhaustive to a reader, but not provably so to static analysis. The repair
expresses the decision as one ``if``/``else`` without changing either payload.

Pinned here, mapped to the T S156 contract (steps 2-3):

* both admitted reasons — and any unknown reason, which resolves to the
  authentication-required payload exactly as before — always bind ``error``
  and ``recovery_hint``;
* the exact payload strings are unchanged;
* both payloads are environment-bound (CS Finding 4, extended to the
  cross-subject payload);
* the REAL ``_env_urls`` exception path (staging with no resolvable origin)
  never advertises a production PRM — the dead module constant ``PRM_URL``
  must never re-enter the fallback (class sweep of CS Finding 4);
* structurally, exactly ONE ``if`` binds ``error``/``hint``, the if/elif
  chain ends in a real ``else``, and EVERY arm DEFINITELY binds BOTH names
  (a binding under a nested non-exhaustive ``if`` does not count). This is the
  discriminating regression: it FAILS on ``7a0c462`` (two ``if`` statements,
  no ``else``) and PASSES on the repaired head;
* CPython's own definite-assignment analysis agrees: ``error``/``hint`` are
  loaded with ``LOAD_FAST`` (proven bound), not ``LOAD_FAST_CHECK`` — which is
  how ``7a0c462`` compiled them.
"""

import ast
import dis
import inspect
import sys
import textwrap

import pytest

from verifimind_mcp.middleware import registration_gate as rg
from verifimind_mcp.middleware.registration_gate import (
    DENIAL_AUTHENTICATION_REQUIRED,
    DENIAL_CROSS_SUBJECT,
    _denial_payload,
)

TOOL = "run_full_trinity"
PROD_ORIGIN = "https://verifimind.ysenseai.org"
STAGE_ORIGIN = "https://staging.example"
PRM_PATH = "/.well-known/oauth-protected-resource"
BOTH_REASONS = [DENIAL_CROSS_SUBJECT, DENIAL_AUTHENTICATION_REQUIRED]


def _env(monkeypatch, name, origin):
    monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", name)
    monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", origin)


def _without_timestamp(payload):
    payload = dict(payload)
    payload.pop("timestamp")
    return payload


# ── Exact payload contract: neither payload changed ─────────────────────────

class TestPayloadsUnchanged:
    def test_cross_subject_payload_exact(self, monkeypatch):
        _env(monkeypatch, "production", PROD_ORIGIN)
        p = _denial_payload(TOOL, DENIAL_CROSS_SUBJECT)
        assert p["status"] == "error"
        assert p["error_code"] == "CROSS_SUBJECT_MISMATCH"
        assert p["error"] == (
            f"'{TOOL}' was called with a user_uuid that does not match "
            "the authenticated account. The argument confers no authority; "
            "remove it or use your own account's value."
        )
        assert p["recovery_hint"] == (
            "Tool-argument identity is diagnostics only. Your authenticated "
            "session already attributes this call; omit user_uuid entirely."
        )
        assert p["register_url"] == f"{PROD_ORIGIN}/register"
        assert p["resource_metadata"] == f"{PROD_ORIGIN}{PRM_PATH}"
        assert p["retryable"] is False

    def test_authentication_required_payload_exact(self, monkeypatch):
        _env(monkeypatch, "production", PROD_ORIGIN)
        prm = f"{PROD_ORIGIN}{PRM_PATH}"
        p = _denial_payload(TOOL, DENIAL_AUTHENTICATION_REQUIRED)
        assert p["status"] == "error"
        assert p["error_code"] == "AUTHENTICATION_REQUIRED"
        assert p["error"] == (
            f"'{TOOL}' requires an authenticated session. Discovery, "
            "template reads, and all pages remain available without one."
        )
        assert p["recovery_hint"] == (
            f"Connect through an OAuth-capable MCP client (authorization "
            f"server in {prm}), or register free at {PROD_ORIGIN}/register "
            "and use a personal access token for local clients. All gated "
            "tools remain free after registration."
        )
        assert p["register_url"] == f"{PROD_ORIGIN}/register"
        assert p["resource_metadata"] == prm
        assert p["retryable"] is False

    def test_authentication_required_without_prm_degrades_clause(
        self, monkeypatch
    ):
        # Pins the no-PRM STRING branch of the hint only: ``_env_urls`` is
        # replaced wholesale here, so its ``except`` clause is NOT exercised —
        # the real fallback path is pinned by
        # test_misconfigured_staging_never_advertises_a_production_prm.
        # Unchanged from the prior form.
        monkeypatch.setattr(rg, "_env_urls", lambda: (rg.REGISTER_URL, None))
        p = _denial_payload(TOOL, DENIAL_AUTHENTICATION_REQUIRED)
        assert p["recovery_hint"].startswith(
            "Connect through an OAuth-capable MCP client, or register free at "
            f"{rg.REGISTER_URL} and use a personal access token"
        )
        assert "resource_metadata" not in p
        assert p["register_url"] == rg.REGISTER_URL


# ── Every admitted path binds error and hint (the CodeQL error class) ───────

class TestEveryPathBindsErrorAndHint:
    @pytest.mark.parametrize(
        "reason", BOTH_REASONS + ["some_future_reason"]
    )
    def test_error_and_hint_are_always_bound(self, monkeypatch, reason):
        _env(monkeypatch, "production", PROD_ORIGIN)
        p = _denial_payload(TOOL, reason)
        assert isinstance(p["error"], str) and p["error"]
        assert isinstance(p["recovery_hint"], str) and p["recovery_hint"]
        assert p["error_code"] == (
            "CROSS_SUBJECT_MISMATCH"
            if reason == DENIAL_CROSS_SUBJECT
            else "AUTHENTICATION_REQUIRED"
        )

    def test_unknown_reason_is_authentication_required_unchanged(
        self, monkeypatch
    ):
        # The prior form's ``reason != DENIAL_CROSS_SUBJECT`` branch admitted
        # any other value; the ``else`` preserves that resolution exactly.
        _env(monkeypatch, "production", PROD_ORIGIN)
        assert _without_timestamp(_denial_payload(TOOL, "unknown")) == (
            _without_timestamp(
                _denial_payload(TOOL, DENIAL_AUTHENTICATION_REQUIRED)
            )
        )


# ── Environment binding holds for BOTH payloads (CS Finding 4, extended) ────

class TestBothPayloadsEnvironmentBound:
    @pytest.mark.parametrize("reason", BOTH_REASONS)
    def test_staging_never_points_at_production(self, monkeypatch, reason):
        _env(monkeypatch, "staging", STAGE_ORIGIN)
        p = _denial_payload(TOOL, reason)
        assert "verifimind.ysenseai.org" not in str(p)
        assert p["register_url"] == f"{STAGE_ORIGIN}/register"
        assert p["resource_metadata"] == f"{STAGE_ORIGIN}{PRM_PATH}"

    @pytest.mark.parametrize("reason", BOTH_REASONS)
    def test_production_points_at_production(self, monkeypatch, reason):
        _env(monkeypatch, "production", PROD_ORIGIN)
        p = _denial_payload(TOOL, reason)
        assert p["register_url"] == f"{PROD_ORIGIN}/register"
        assert p["resource_metadata"] == f"{PROD_ORIGIN}{PRM_PATH}"

    @pytest.mark.parametrize("reason", BOTH_REASONS)
    def test_misconfigured_staging_never_advertises_a_production_prm(
        self, monkeypatch, reason
    ):
        # The REAL ``_env_urls`` path, not a monkeypatch: a staging service
        # that cannot resolve its own origin must not fall back to the
        # production authorization server (CS Finding 4 / T P0-8). The dead
        # module constant ``PRM_URL`` stays dead; the documented fallback is
        # ``(REGISTER_URL, None)``.
        monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "staging")
        monkeypatch.delenv("VERIFIMIND_PUBLIC_ORIGIN", raising=False)
        monkeypatch.delenv("K_SERVICE", raising=False)
        p = _denial_payload(TOOL, reason)
        assert "resource_metadata" not in p
        assert PRM_PATH not in str(p)
        assert p["register_url"] == rg.REGISTER_URL


# ── Structural pin: exactly one exhaustive decision binds error/hint ────────
# Discriminating: FAILS on 7a0c462 (two independent ``if``s, neither with
# an ``else``) and PASSES on the repaired head.

def _target_names(target):
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return set().union(*(_target_names(element) for element in target.elts))
    return set()


def _names_assigned(statements):
    """Names assigned ANYWHERE under ``statements`` (walks nested nodes).

    Used only to FIND the decision and to detect bindings outside it;
    ``_definitely_assigned`` below is what PROVES the decision.
    """
    names = set()
    for statement in statements:
        for node in ast.walk(statement):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    names |= _target_names(target)
            elif isinstance(node, ast.AnnAssign):
                names |= _target_names(node.target)
    return names


def _denial_payload_function():
    source = textwrap.dedent(inspect.getsource(_denial_payload))
    function = ast.parse(source).body[0]
    assert isinstance(function, ast.FunctionDef)
    return function


def _arms(decision):
    """Every arm of an if/elif/else chain.

    Returns ``(bodies, terminal_else)``: each ``If`` body along the chain,
    and the terminal ``else`` body — ``None`` when the chain has no real
    ``else`` (an ``if``/``elif`` chain without one still has a fall-through
    path, which is exactly the shape static analysis rejects).
    """
    bodies, node = [], decision
    while True:
        bodies.append(node.body)
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            node = node.orelse[0]  # elif: keep walking the chain
            continue
        return bodies, (node.orelse or None)


def _definitely_assigned(statements):
    """Names bound on EVERY control path through ``statements``.

    Definite-assignment semantics — the property static analysis actually
    checks: a plain, annotated, or tuple assignment binds; a nested
    if/elif/else binds a name only when it has a real terminal ``else`` and
    every arm binds it; ``with`` bodies are followed; a ``try`` binds what its
    body-plus-else and every handler all bind, plus its ``finally``. Anything
    else binds nothing. (``_names_assigned`` above deliberately walks nested
    nodes — it is used only to FIND the decision, never to prove it.)
    """
    names = set()
    for statement in statements:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                names |= _target_names(target)
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            names |= _target_names(statement.target)
        elif isinstance(statement, ast.If):
            bodies, terminal_else = _arms(statement)
            if terminal_else is not None:
                names |= set.intersection(
                    *(_definitely_assigned(arm) for arm in bodies + [terminal_else])
                )
        elif isinstance(statement, ast.With):
            names |= _definitely_assigned(statement.body)
        elif isinstance(statement, ast.Try):
            paths = [_definitely_assigned(statement.body + statement.orelse)]
            paths += [_definitely_assigned(h.body) for h in statement.handlers]
            names |= set.intersection(*paths)
            names |= _definitely_assigned(statement.finalbody)
    return names


class TestOneExhaustiveDecision:
    def test_error_and_hint_are_bound_by_exactly_one_if_else(self):
        function = _denial_payload_function()
        binding = [
            node for node in function.body
            if isinstance(node, ast.If)
            and {"error", "hint"} & (
                _names_assigned(node.body) | _names_assigned(node.orelse)
            )
        ]
        assert len(binding) == 1, (
            f"{len(binding)} top-level `if` statements bind error/hint; "
            "static analysis needs exactly ONE exhaustive if/else"
        )
        bodies, terminal_else = _arms(binding[0])
        assert terminal_else is not None, (
            "the decision has no terminal `else`: an if/elif chain without "
            "one leaves a fall-through path with error/hint unbound"
        )
        for arm in bodies + [terminal_else]:
            assert {"error", "hint"} <= _definitely_assigned(arm), (
                "an arm of the decision does not DEFINITELY bind both error "
                "and hint (a binding under a nested non-exhaustive `if` does "
                "not count)"
            )

    @pytest.mark.skipif(
        sys.version_info < (3, 12),
        reason="LOAD_FAST_CHECK (CPython's definite-assignment oracle) "
               "exists from 3.12; production runs 3.12",
    )
    def test_compiler_proves_error_and_hint_bound(self):
        # CPython loads a local it cannot prove bound with LOAD_FAST_CHECK
        # and a proven-bound local with LOAD_FAST. 7a0c462 compiled error and
        # hint with LOAD_FAST_CHECK; the exhaustive decision compiles them
        # with LOAD_FAST — an oracle independent of both CodeQL and our AST.
        unproven = {
            instruction.argval
            for instruction in dis.get_instructions(_denial_payload)
            if instruction.opname == "LOAD_FAST_CHECK"
        }
        assert not ({"error", "hint"} & unproven), unproven

    def test_error_and_hint_are_not_bound_outside_the_decision(self):
        function = _denial_payload_function()
        outside = [n for n in function.body if not isinstance(n, ast.If)]
        assert not ({"error", "hint"} & _names_assigned(outside))
