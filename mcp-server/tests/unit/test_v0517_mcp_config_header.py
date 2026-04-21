"""
Tests for v0.5.17 — mcp_config UUID header fix (T Phase 84 hybrid D1)

Coverage:
  - mcp_config args include --header flag with X-VerifiMind-UUID:${VERIFIMIND_UUID}
  - VERIFIMIND_UUID env var still present (backward compat)
  - Header value uses ${VERIFIMIND_UUID} expansion pattern (not hardcoded uuid)
  - Server version assertion
"""

import inspect

import verifimind_mcp.server as _srv_module

_SERVER_SOURCE = inspect.getsource(_srv_module)


class TestMcpConfigHeader:

    def _extras(self, uuid: str = "019d40d6-9e84-7738-9c0c-fa85b2930600"):
        from verifimind_mcp.registration import _build_registration_extras
        return _build_registration_extras(uuid, "https://polar.sh/checkout/x")

    def test_args_include_header_flag(self):
        args = self._extras()["mcp_config"]["mcpServers"]["verifimind"]["args"]
        assert "--header" in args

    def test_header_value_is_x_verifimind_uuid(self):
        args = self._extras()["mcp_config"]["mcpServers"]["verifimind"]["args"]
        idx = args.index("--header")
        header_value = args[idx + 1]
        assert header_value.startswith("X-VerifiMind-UUID:")

    def test_header_uses_env_var_expansion_not_hardcoded_uuid(self):
        args = self._extras()["mcp_config"]["mcpServers"]["verifimind"]["args"]
        idx = args.index("--header")
        header_value = args[idx + 1]
        assert "${VERIFIMIND_UUID}" in header_value
        assert "019d40d6" not in header_value

    def test_env_var_still_present(self):
        server = self._extras()["mcp_config"]["mcpServers"]["verifimind"]
        assert server["env"]["VERIFIMIND_UUID"] == "019d40d6-9e84-7738-9c0c-fa85b2930600"

    def test_mcp_remote_still_in_args(self):
        args = self._extras()["mcp_config"]["mcpServers"]["verifimind"]["args"]
        assert "mcp-remote" in args

    def test_server_url_still_in_args(self):
        args = self._extras()["mcp_config"]["mcpServers"]["verifimind"]["args"]
        assert any("verifimind.ysenseai.org" in a for a in args)

    def test_different_uuids_produce_same_header_template(self):
        uuid_a = "019d40d6-9e84-7738-9c0c-fa85b2930600"
        uuid_b = "019e1234-abcd-7000-beef-000000000001"
        args_a = _build_args(uuid_a)
        args_b = _build_args(uuid_b)
        # The --header arg should be identical regardless of uuid (uses env var)
        header_a = args_a[args_a.index("--header") + 1]
        header_b = args_b[args_b.index("--header") + 1]
        assert header_a == header_b == "X-VerifiMind-UUID:${VERIFIMIND_UUID}"


def _build_args(uuid: str) -> list:
    from verifimind_mcp.registration import _build_registration_extras
    extras = _build_registration_extras(uuid, "https://polar.sh/checkout/x")
    return extras["mcp_config"]["mcpServers"]["verifimind"]["args"]


class TestServerVersion:

    def test_server_version_is_0517(self):
        from verifimind_mcp.server import SERVER_VERSION
        assert SERVER_VERSION == "0.5.17", f"Expected 0.5.17, got {SERVER_VERSION}"
