# IAM Policy Classifier - Infrastructure Manager
# Usage:
#   .\infra\manage.ps1 up    # scale up before an interview / demo
#   .\infra\manage.ps1 down  # scale down after to save costs

param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("up","down")]
    [string]$Command
)

$CLUSTER   = "iam-classifier-cluster"
$SERVICE   = "iam-classifier-service"
$APP_URL   = "http://iam-classifier-alb-330518746.us-east-1.elb.amazonaws.com"
$REGION    = "us-east-1"

# ── helpers ────────────────────────────────────────────────────────────────────

function Write-Step([string]$msg) {
    Write-Host "`n==> $msg" -ForegroundColor Cyan
}

function Write-OK([string]$msg) {
    Write-Host "    [OK] $msg" -ForegroundColor Green
}

function Write-Err([string]$msg) {
    Write-Host "    [ERROR] $msg" -ForegroundColor Red
}

function Assert-AWSCLI {
    Write-Step "Checking prerequisites"
    if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
        Write-Err "AWS CLI not found. Install it from: https://aws.amazon.com/cli/"
        exit 1
    }
    Write-OK "AWS CLI found"

    # Quick connectivity check
    $result = aws sts get-caller-identity --no-cli-pager 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Err "AWS credentials not configured or expired."
        Write-Host "    Run: aws configure" -ForegroundColor Yellow
        exit 1
    }
    Write-OK "AWS credentials valid"
}

# ── up ─────────────────────────────────────────────────────────────────────────

function Invoke-Up {
    Assert-AWSCLI

    Write-Step "Scaling ECS service up to 1 task"
    aws ecs update-service `
        --cluster $CLUSTER `
        --service $SERVICE `
        --desired-count 1 `
        --no-cli-pager | Out-Null

    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to update ECS service."
        exit 1
    }
    Write-OK "Desired count set to 1"

    Write-Step "Waiting for service to reach steady state (timeout: 5 min)"
    $timeout   = 300   # seconds
    $interval  = 15
    $elapsed   = 0
    $stable    = $false

    while ($elapsed -lt $timeout) {
        Start-Sleep -Seconds $interval
        $elapsed += $interval

        $running = aws ecs describe-services `
            --cluster $CLUSTER `
            --services $SERVICE `
            --no-cli-pager `
            --query "services[0].runningCount" `
            --output text 2>&1

        $deployments = aws ecs describe-services `
            --cluster $CLUSTER `
            --services $SERVICE `
            --no-cli-pager `
            --query "length(services[0].deployments)" `
            --output text 2>&1

        Write-Host "    [$elapsed`s] Running tasks: $running  |  Active deployments: $deployments"

        if ($running -eq "1" -and $deployments -eq "1") {
            $stable = $true
            break
        }
    }

    if (-not $stable) {
        Write-Err "Service did not stabilize within 5 minutes."
        Write-Host "    Check ECS console for details:" -ForegroundColor Yellow
        Write-Host "    https://console.aws.amazon.com/ecs/v2/clusters/$CLUSTER/services/$SERVICE" -ForegroundColor Yellow
        exit 1
    }

    Write-OK "Service is stable"

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  App is live! Open the URL below:" -ForegroundColor Green
    Write-Host "  $APP_URL" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
}

# ── down ───────────────────────────────────────────────────────────────────────

function Invoke-Down {
    Assert-AWSCLI

    Write-Step "Scaling ECS service down to 0 tasks"
    aws ecs update-service `
        --cluster $CLUSTER `
        --service $SERVICE `
        --desired-count 0 `
        --no-cli-pager | Out-Null

    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to update ECS service."
        exit 1
    }
    Write-OK "Desired count set to 0"

    Write-Step "Confirming tasks are stopping"
    Start-Sleep -Seconds 5

    $running = aws ecs describe-services `
        --cluster $CLUSTER `
        --services $SERVICE `
        --no-cli-pager `
        --query "services[0].runningCount" `
        --output text 2>&1

    Write-OK "Running task count: $running (draining to 0)"

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  Resources scaled down." -ForegroundColor Yellow
    Write-Host "  Saving ~`$1-3/day while idle." -ForegroundColor Yellow
    Write-Host "  Run '.\infra\manage.ps1 up' to restore." -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
}

# ── dispatch ───────────────────────────────────────────────────────────────────

switch ($Command) {
    "up"   { Invoke-Up }
    "down" { Invoke-Down }
}
