<#
.SYNOPSIS
Production Deployment & Automated Rollback Script for Tokenly POS (Windows Server 2022)
.DESCRIPTION
Pulls new image, deploys via docker-compose, polls /healthz, and automatically reverts
to the last known stable image if health verification fails.
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$TargetImageTag,

    [string]$HealthCheckUrl = "http://localhost:5000/healthz",
    [int]$MaxPollRetries = 20,
    [int]$PollIntervalSeconds = 3,
    [string]$StateFile = "current_stable_version.txt"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "TOKENLY POS — PRODUCTION DEPLOYMENT ENGINE" -ForegroundColor Cyan
Write-Host "Target Release Tag: $TargetImageTag" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Record / Read Previous Stable Image Tag
$PreviousStableTag = "latest"
if (Test-Path $StateFile) {
    $PreviousStableTag = (Get-Content $StateFile).Trim()
    Write-Host "[STATE] Previous validated stable tag: $PreviousStableTag" -ForegroundColor Green
} else {
    # Attempt inspecting active container
    try {
        $ActiveImage = docker inspect --format='{{.Config.Image}}' tokenly-pos-app 2>$null
        if ($ActiveImage) {
            $PreviousStableTag = $ActiveImage.Trim()
        }
    } catch {
        Write-Host "[STATE] No prior stable state file found. Defaulting fallback to 'latest'." -ForegroundColor Yellow
    }
    Set-Content -Path $StateFile -Value $PreviousStableTag
}

# Function: Execute Rollback Routine
function Invoke-AutomatedRollback {
    param([string]$Reason)
    
    Write-Host "`n==========================================================" -ForegroundColor Red
    Write-Host "[CRITICAL ALERT] POST-DEPLOYMENT VERIFICATION FAILED!" -ForegroundColor Red
    Write-Host "Reason: $Reason" -ForegroundColor Red
    Write-Host "Initiating Automated Rollback to: $PreviousStableTag" -ForegroundColor Red
    Write-Host "==========================================================" -ForegroundColor Red

    # 1. Dump failure logs for GitHub Actions artifact capture
    try {
        Write-Host "[DIAGNOSTICS] Extracting stdout/stderr logs from failing container..." -ForegroundColor Yellow
        docker logs --tail 100 tokenly-pos-app > failure_container_logs.log 2>&1
    } catch {
        Write-Host "[DIAGNOSTICS] Failed to extract container logs." -ForegroundColor Red
    }

    # 2. Revert Docker environment to previous stable tag
    $env:IMAGE_TAG = $PreviousStableTag
    Write-Host "[ROLLBACK] Relaunching previous stable container image ($PreviousStableTag)..." -ForegroundColor Yellow
    
    docker-compose -f docker-compose.prod.yml up -d --force-recreate
    
    # 3. Verify rollback target health
    Start-Sleep -Seconds 5
    try {
        $RollbackResp = Invoke-RestMethod -Uri $HealthCheckUrl -TimeoutSec 5 -ErrorAction Stop
        if ($RollbackResp.status -eq "healthy") {
            Write-Host "[ROLLBACK SUCCESS] System successfully reverted and stabilized on $PreviousStableTag!" -ForegroundColor Green
        }
    } catch {
        Write-Host "[ROLLBACK WARNING] Unable to verify health of reverted container." -ForegroundColor Red
    }

    # Exit with code 1 so GitHub Actions pipeline registers FAILURE
    exit 1
}

# Step 2: Pull New Image Tag
Write-Host "`n[PULL] Fetching target container image: $TargetImageTag..." -ForegroundColor Cyan
try {
    docker pull $TargetImageTag
} catch {
    Invoke-AutomatedRollback -Reason "Failed to pull target Docker image '$TargetImageTag' from registry."
}

# Step 3: Atomic Rolling Container Update
Write-Host "[DEPLOY] Updating runtime container environment..." -ForegroundColor Cyan
$env:IMAGE_TAG = $TargetImageTag

try {
    docker-compose -f docker-compose.prod.yml up -d --force-recreate
} catch {
    Invoke-AutomatedRollback -Reason "docker-compose up failed during container deployment."
}

# Step 4: Active Post-Deployment Health Check Polling Loop
Write-Host "`n[HEALTH CHECK] Polling $HealthCheckUrl every $PollIntervalSeconds s (Max $MaxPollRetries retries)..." -ForegroundColor Cyan

$IsHealthy = $false
for ($i = 1; $i -le $MaxPollRetries; $i++) {
    try {
        Write-Host " -> Attempt $i/$MaxPollRetries..." -NoNewline
        $Response = Invoke-RestMethod -Uri $HealthCheckUrl -TimeoutSec 4 -ErrorAction Stop
        
        if ($Response.status -eq "healthy") {
            Write-Host " HEALTHY (HTTP 200)" -ForegroundColor Green
            $IsHealthy = $true
            break
        } else {
            Write-Host " UNHEALTHY ($($Response.status))" -ForegroundColor Yellow
        }
    } catch {
        Write-Host " PENDING / ERROR ($($_.Exception.Message))" -ForegroundColor Yellow
    }
    
    Start-Sleep -Seconds $PollIntervalSeconds
}

# Step 5: Evaluate Verification Result
if (-not $IsHealthy) {
    Invoke-AutomatedRollback -Reason "Health check endpoint failed to return HTTP 200 'healthy' within $($MaxPollRetries * $PollIntervalSeconds) seconds."
}

# Step 6: Post-Deployment Success Housekeeping
Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "[SUCCESS] Target image '$TargetImageTag' verified healthy!" -ForegroundColor Green
Write-Host "Updating stable release tracking file..." -ForegroundColor Green
Set-Content -Path $StateFile -Value $TargetImageTag

# Clean up dangling images while retaining immediate previous image
try {
    docker image prune -f --filter "until=24h" | Out-Null
} catch {}

Write-Host "==========================================================" -ForegroundColor Green
exit 0
