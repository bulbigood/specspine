# External Grafana Grow scenario: optional backend capability

## User request

Углуби существующую спецификацию
`specspine/plugins/plugin-backend-protocol.md` для принятого изменения
совместимости optional backend capability.

Приняты следующие архитектурные решения:

- минимальная negotiated protocol version остаётся v2;
- появление новой optional capability само по себе не повышает версию handshake;
- отсутствие capability и gRPC `Unimplemented` нормализуются в
  `ErrMethodNotImplemented`, после чего caller обязан применить существующий
  fallback либо явно вернуть unsupported outcome;
- результат обнаружения отсутствующей capability кэшируется только на время
  жизни конкретного plugin client и сбрасывается при перезапуске процесса;
- после перезапуска host environment вычисляется заново по существующей
  environment policy;
- cancellation продолжает классифицироваться отдельно от прочих ошибок.

Измени только указанный канонический документ. Сохрани его ID и существующие
Observed claims; добавь принятый контракт как intended architecture, не выдавая
его за уже реализованный. Самостоятельно найди в SpecSpine затрагиваемые
архитектурные границы и сохрани их canonical ownership. Не расширяй изменение
за пределы compatibility policy и не добавляй implementation, rollout, тесты
или сроки.

Сначала собери минимальный архитектурный контекст из SpecSpine, затем выполни
изменение через Grow. Если в изолированном окружении доступен Extract, используй
его для этапа сбора контекста; если его нет, найди тот же контекст обычной
навигацией по SpecSpine.
