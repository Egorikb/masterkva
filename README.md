# MasterKva Assembly Workspace

Сюда собирается отдельная версия проекта по приоритетам:

1. Укрепить backend учебного цикла
2. Стабилизировать UI-кабинет
3. Подключить RAG только в учебном контексте
4. Добавить тесты на переходы состояний

## Источники
- Текущий frontend: `/home/egor/workspace_hermes/masterkva/frontend`
- Текущий backend: `/home/egor/workspace_hermes/masterkva/backend`
- Архитектурный референс: `/home/egor/workspace_hermes/DeepTutor`

## Правило сборки
Сначала фиксируем учебной backend-цикл, затем UI, затем учебный RAG, затем тесты. Не расширяемся в payments/TutorBot/book до закрытия этих 4 пунктов.
