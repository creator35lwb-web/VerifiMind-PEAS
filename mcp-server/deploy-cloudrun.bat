@echo off
REM ============================================================================
REM HARD-RETIRED (T S97 round-7 residual, 2026-07-26) - DO NOT USE
REM ============================================================================
REM This v0.3.1-era Windows script targeted the LEGACY service "verifimind-mcp"
REM (asia-southeast1), which is not the production service, and it carried no
REM build-identity attestation. Every live deployment goes through:
REM   - the Cloud Build trigger (root cloudbuild.yaml), or
REM   - ./deploy-cloudrun.sh (exact-committed-bytes archive + guards)
REM RETIREMENT-STUB-MARKER: deploy-path-retired
REM ============================================================================
echo ERROR: deploy-cloudrun.bat is HARD-RETIRED. Use ./deploy-cloudrun.sh instead. 1>&2
exit /b 1
