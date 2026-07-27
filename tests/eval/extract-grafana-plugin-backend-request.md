# External Grafana scenario: plugin backend request lifecycle

## User request

Подготовь архитектурный контекст для изменения обработки backend-запроса к
плагину: handshake и multiplexed protocol, запуск процесса в host environment
и классификацию transport/process failure в HTTP status. Не смешивай этот путь
с адаптером HTTP-ответов Kubernetes resource plugins.
