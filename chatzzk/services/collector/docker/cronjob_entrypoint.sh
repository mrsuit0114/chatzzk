#!/bin/bash
# cronjob_entrypoint.sh

set -e

# 첫 번째 인자가 없으면 에러 출력
if [ -z "$1" ]; then
    echo "Error: No trigger function name provided."
    echo "Usage: $0 <trigger_function_name>"
    exit 1
fi

TRIGGER_FUNCTION=$1
echo "Executing trigger function: ${TRIGGER_FUNCTION}"

# Python을 실행하여 triggers.py의 특정 함수를 호출
exec python -c "from chatzzk.services.collector.jobs.triggers import ${TRIGGER_FUNCTION}; ${TRIGGER_FUNCTION}()"
