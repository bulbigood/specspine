# External Grafana Grow scenario: session recovery policy

## User request

Углуби существующую спецификацию
`specspine/identity-access/authentication-sessions.md` для принятой policy
восстановления пользовательской сессии.

Приняты следующие архитектурные решения:

- failure внешнего provider logout не отменяет локальный logout: локальный
  session token отзывается, а provider failure сохраняется как наблюдаемая
  best-effort ошибка;
- повторный logout отозванной локальной сессии идемпотентен;
- contention или временная недоступность cleanup lock не блокирует
  authentication и login/logout paths; текущий cleanup cycle пропускается, а
  expired tokens всё равно отклоняются при чтении;
- rotation сохраняет только current и previous token в пределах одной
  логической session; previous token не создаёт вторую identity;
- authorization policy получает уже установленную identity и не становится
  владельцем session recovery.

Измени только указанный канонический документ. Сохрани его ID и существующие
Observed claims; запиши решения как intended architecture, не как доказанную
реализацию. Самостоятельно найди в SpecSpine затрагиваемые архитектурные
границы и сохрани их canonical ownership. Не вводи новые provider-specific,
persistence, implementation или delivery decisions, тесты либо сроки.

Сначала собери минимальный архитектурный контекст из SpecSpine, затем выполни
изменение через Grow. Если в изолированном окружении доступен Extract, используй
его для этапа сбора контекста; если его нет, найди тот же контекст обычной
навигацией по SpecSpine.
