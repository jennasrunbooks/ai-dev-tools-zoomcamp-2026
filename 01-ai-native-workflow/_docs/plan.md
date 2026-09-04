# Project Specification: Shared Household Chore System (Django)

## 1. Project Overview
A web-based shared household chore management application built with **Python & Django**. Designed for flexible household dynamics (roommates, couples, or families), the system offers an open chore pool where members claim tasks on demand, automated deadline-driven visual urgency indicators, and dynamic seasonal chore templating (e.g., summer lawn care vs. winter snow removal).

---

## 2. Core Features (The 4 Pillars)

### Feature 1: Open-Pool Kanban Claim Board
* **Description:** Chores live in a shared, transparent board rather than being rigidly assigned. Authenticated household members claim tasks on demand.
* **Pipeline Stages:**
  * `Unclaimed Pool`: Open chores awaiting someone to pick them up.
  * `In Progress`: Chores actively claimed by a household member.
  * `Completed This Week`: Chores completed within the last 7 days.
* **Quick Actions:** One-click POST actions for **"Claim"** (assigns `request.user` and sets status to `IN_PROGRESS`) and **"Complete"** (timestamps completion and moves to `COMPLETED`).

### Feature 2: Deadline-Driven Visual Urgency Engine
* **Description:** Dynamically calculates time-based urgency badges on the Django model layer to eliminate nagging and highlight neglected tasks.
* **Urgency Tiers (Model Property):**
  * 🟢 **On Track:** More than 1 day until `due_date`.
  * 🟡 **Due Soon:** Due today or tomorrow.
  * 🔴 **Overdue:** Past `due_date`.
  * 🚨 **Critical Overdue:** More than 3 days past `due_date` (visually highlighted and escalated to the top of the pool).

### Feature 3: Dynamic Seasonal Chore Filtering
* **Description:** Prevents clutter by showing chores only when relevant to the current time of year.
* **Mechanism:** A `HouseholdSettings` model stores the active household season (`SPRING`, `SUMMER`, `FALL`, `WINTER`, or `ALL`).
* **Behavior:** Chores tagged with a specific season (e.g., lawn mowing in summer, snow shoveling in winter) only appear when the household setting matches, while `YEAR_ROUND` chores remain visible all year.

### Feature 4: Automated Recurrence & History Archive
* **Description:** Chores repeat automatically on defined intervals (`DAILY`, `WEEKLY`, `BIWEEKLY`, `MONTHLY`).
* **Mechanism:** When a recurring chore is marked completed, the system timestamps the completion for history and automatically spawns the next chore instance in the `Unclaimed Pool` with an updated `due_date`.

---

## 3. Django Architecture & Data Models

### 3.1 Django Apps
* `chores`: Core app containing chore management, models, views, and templates.

### 3.2 Models

#### `HouseholdSettings`
* `name` (`CharField`): Household name.
* `current_season` (`CharField`, choices): `SPRING`, `SUMMER`, `FALL`, `WINTER`, `ALL`.

#### `Chore`
* `title` (`CharField`): Name of the chore (e.g., "Mow Lawn", "Clean Bathroom").
* `description` (`TextField`, optional): Detailed instructions.
* `status` (`CharField`, choices): `UNCLAIMED` (default), `IN_PROGRESS`, `COMPLETED`.
* `claimed_by` (`ForeignKey(User)`, null=True, blank=True): Member currently owning the task.
* `due_date` (`DateField`): Target deadline for task completion.
* `frequency` (`CharField`, choices): `ONE_OFF`, `DAILY`, `WEEKLY`, `BIWEEKLY`, `MONTHLY`.
* `season` (`CharField`, choices): `YEAR_ROUND`, `SPRING`, `SUMMER`, `FALL`, `WINTER`.
* `created_at` (`DateTimeField`, auto_now_add=True).
* `completed_at` (`DateTimeField`, null=True, blank=True).

#### Model Methods / Properties
* `urgency_level`: Computes days remaining until `due_date` and returns `("ON_TRACK", "DUE_SOON", "OVERDUE", "CRITICAL")` with corresponding badge colors and CSS classes.
* `is_in_season(current_season)`: Checks if the chore should be visible under the active season.

---

## 4. Key Endpoints & Views

| URL | View | Description |
|---|---|---|
| `/` | `ChoreBoardView` | Kanban dashboard displaying Unclaimed, In Progress, and Completed columns. |
| `/chores/<int:pk>/claim/` | `claim_chore` | POST endpoint to assign chore to `request.user`. |
| `/chores/<int:pk>/complete/` | `complete_chore` | POST endpoint to mark chore done and trigger next recurrence. |
| `/settings/season/` | `update_season` | POST endpoint to switch global active season. |

---

## 5. Development Backlog

* **Task 1: Project & App Setup**: Initialize Django project, create the `chores` app, and register it in `settings.py` (`INSTALLED_APPS`).
* **Task 2: Data Models & Migrations**: Define `HouseholdSettings` and `Chore` models with urgency properties and run initial migrations.
* **Task 3: Kanban Dashboard View**: Build `ChoreBoardView` and responsive HTML template rendering the three status columns and urgency badges.
* **Task 4: Interactive Claim & Complete Actions**: Implement view actions and CSRF-protected forms/buttons for claiming and completing chores.
* **Task 5: Seasonal Filtering & Toggle**: Implement season switcher and filter queryset by current household season.
* **Task 6: Recurrence Engine & Automated Tests**: Implement auto-generation of recurring chores upon completion and comprehensive Django unit tests.
