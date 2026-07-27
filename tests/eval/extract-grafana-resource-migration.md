# External Grafana scenario: resource migration lifecycle

## User request

Подготовь архитектурный контекст для изменения lifecycle миграции одного
Grafana resource с legacy SQL на Unified Storage. Нужно изменить переключение
legacy → dual-write → unified, обработку недоступного migration log и
served-version guard, не смешав это с выполнением backfill migration или общим
Resource API direction.
