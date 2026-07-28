# External Grafana Grow scenario: cascade failure boundary

## User request

Углуби существующую спецификацию
`specspine/content/folder-cascade-deletion.md` для принятой failure policy
каскадного удаления folder subtree.

Приняты следующие архитектурные решения:

- force-delete остаётся opt-in операцией, а обычное delete сохраняет прежнюю
  семантику;
- cascade выполняется depth-first, leaves before parents, и не обещает
  транзакционную атомарность всего subtree;
- descendant `NotFound` считается идемпотентным успехом, root `NotFound`
  возвращается caller;
- первая ошибка authorization, search, dashboard deletion или contents cleanup
  останавливает дальнейший обход и возвращается caller;
- уже выполненные удаления не откатываются, а
  `grafana.app/folder-terminating=true` сохраняет видимость незавершённого
  lifecycle для последующего повтора;
- retry с теми же полномочиями обязан безопасно продолжить обход, повторно
  принимая отсутствующих descendants;
- Browse hierarchy после успешного ответа инвалидирует затронутый subtree, но
  frontend не является источником состава каскада.

Измени только указанный канонический документ. Сохрани его ID и существующие
Observed claims; добавь решения как intended architecture без утверждения о
полной реализации. Сохрани границы с dashboard lifecycle, content browse,
Resource API и authorization policy. Не добавляй миграцию library panels,
background job, новый API endpoint, storage schema, rollout, тесты или сроки.

Сначала собери минимальный архитектурный контекст из SpecSpine, затем выполни
изменение через Grow. Если в изолированном окружении доступен Extract, используй
его для этапа сбора контекста; если его нет, найди тот же контекст обычной
навигацией по SpecSpine.
