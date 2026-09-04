from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Chore, ChoreStatus, Frequency, HouseholdSettings, Season


def board_view(request):
    """Main Kanban board showing Unclaimed, In Progress, and Completed chores."""
    settings = HouseholdSettings.get_settings()
    active_season = request.GET.get("season", settings.current_season)

    # Base query
    chores = Chore.objects.select_related("claimed_by").all()

    # Filter by season
    in_season_chores = [c for c in chores if c.is_in_season(active_season)]

    unclaimed_chores = [
        c for c in in_season_chores if c.status == ChoreStatus.UNCLAIMED
    ]
    in_progress_chores = [
        c for c in in_season_chores if c.status == ChoreStatus.IN_PROGRESS
    ]

    # Completed chores (from last 7 days or recently completed)
    one_week_ago = timezone.now() - timedelta(days=7)
    completed_chores = [
        c for c in chores
        if c.status == ChoreStatus.COMPLETED
        and (c.completed_at is None or c.completed_at >= one_week_ago)
    ]
    completed_chores.sort(
        key=lambda c: c.completed_at or timezone.now(), reverse=True
    )

    users = User.objects.all()

    context = {
        "settings": settings,
        "active_season": active_season,
        "seasons": Season.choices,
        "frequencies": Frequency.choices,
        "unclaimed_chores": unclaimed_chores,
        "in_progress_chores": in_progress_chores,
        "completed_chores": completed_chores,
        "users": users,
        "today": timezone.localdate(),
    }
    return render(request, "chores/board.html", context)


@require_POST
def claim_chore(request, pk):
    """Claim a chore from the open pool."""
    chore = get_object_or_404(Chore, pk=pk)
    user = None

    if request.user.is_authenticated:
        user = request.user
    else:
        user_id = request.POST.get("user_id")
        if user_id:
            user = User.objects.filter(id=user_id).first()
        if not user:
            # Fallback to demo/household user
            user, _ = User.objects.get_or_create(
                username="Household Member", defaults={"first_name": "Household", "last_name": "Member"}
            )

    chore.claim(user)
    messages.success(request, f"'{chore.title}' claimed by {user.get_full_name() or user.username}!")
    return redirect("chores:board")


@require_POST
def unclaim_chore(request, pk):
    """Release a chore back to the open pool."""
    chore = get_object_or_404(Chore, pk=pk)
    chore.unclaim()
    messages.info(request, f"'{chore.title}' released back to the unclaimed pool.")
    return redirect("chores:board")


@require_POST
def complete_chore(request, pk):
    """Mark a chore complete and spawn next recurrence if configured."""
    chore = get_object_or_404(Chore, pk=pk)
    next_chore = chore.complete()
    if next_chore:
        messages.success(
            request,
            f"Completed '{chore.title}'! Next instance scheduled for {next_chore.due_date}.",
        )
    else:
        messages.success(request, f"Completed '{chore.title}'!")
    return redirect("chores:board")


@require_POST
def create_chore(request):
    """Create a new chore and add it to the open pool."""
    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    due_date_str = request.POST.get("due_date")
    frequency = request.POST.get("frequency", Frequency.ONE_OFF)
    season = request.POST.get("season", Season.YEAR_ROUND)

    if not title:
        messages.error(request, "Chore title cannot be empty.")
        return redirect("chores:board")

    if not due_date_str:
        due_date = timezone.localdate() + timedelta(days=2)
    else:
        due_date = due_date_str

    Chore.objects.create(
        title=title,
        description=description,
        status=ChoreStatus.UNCLAIMED,
        due_date=due_date,
        frequency=frequency,
        season=season,
    )
    messages.success(request, f"Added chore '{title}' to the pool!")
    return redirect("chores:board")


@require_POST
def update_season(request):
    """Update current household season toggle."""
    new_season = request.POST.get("season")
    if new_season in dict(Season.choices):
        settings = HouseholdSettings.get_settings()
        settings.current_season = new_season
        settings.save(update_fields=["current_season"])
        messages.success(request, f"Household season set to {settings.get_current_season_display()}!")
    return redirect("chores:board")
