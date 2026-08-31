"""OAuth 2.1 authorization spine for MCP registration-auth (Design v2).

Narrow, spec-exact, stdlib-crypto core: authorization-code + PKCE (S256
only), opaque store-validated tokens (access / refresh / personal access
token), refresh rotation with reuse-detection revocation, RFC 7009 revoke,
RFC 8414 AS metadata, RFC 9728 protected-resource metadata, and bounded
RFC 7591 dynamic client registration. Public clients only (PKCE mandatory,
token_endpoint_auth_method "none"). No JWT/JOSE: the authorization server
and the protected resource are the same origin, so tokens are validated by
store lookup with constant-time verifier comparison — every credential is
individually revocable and only hashes exist at rest.

Design record: private Hub brief 20260831_RNA_registration_auth_design_v2_oauth.md
(T S152 HOLD P0s 1-8 + T S153 OAuth addendum, D-152-*, D-153-*).
"""
