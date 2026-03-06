#!/usr/bin/env bash
# IAM Policy Classifier - Infrastructure Manager
# Usage:
#   ./infra/manage.sh up    # scale up before an interview / demo
#   ./infra/manage.sh down  # scale down after to save costs

set -euo pipefail

CLUSTER="iam-classifier-cluster"
SERVICE="iam-classifier-service"
APP_URL="http://iam-classifier-alb-330518746.us-east-1.elb.amazonaws.com"
REGION="us-east-1"

# ── helpers ────────────────────────────────────────────────────────────────────

step()  { echo -e "\n\033[36m==> $*\033[0m"; }
ok()    { echo -e "    \033[32m[OK]\033[0m $*"; }
err()   { echo -e "    \033[31m[ERROR]\033[0m $*"; }

assert_awscli() {
    step "Checking prerequisites"
    if ! command -v aws &>/dev/null; then
        err "AWS CLI not found. Install it from: https://aws.amazon.com/cli/"
        exit 1
    fi
    ok "AWS CLI found"

    if ! aws sts get-caller-identity --no-cli-pager &>/dev/null; then
        err "AWS credentials not configured or expired."
        echo "    Run: aws configure"
        exit 1
    fi
    ok "AWS credentials valid"
}

# ── up ─────────────────────────────────────────────────────────────────────────

cmd_up() {
    assert_awscli

    step "Scaling ECS service up to 1 task"
    aws ecs update-service \
        --cluster "$CLUSTER" \
        --service "$SERVICE" \
        --desired-count 1 \
        --no-cli-pager > /dev/null
    ok "Desired count set to 1"

    step "Waiting for service to reach steady state (timeout: 5 min)"
    TIMEOUT=300
    INTERVAL=15
    ELAPSED=0
    STABLE=false

    while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
        sleep "$INTERVAL"
        ELAPSED=$((ELAPSED + INTERVAL))

        RUNNING=$(aws ecs describe-services \
            --cluster "$CLUSTER" \
            --services "$SERVICE" \
            --no-cli-pager \
            --query "services[0].runningCount" \
            --output text)

        DEPLOYMENTS=$(aws ecs describe-services \
            --cluster "$CLUSTER" \
            --services "$SERVICE" \
            --no-cli-pager \
            --query "length(services[0].deployments)" \
            --output text)

        echo "    [${ELAPSED}s] Running tasks: $RUNNING  |  Active deployments: $DEPLOYMENTS"

        if [ "$RUNNING" = "1" ] && [ "$DEPLOYMENTS" = "1" ]; then
            STABLE=true
            break
        fi
    done

    if [ "$STABLE" != "true" ]; then
        err "Service did not stabilize within 5 minutes."
        echo "    Check ECS console:"
        echo "    https://console.aws.amazon.com/ecs/v2/clusters/$CLUSTER/services/$SERVICE"
        exit 1
    fi

    ok "Service is stable"

    echo ""
    echo -e "\033[32m========================================\033[0m"
    echo -e "\033[32m  App is live! Open the URL below:\033[0m"
    echo -e "\033[33m  $APP_URL\033[0m"
    echo -e "\033[32m========================================\033[0m"
    echo ""
}

# ── down ───────────────────────────────────────────────────────────────────────

cmd_down() {
    assert_awscli

    step "Scaling ECS service down to 0 tasks"
    aws ecs update-service \
        --cluster "$CLUSTER" \
        --service "$SERVICE" \
        --desired-count 0 \
        --no-cli-pager > /dev/null
    ok "Desired count set to 0"

    step "Confirming tasks are stopping"
    sleep 5

    RUNNING=$(aws ecs describe-services \
        --cluster "$CLUSTER" \
        --services "$SERVICE" \
        --no-cli-pager \
        --query "services[0].runningCount" \
        --output text)

    ok "Running task count: $RUNNING (draining to 0)"

    echo ""
    echo -e "\033[33m========================================\033[0m"
    echo -e "\033[33m  Resources scaled down.\033[0m"
    echo -e "\033[33m  Saving ~\$1-3/day while idle.\033[0m"
    echo -e "\033[33m  Run './infra/manage.sh up' to restore.\033[0m"
    echo -e "\033[33m========================================\033[0m"
    echo ""
}

# ── dispatch ───────────────────────────────────────────────────────────────────

case "${1:-}" in
    up)   cmd_up ;;
    down) cmd_down ;;
    *)
        echo "Usage: $0 [up|down]"
        echo "  up   - Scale ECS service to 1 task, wait for steady state"
        echo "  down - Scale ECS service to 0 tasks to save costs"
        exit 1
        ;;
esac
