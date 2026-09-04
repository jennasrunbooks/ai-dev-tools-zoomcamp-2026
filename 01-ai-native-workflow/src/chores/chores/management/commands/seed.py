from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from chores.models import Chore, ChoreStatus, Frequency, HouseholdSettings, Season


class Command(BaseCommand):
    help = "Seeds sample household members (Jenna and Barry) and chores across urgency tiers and seasons."

    def handle(self, *args, **options):
        # Settings
        settings = HouseholdSettings.get_settings()
        settings.name = "Jenna & Barry's Home"
        settings.current_season = Season.SUMMER
        settings.save()

        # Household members
        jenna, _ = User.objects.get_or_create(
            username="jenna",
            defaults={"first_name": "Jenna", "last_name": "S.", "email": "jenna@example.com"}
        )
        barry, _ = User.objects.get_or_create(
            username="barry",
            defaults={"first_name": "Barry", "last_name": "B.", "email": "barry@example.com"}
        )

        today = timezone.localdate()

        # Reset or populate sample chores
        Chore.objects.all().delete()

        # 1. Critical Overdue
        Chore.objects.create(
            title="Deep Clean Oven",
            description="Scrub inside racks and wipe down glass door",
            due_date=today - timedelta(days=4),
            frequency=Frequency.MONTHLY,
            season=Season.YEAR_ROUND,
            status=ChoreStatus.UNCLAIMED,
        )

        # 2. Overdue (Summer chore)
        Chore.objects.create(
            title="Mow Front & Back Lawn",
            description="Mow grass and trim edges along walkway",
            due_date=today - timedelta(days=1),
            frequency=Frequency.WEEKLY,
            season=Season.SUMMER,
            status=ChoreStatus.UNCLAIMED,
        )

        # 3. In Progress (Claimed by Jenna)
        Chore.objects.create(
            title="Empty Dishwasher & Wipe Counters",
            description="Put away clean dishes and sanitize kitchen surfaces",
            due_date=today,
            frequency=Frequency.DAILY,
            season=Season.YEAR_ROUND,
            status=ChoreStatus.IN_PROGRESS,
            claimed_by=jenna,
        )

        # 4. On Track (Year-Round chore)
        Chore.objects.create(
            title="Clean Bathroom Mirrors & Sink",
            description="Disinfect sinks and wipe down glass",
            due_date=today + timedelta(days=3),
            frequency=Frequency.WEEKLY,
            season=Season.YEAR_ROUND,
            status=ChoreStatus.UNCLAIMED,
        )

        # 5. Off-Season (Winter chore - hidden when Summer is active)
        Chore.objects.create(
            title="Shovel Driveway & De-ice Walkway",
            description="Clear snow and apply rock salt to stairs",
            due_date=today + timedelta(days=1),
            frequency=Frequency.SEASONAL,
            season=Season.WINTER,
            status=ChoreStatus.UNCLAIMED,
        )

        # 6. Completed (Finished by Barry)
        Chore.objects.create(
            title="Take Out Trash & Recycling",
            description="Wheel bins to the curb",
            due_date=today - timedelta(days=1),
            frequency=Frequency.WEEKLY,
            season=Season.YEAR_ROUND,
            status=ChoreStatus.COMPLETED,
            claimed_by=barry,
            completed_at=timezone.now() - timedelta(hours=5),
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded Jenna & Barry's household and sample chores."))
