#!/usr/bin/env bash

set -u

PORT="${PORT:-18000}"
WEBHOOK_SECRET="${WEBHOOK_SECRET:-test_secret}"
BOT_USERNAME="${BOT_USERNAME:-test_bot}"
BASE_URL="http://127.0.0.1:${PORT}"

PASS_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf '[PASS] %s\n' "$1"
}

fail() {
  printf '[FAIL] %s\n' "$1"
  exit 1
}

cleanup() {
  if [ -n "${SERVER_PID:-}" ] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
  rm -f /tmp/test_webhook_response_bad.json /tmp/test_webhook_response_good.json
}

trap cleanup EXIT

WEBHOOK_SECRET="${WEBHOOK_SECRET}" BOT_USERNAME="${BOT_USERNAME}" uv run uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" >/tmp/test_webhook_server.log 2>&1 &
SERVER_PID=$!

READY=0
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if curl -s "${BASE_URL}/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 0.5
done

if [ "${READY}" -ne 1 ]; then
  fail "server failed to start"
fi
pass "server started"

BAD_PAYLOAD='{"action":"opened","pull_request":{"number":1},"sender":{"login":"real_user"}}'
BAD_CODE=$(curl -s -o /tmp/test_webhook_response_bad.json -w '%{http_code}' -X POST "${BASE_URL}/webhook" \
  -H 'X-Hub-Signature-256: sha256=invalid' \
  -H 'X-GitHub-Event: pull_request' \
  -H 'Content-Type: application/json' \
  -d "${BAD_PAYLOAD}")

if [ "${BAD_CODE}" != "403" ]; then
  fail "invalid signature should return 403 (got ${BAD_CODE})"
fi
pass "invalid signature rejected"

GOOD_PAYLOAD=$(printf '{"action":"opened","pull_request":{"number":2},"sender":{"login":"%s"}}' "${BOT_USERNAME}")
GOOD_SIG=$(PAYLOAD="${GOOD_PAYLOAD}" WEBHOOK_SECRET="${WEBHOOK_SECRET}" uv run python -c 'import hashlib,hmac,os; payload=os.environ["PAYLOAD"].encode(); secret=os.environ["WEBHOOK_SECRET"].encode(); print(hmac.new(secret, payload, hashlib.sha256).hexdigest())')

GOOD_CODE=$(curl -s -o /tmp/test_webhook_response_good.json -w '%{http_code}' -X POST "${BASE_URL}/webhook" \
  -H "X-Hub-Signature-256: sha256=${GOOD_SIG}" \
  -H 'X-GitHub-Event: pull_request' \
  -H 'Content-Type: application/json' \
  -d "${GOOD_PAYLOAD}")

GOOD_BODY=$(uv run python -c 'import pathlib; print(pathlib.Path("/tmp/test_webhook_response_good.json").read_text(encoding="utf-8"), end="")')

if [ "${GOOD_CODE}" != "200" ]; then
  fail "valid signature should return 200 (got ${GOOD_CODE})"
fi

case "${GOOD_BODY}" in
  *"\"status\":\"ignored\""*|*"\"status\": \"ignored\""*)
    pass "valid signature accepted and bot PR ignored"
    ;;
  *)
    fail "valid request response body unexpected: ${GOOD_BODY}"
    ;;
esac

printf '[PASS] webhook integration checks complete (%s checks)\n' "${PASS_COUNT}"
exit 0
