@echo off
REM ============================================================================
REM VerifiMind-PEAS Cloud Run Deployment Script (Windows)
REM v0.3.1 - With EDoS Protection Settings
REM ============================================================================

setlocal enabledelayedexpansion

REM Configuration
set SERVICE_NAME=verifimind-mcp
set REGION=asia-southeast1
for /f "tokens=*" %%i in ('gcloud config get-value project 2^>nul') do set PROJECT_ID=%%i

REM CRITICAL: Protection settings
set MAX_INSTANCES=3
set MIN_INSTANCES=0
set CONCURRENCY=10
set TIMEOUT=60
set MEMORY=512Mi
set CPU=1

REM Rate limiting
set RATE_LIMIT_PER_IP=10
set RATE_LIMIT_GLOBAL=100

echo ============================================================================
echo VerifiMind-PEAS Cloud Run Deployment
echo ============================================================================
echo Project:       %PROJECT_ID%
echo Service:       %SERVICE_NAME%
echo Region:        %REGION%
echo Max Instances: %MAX_INSTANCES% (HARD CAP - EDoS Protection)
echo Memory:        %MEMORY%
echo CPU:           %CPU%
echo ============================================================================

set /p confirm="Deploy with these settings? (y/N): "
if /i not "%confirm%"=="y" (
    echo Deployment cancelled.
    exit /b 0
)

echo.
echo Step 1: Building container image...
cd /d "%~dp0"

gcloud builds submit --tag "gcr.io/%PROJECT_ID%/%SERVICE_NAME%:v0.3.1" --timeout=600s

echo.
echo Step 2: Deploying to Cloud Run with EDoS protection...

gcloud run deploy %SERVICE_NAME% ^
    --image "gcr.io/%PROJECT_ID%/%SERVICE_NAME%:v0.3.1" ^
    --region %REGION% ^
    --platform managed ^
    --allow-unauthenticated ^
    --max-instances %MAX_INSTANCES% ^
    --min-instances %MIN_INSTANCES% ^
    --concurrency %CONCURRENCY% ^
    --timeout %TIMEOUT%s ^
    --memory %MEMORY% ^
    --cpu %CPU% ^
    --set-env-vars "RATE_LIMIT_PER_IP=%RATE_LIMIT_PER_IP%,RATE_LIMIT_GLOBAL=%RATE_LIMIT_GLOBAL%,LLM_PROVIDER=gemini" ^
    --port 8080

echo.
echo Step 3: Getting service URL...
for /f "tokens=*" %%i in ('gcloud run services describe %SERVICE_NAME% --region %REGION% --format="value(status.url)"') do set SERVICE_URL=%%i

echo.
echo ============================================================================
echo DEPLOYMENT COMPLETE!
echo ============================================================================
echo Service URL:    %SERVICE_URL%
echo Health Check:   %SERVICE_URL%/health
echo MCP Endpoint:   %SERVICE_URL%/mcp/
echo ============================================================================
echo.
echo To test: curl %SERVICE_URL%/health
echo.

endlocal
