# External Grafana Evolve scenario: cascade failure boundary

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
полной реализации. Самостоятельно найди в SpecSpine затрагиваемые
архитектурные границы и сохрани их canonical ownership. Не вводи новые
implementation, persistence или delivery decisions, тесты либо сроки.

Сначала собери минимальный архитектурный контекст из SpecSpine, затем выполни
изменение через Evolve. Если в изолированном окружении доступен Extract, используй
его для этапа сбора контекста; если его нет, найди тот же контекст обычной
навигацией по SpecSpine.
