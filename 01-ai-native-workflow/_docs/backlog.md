# Development Backlog: Shared Household Chore System

Derived from [_docs/plan.md](./_docs/plan.md).

- [x] **Task 1: Project & App Setup**: Initialize Django project with `uv`, create the `chores` app, and register it in `config/settings.py` (`INSTALLED_APPS`).
- [x] **Task 2: Data Models & Migrations**: Define `HouseholdSettings` and `Chore` models with urgency properties, recurrence methods, and run initial migrations.
- [x] **Task 3: Kanban Dashboard View & Templates**: Build `board_view` and responsive Bootstrap Kanban HTML templates displaying Unclaimed Pool, In Progress, and Completed columns.
- [x] **Task 4: Interactive Claim & Complete Actions**: Implement CSRF-protected views and forms for claiming, unclaiming, and completing chores.
- [x] **Task 5: Dynamic Seasonal Filtering & Toggle**: Implement season switcher and filter tasks dynamically by active household season.
- [x] **Task 6: Recurrence Engine & Automated Tests**: Implement auto-generation of recurring chore instances upon completion and write comprehensive unit tests.
