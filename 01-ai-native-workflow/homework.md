## Question 1: Select your coding agent

You can use any coding agent you want. Which one did you choose? 

> 💡 **Answer:** Antigravity CLI (powered by Gemini models)

## Question 2: Turn the idea into a spec

> 💡 **Key Features Settled On:**
> 1. **Open-Pool Kanban Claim Board:** Shared chore pool (`Unclaimed Pool` → `In Progress` → `Completed This Week`) where members claim tasks on demand via 1-click actions.
> 2. **Deadline-Driven Visual Urgency Engine:** Dynamic Django model property calculating urgency tiers (`🟢 On Track` → `🟡 Due Soon` → `🔴 Overdue` → `🚨 Critical Overdue`) based on `due_date`.
> 3. **Dynamic Seasonal Chore Filtering:** Central household season setting (`SPRING`, `SUMMER`, `FALL`, `WINTER`) filtering active seasonal tasks (e.g., summer lawn care vs. winter snow removal).
> 4. **Automated Recurrence & History Archive:** Completed recurring chores timestamp history and automatically spawn the next instance into the open pool with an updated deadline.
> 
> *Full spec saved to `_docs/plan.md`*

## Question 3: Django project

What's the file you need to edit to include the created app in the project?

> 💡 **Answer:** `settings.py`

## Question 4: Backlog

What's task 1 in the backlog your agent came up with?

> 💡 **Answer:**
> - [x] **Task 1: Project & App Setup**: Initialize Django project with `uv`, create the `chores` app, and register it in `config/settings.py` (`INSTALLED_APPS`).
>
> *Full backlog saved to `_docs/backlog.md`*

## Question 5: First version

Run the server. Which command do you use to start the Django development server?

> 💡 **Answer:** `uv run python manage.py runserver`

## Question 6: Tests

What's the command you use for running tests in the terminal?

> 💡 **Answer:** `python manage.py test` (or `uv run python manage.py test`)
