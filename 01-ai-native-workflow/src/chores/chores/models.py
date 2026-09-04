from datetime import timedelta
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Season(models.TextChoices):
    ALL = "ALL", "All / Any Season"
    YEAR_ROUND = "YEAR_ROUND", "Year-Round"
    SPRING = "SPRING", "Spring"
    SUMMER = "SUMMER", "Summer"
    FALL = "FALL", "Fall"
    WINTER = "WINTER", "Winter"


class Frequency(models.TextChoices):
    ONE_OFF = "ONE_OFF", "One-off"
    DAILY = "DAILY", "Daily"
    WEEKLY = "WEEKLY", "Weekly"
    BIWEEKLY = "BIWEEKLY", "Bi-Weekly"
    MONTHLY = "MONTHLY", "Monthly"
    SEASONAL = "SEASONAL", "Seasonal"


class ChoreStatus(models.TextChoices):
    UNCLAIMED = "UNCLAIMED", "Unclaimed Pool"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"


class HouseholdSettings(models.Model):
    name = models.CharField(max_length=100, default="Our Household")
    current_season = models.CharField(
        max_length=20,
        choices=[
            (Season.ALL, "All / Any Season"),
            (Season.SPRING, "Spring"),
            (Season.SUMMER, "Summer"),
            (Season.FALL, "Fall"),
            (Season.WINTER, "Winter"),
        ],
        default=Season.ALL,
    )

    class Meta:
        verbose_name_plural = "Household Settings"

    def __str__(self):
        return f"{self.name} (Season: {self.get_current_season_display()})"

    @classmethod
    def get_settings(cls):
        settings, _ = cls.objects.get_or_create(id=1, defaults={"name": "Our Household"})
        return settings


class Chore(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=ChoreStatus.choices,
        default=ChoreStatus.UNCLAIMED,
    )
    claimed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="claimed_chores",
    )
    due_date = models.DateField()
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.ONE_OFF,
    )
    season = models.CharField(
        max_length=20,
        choices=Season.choices,
        default=Season.YEAR_ROUND,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["due_date", "created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def urgency_code(self):
        """Returns urgency category code: DONE, CRITICAL, OVERDUE, DUE_SOON, ON_TRACK."""
        if self.status == ChoreStatus.COMPLETED:
            return "DONE"
        if not self.due_date:
            return "NO_DEADLINE"
        today = timezone.localdate()
        delta = (self.due_date - today).days
        if delta < -3:
            return "CRITICAL"
        elif delta < 0:
            return "OVERDUE"
        elif delta <= 1:
            return "DUE_SOON"
        return "ON_TRACK"

    @property
    def urgency_label(self):
        labels = {
            "DONE": "✅ Completed",
            "CRITICAL": "🚨 Critical Overdue",
            "OVERDUE": "🔴 Overdue",
            "DUE_SOON": "🟡 Due Soon",
            "ON_TRACK": "🟢 On Track",
            "NO_DEADLINE": "⚪ No Deadline",
        }
        return labels.get(self.urgency_code, "⚪ No Deadline")

    @property
    def urgency_badge_class(self):
        classes = {
            "DONE": "bg-secondary text-white",
            "CRITICAL": "bg-danger text-white fw-bold animate-pulse",
            "OVERDUE": "bg-danger text-white",
            "DUE_SOON": "bg-warning text-dark",
            "ON_TRACK": "bg-success text-white",
            "NO_DEADLINE": "bg-light text-muted",
        }
        return classes.get(self.urgency_code, "bg-light text-muted")

    def is_in_season(self, current_season: str) -> bool:
        """Determines if this chore matches the current household season."""
        if current_season == Season.ALL:
            return True
        if self.season == Season.YEAR_ROUND:
            return True
        return self.season == current_season

    def claim(self, user: User):
        """Assigns the chore to a user and sets status to in-progress."""
        self.claimed_by = user
        self.status = ChoreStatus.IN_PROGRESS
        self.save(update_fields=["claimed_by", "status"])

    def unclaim(self):
        """Releases the chore back to the unclaimed pool."""
        self.claimed_by = None
        self.status = ChoreStatus.UNCLAIMED
        self.save(update_fields=["claimed_by", "status"])

    def complete(self):
        """Marks the chore as complete and spawns next instance if recurring."""
        self.status = ChoreStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])

        # Recur if applicable
        if self.frequency != Frequency.ONE_OFF:
            return self.spawn_next_recurrence()
        return None

    def spawn_next_recurrence(self):
        """Spawns the next recurring instance of this chore in the unclaimed pool."""
        today = timezone.localdate()
        base_date = max(self.due_date, today)

        delta_map = {
            Frequency.DAILY: timedelta(days=1),
            Frequency.WEEKLY: timedelta(weeks=1),
            Frequency.BIWEEKLY: timedelta(weeks=2),
            Frequency.MONTHLY: timedelta(days=30),
            Frequency.SEASONAL: timedelta(days=90),
        }
        next_due_date = base_date + delta_map.get(self.frequency, timedelta(weeks=1))

        return Chore.objects.create(
            title=self.title,
            description=self.description,
            status=ChoreStatus.UNCLAIMED,
            claimed_by=None,
            due_date=next_due_date,
            frequency=self.frequency,
            season=self.season,
        )
