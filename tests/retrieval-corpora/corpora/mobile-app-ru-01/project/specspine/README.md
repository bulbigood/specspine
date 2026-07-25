# Архитектура мобильного приложения «Город»

**ID:** `project-architecture` · **Kind:** `index`

Приложение показывает транспорт, позволяет покупать билеты и сохраняет
избранные маршруты. Оно работает на Android и iOS, а общие правила описаны
независимо от конкретного UI-фреймворка.

## Карта документации

### Запуск и интерфейс

- [Навигация](navigation.md) — экраны, стеки и восстановление маршрута.
- [Глубокие ссылки](deep-links.md) — разбор внешних URI.
- [Доступность](accessibility.md) — масштаб текста и озвучивание элементов.
- [Флаги функций](feature-flags.md) — безопасное включение возможностей.

### Данные и сеть

- [Автономная синхронизация](offline-sync.md) — владелец разрешения конфликтов.
- [Локальное хранилище](local-storage.md) — схема базы и транзакции.
- [Аутентификация](authentication.md) — сессии и обновление доступа.
- [Кэш изображений](image-cache.md) — память и дисковый кэш.

### Интеграции

- [Push-уведомления](push-notifications.md) — токены доставки и переходы.
- [Платежи](payments.md) — покупка билета и подтверждение операции.
- [Аналитика](analytics.md) — события без персональных данных.

### Эксплуатация

- [Конфигурация](configuration.md) — окружения и удалённые параметры.
- [Выпуск приложения](release-process.md) — сборки и поэтапная публикация.
- [Реагирование на инциденты](incident-playbook.md) — оперативные выключатели.

## Границы

Локальная база хранит подтверждённое состояние и очередь намерений. Экран не
решает конфликты данных и не интерпретирует ответы платёжного провайдера.
Удалённая конфигурация управляет доступностью функций, но не меняет инварианты
данных.

## Coverage

### Mapped

- [Навигация](navigation.md) — bundled fixture is mapped.
- [Глубокие ссылки](deep-links.md) — bundled fixture is mapped.
- [Доступность](accessibility.md) — bundled fixture is mapped.
- [Флаги функций](feature-flags.md) — bundled fixture is mapped.
- [Автономная синхронизация](offline-sync.md) — bundled fixture is mapped.
- [Локальное хранилище](local-storage.md) — bundled fixture is mapped.
- [Аутентификация](authentication.md) — bundled fixture is mapped.
- [Кэш изображений](image-cache.md) — bundled fixture is mapped.
- [Push-уведомления](push-notifications.md) — bundled fixture is mapped.
- [Платежи](payments.md) — bundled fixture is mapped.
- [Аналитика](analytics.md) — bundled fixture is mapped.
- [Конфигурация](configuration.md) — bundled fixture is mapped.
- [Выпуск приложения](release-process.md) — bundled fixture is mapped.
- [Реагирование на инциденты](incident-playbook.md) — bundled fixture is mapped.

### Partially mapped

- No partially mapped bundled areas.

### Unmapped

- No known unmapped bundled areas.
