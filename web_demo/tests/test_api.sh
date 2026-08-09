#!/bin/bash
# ============================================================
# API Test Suite for Mental Health AI Platform
# Tests all endpoints with curl commands
# ============================================================

set -e

BASE_URL="${API_BASE_URL:-http://localhost:8000}"
API_BASE="$BASE_URL/api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'

# Counters
PASSED=0
FAILED=0

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

test_pass() {
    echo -e "  ${GREEN}✓ PASS:${NC} $1"
    ((PASSED++))
}

test_fail() {
    echo -e "  ${RED}✗ FAIL:${NC} $1"
    ((FAILED++))
}

test_info() {
    echo -e "  ${YELLOW}→ INFO:${NC} $1"
}

# ============================================================
# 1. Health & Root Endpoints
# ============================================================
print_header "1. Health & Root Endpoints"

echo ""
echo "Testing GET /"
ROOT_RESP=$(curl -s "$BASE_URL/")
if echo "$ROOT_RESP" | grep -q "Mental Health AI API"; then
    test_pass "Root endpoint returns API info"
else
    test_fail "Root endpoint failed"
    echo "  Response: $ROOT_RESP"
fi

echo ""
echo "Testing GET /api/health"
HEALTH_RESP=$(curl -s "$API_BASE/health")
if echo "$HEALTH_RESP" | grep -q '"status":"healthy"'; then
    test_pass "Health check returns healthy status"
else
    test_fail "Health check failed"
    echo "  Response: $HEALTH_RESP"
fi

# ============================================================
# 2. Dashboard Stats
# ============================================================
print_header "2. Dashboard Stats Endpoint"

echo ""
echo "Testing GET /api/dashboard/stats"
DASH_RESP=$(curl -s "$API_BASE/dashboard/stats")
if echo "$DASH_RESP" | grep -q '"totalComments"'; then
    test_pass "Dashboard stats returns data"
    test_info "Total Comments: $(echo $DASH_RESP | grep -o '"totalComments":[0-9]*' | cut -d: -f2)"
    test_info "Gold Labels: $(echo $DASH_RESP | grep -o '"goldLabels":[0-9]*' | cut -d: -f2)"
else
    test_fail "Dashboard stats failed"
    echo "  Response: $DASH_RESP"
fi

# ============================================================
# 3. Single Prediction
# ============================================================
print_header "3. Single Prediction Endpoint"

echo ""
echo "Testing POST /api/predict (normal text)"
NORMAL_TEXT="Hôm nay trời đẹp quá, tôi rất vui"
PRED_RESP=$(curl -s -X POST "$API_BASE/predict" \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"$NORMAL_TEXT\"}")

if echo "$PRED_RESP" | grep -q '"prediction"'; then
    test_pass "Single prediction returns result"
    test_info "Prediction: $(echo $PRED_RESP | grep -o '"prediction":"[^"]*"' | cut -d'"' -f4)"
    test_info "Confidence: $(echo $PRED_RESP | grep -o '"confidence":[0-9.]*' | cut -d: -f2)"
    test_info "Risk Level: $(echo $PRED_RESP | grep -o '"riskLevel":"[^"]*"' | cut -d'"' -f4)"
else
    test_fail "Single prediction failed"
    echo "  Response: $PRED_RESP"
fi

echo ""
echo "Testing POST /api/predict (depression text)"
DEPRESS_TEXT="Tôi cảm thấy mệt mỏi và buồn bã, không muốn làm gì cả"
PRED_RESP2=$(curl -s -X POST "$API_BASE/predict" \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"$DEPRESS_TEXT\"}")

if echo "$PRED_RESP2" | grep -q '"prediction"'; then
    test_pass "Depression prediction returns result"
    test_info "Prediction: $(echo $PRED_RESP2 | grep -o '"prediction":"[^"]*"' | cut -d'"' -f4)"
else
    test_fail "Depression prediction failed"
    echo "  Response: $PRED_RESP2"
fi

echo ""
echo "Testing POST /api/predict (empty text - should fail)"
EMPTY_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/predict" \
    -H "Content-Type: application/json" \
    -d '{"text": ""}')
HTTP_CODE=$(echo "$EMPTY_RESP" | tail -1)
if [ "$HTTP_CODE" = "422" ]; then
    test_pass "Empty text validation works (422)"
else
    test_fail "Empty text validation should return 422, got $HTTP_CODE"
fi

# ============================================================
# 4. Batch Prediction
# ============================================================
print_header "4. Batch Prediction Endpoint"

echo ""
echo "Testing POST /api/predict/batch"
BATCH_RESP=$(curl -s -X POST "$API_BASE/predict/batch" \
    -H "Content-Type: application/json" \
    -d '{"comments": ["Tôi rất vui hôm nay", "Tôi cảm thấy mệt mỏi", "Ngày mai đi chơi với bạn"]}')

if echo "$BATCH_RESP" | grep -q '"results"'; then
    test_pass "Batch prediction returns results"
    test_info "Total: $(echo $BATCH_RESP | grep -o '"total":[0-9]*' | cut -d: -f2)"
    test_info "Depression count: $(echo $BATCH_RESP | grep -o '"depression_count":[0-9]*' | cut -d: -f2)"
else
    test_fail "Batch prediction failed"
    echo "  Response: $BATCH_RESP"
fi

echo ""
echo "Testing POST /api/predict/batch (empty array)"
EMPTY_BATCH=$(curl -s -X POST "$API_BASE/predict/batch" \
    -H "Content-Type: application/json" \
    -d '{"comments": []}')
if echo "$EMPTY_BATCH" | grep -q '"results":\[\]'; then
    test_pass "Empty batch returns empty results"
else
    test_fail "Empty batch should return empty results"
fi

# ============================================================
# 5. Topics Endpoint
# ============================================================
print_header "5. Topics Endpoint"

echo ""
echo "Testing GET /api/topics"
TOPICS_RESP=$(curl -s "$API_BASE/topics?limit=5")
if echo "$TOPICS_RESP" | grep -q '"id"'; then
    test_pass "Topics endpoint returns data"
    test_info "Sample topic: $(echo $TOPICS_RESP | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4)"
else
    test_fail "Topics endpoint failed"
    echo "  Response: $TOPICS_RESP"
fi

echo ""
echo "Testing GET /api/topics (invalid limit)"
TOPICS_RESP2=$(curl -s -w "\n%{http_code}" "$API_BASE/topics?limit=999")
HTTP_CODE=$(echo "$TOPICS_RESP2" | tail -1)
if [ "$HTTP_CODE" = "422" ]; then
    test_pass "Invalid limit validation works (422)"
else
    test_fail "Invalid limit should return 422, got $HTTP_CODE"
fi

# ============================================================
# 6. Model Comparison
# ============================================================
print_header "6. Model Comparison Endpoint"

echo ""
echo "Testing GET /api/models/comparison"
MODELS_RESP=$(curl -s "$API_BASE/models/comparison")
if echo "$MODELS_RESP" | grep -q '"models"'; then
    test_pass "Model comparison returns data"
    MODEL_COUNT=$(echo "$MODELS_RESP" | grep -o '"name":"[^"]*"' | wc -l)
    test_info "Number of models: $MODEL_COUNT"
else
    test_fail "Model comparison failed"
    echo "  Response: $MODELS_RESP"
fi

# ============================================================
# 7. Statistics Endpoint
# ============================================================
print_header "7. Statistics Endpoint"

echo ""
echo "Testing GET /api/statistics"
STATS_RESP=$(curl -s "$API_BASE/statistics")
if echo "$STATS_RESP" | grep -q '"confusion_matrix"'; then
    test_pass "Statistics returns data"
    test_info "Class distribution keys: $(echo $STATS_RESP | grep -o '"depression":[0-9]*' | head -1)"
else
    test_fail "Statistics endpoint failed"
    echo "  Response: $STATS_RESP"
fi

# ============================================================
# 8. History Endpoints
# ============================================================
print_header "8. History Endpoints"

echo ""
echo "Testing GET /api/history"
HIST_RESP=$(curl -s "$API_BASE/history?limit=5")
if echo "$HIST_RESP" | grep -q '"items"'; then
    test_pass "History endpoint returns data"
    test_info "Total history items: $(echo $HIST_RESP | grep -o '"total":[0-9]*' | cut -d: -f2)"
else
    test_fail "History endpoint failed"
    echo "  Response: $HIST_RESP"
fi

echo ""
echo "Testing GET /api/history (with offset)"
HIST_RESP2=$(curl -s "$API_BASE/history?limit=5&offset=5")
if echo "$HIST_RESP2" | grep -q '"items"'; then
    test_pass "History with offset works"
else
    test_fail "History with offset failed"
fi

echo ""
echo "Testing POST /api/history (save entry)"
SAVE_RESP=$(curl -s -X POST "$API_BASE/history" \
    -H "Content-Type: application/json" \
    -d '{"text": "Test entry for API testing"}')
if echo "$SAVE_RESP" | grep -q '"status":"saved"'; then
    test_pass "Save history entry works"
    HISTORY_ID=$(echo "$SAVE_RESP" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    test_info "Saved ID: $HISTORY_ID"

    # Test delete with the saved ID
    echo ""
    echo "Testing DELETE /api/history/{id}"
    DELETE_RESP=$(curl -s -X DELETE "$API_BASE/history/$HISTORY_ID")
    if echo "$DELETE_RESP" | grep -q '"status":"deleted"'; then
        test_pass "Delete history entry works"
    else
        test_fail "Delete history entry failed"
    fi
else
    test_fail "Save history entry failed"
    echo "  Response: $SAVE_RESP"
fi

echo ""
echo "Testing DELETE /api/history (non-existent ID)"
DELETE_RESP2=$(curl -s -w "\n%{http_code}" -X DELETE "$API_BASE/history/non-existent-id-123")
HTTP_CODE=$(echo "$DELETE_RESP2" | tail -1)
if [ "$HTTP_CODE" = "404" ]; then
    test_pass "Delete non-existent ID returns 404"
else
    test_fail "Delete non-existent ID should return 404, got $HTTP_CODE"
fi

# ============================================================
# 9. Model Refresh Endpoints
# ============================================================
print_header "9. Model Refresh Endpoints"

echo ""
echo "Testing GET /api/models/refresh/status"
REFRESH_STATUS=$(curl -s "$API_BASE/models/refresh/status")
if echo "$REFRESH_STATUS" | grep -q '"status"'; then
    test_pass "Refresh status endpoint works"
    test_info "Status: $(echo $REFRESH_STATUS | grep -o '"status":"[^"]*"' | cut -d'"' -f4)"
else
    test_fail "Refresh status endpoint failed"
    echo "  Response: $REFRESH_STATUS"
fi

echo ""
echo "Testing POST /api/models/refresh"
REFRESH_RESP=$(curl -s -X POST "$API_BASE/models/refresh")
if echo "$REFRESH_RESP" | grep -q '"status"'; then
    test_pass "Model refresh works"
    test_info "Refresh status: $(echo $REFRESH_RESP | grep -o '"status":"[^"]*"' | cut -d'"' -f4)"
else
    test_fail "Model refresh failed"
    echo "  Response: $REFRESH_RESP"
fi

# ============================================================
# Summary
# ============================================================
print_header "Test Summary"
echo ""
echo -e "  ${GREEN}Passed: $PASSED${NC}"
echo -e "  ${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! 🎉${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please check the output above.${NC}"
    exit 1
fi
