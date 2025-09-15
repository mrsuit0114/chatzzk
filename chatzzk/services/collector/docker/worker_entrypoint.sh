#!/bin/bash
# worker_entrypoint.sh

# 스크립트 실행 중 오류 발생 시 즉시 중단
set -e

echo "Starting Celery worker..."

# Celery 워커 실행. -A는 Celery 앱의 위치, -c는 동시성(프로세스 수)
# $CELERY_CONCURRENCY 환경 변수가 없으면 기본값으로 2 사용
exec celery -A chatzzk.services.collector.celery_app worker -l info -c ${CELERY_CONCURRENCY:-1}
