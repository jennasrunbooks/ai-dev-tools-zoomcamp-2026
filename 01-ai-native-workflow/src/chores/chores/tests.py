from datetime import timedelta
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Chore, ChoreStatus, Frequency, HouseholdSettings, Season


class ChoreUrgencyModelTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()

    def test_urgency_on_track(self):
        chore = Chore.objects.create(
            title="Clean Windows",
            due_date=self.today + timedelta(days=5),
            frequency=Frequency.WEEKLY,
        )
        self.assertEqual(chore.urgency_code, "ON_TRACK")
        self.assertIn("On Track", chore.urgency_label)

    def test_urgency_due_soon(self):
        chore_tomorrow = Chore.objects.create(
            title="Take Out Trash",
            due_date=self.today + timedelta(days=1),
        )
        self.assertEqual(chore_tomorrow.urgency_code, "DUE_SOON")

        chore_today = Chore.objects.create(
            title="Do Dishes",
            due_date=self.today,
        )
        self.assertEqual(chore_today.urgency_code, "DUE_SOON")

    def test_urgency_overdue(self):
        chore = Chore.objects.create(
            title="Vacuum Living Room",
            due_date=self.today - timedelta(days=2),
        )
        self.assertEqual(chore.urgency_code, "OVERDUE")
        self.assertIn("Overdue", chore.urgency_label)

    def test_urgency_critical_overdue(self):
        chore = Chore.objects.create(
            title="Clean Oven",
            due_date=self.today - timedelta(days=5),
        )
        self.assertEqual(chore.urgency_code, "CRITICAL")
        self.assertIn("Critical", chore.urgency_label)

    def test_urgency_completed(self):
        chore = Chore.objects.create(
            title="Water Plants",
            due_date=self.today - timedelta(days=5),
            status=ChoreStatus.COMPLETED,
        )
        self.assertEqual(chore.urgency_code, "DONE")


class ChoreSeasonalityTests(TestCase):
    def test_is_in_season(self):
        summer_chore = Chore(title="Mow Lawn", season=Season.SUMMER, due_date=timezone.localdate())
        winter_chore = Chore(title="Shovel Snow", season=Season.WINTER, due_date=timezone.localdate())
        year_round_chore = Chore(title="Clean Kitchen", season=Season.YEAR_ROUND, due_date=timezone.localdate())

        # When household is Summer:
        self.assertTrue(summer_chore.is_in_season(Season.SUMMER))
        self.assertFalse(winter_chore.is_in_season(Season.SUMMER))
        self.assertTrue(year_round_chore.is_in_season(Season.SUMMER))

        # When household is Winter:
        self.assertFalse(summer_chore.is_in_season(Season.WINTER))
        self.assertTrue(winter_chore.is_in_season(Season.WINTER))
        self.assertTrue(year_round_chore.is_in_season(Season.WINTER))

        # When household is ALL:
        self.assertTrue(summer_chore.is_in_season(Season.ALL))
        self.assertTrue(winter_chore.is_in_season(Season.ALL))
        self.assertTrue(year_round_chore.is_in_season(Season.ALL))


class ChoreLifecycleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="jenna", password="password123")
        self.today = timezone.localdate()

    def test_claim_and_unclaim(self):
        chore = Chore.objects.create(
            title="Wipe Counters",
            due_date=self.today + timedelta(days=2),
        )
        self.assertEqual(chore.status, ChoreStatus.UNCLAIMED)
        self.assertIsNone(chore.claimed_by)

        chore.claim(self.user)
        self.assertEqual(chore.status, ChoreStatus.IN_PROGRESS)
        self.assertEqual(chore.claimed_by, self.user)

        chore.unclaim()
        self.assertEqual(chore.status, ChoreStatus.UNCLAIMED)
        self.assertIsNone(chore.claimed_by)

    def test_one_off_completion_does_not_recur(self):
        chore = Chore.objects.create(
            title="Fix Door Hinge",
            due_date=self.today,
            frequency=Frequency.ONE_OFF,
        )
        next_chore = chore.complete()
        self.assertIsNone(next_chore)
        self.assertEqual(chore.status, ChoreStatus.COMPLETED)
        self.assertIsNotNone(chore.completed_at)
        self.assertEqual(Chore.objects.count(), 1)

    def test_weekly_completion_spawns_next_instance(self):
        chore = Chore.objects.create(
            title="Clean Bathrooms",
            due_date=self.today,
            frequency=Frequency.WEEKLY,
            season=Season.YEAR_ROUND,
        )
        next_chore = chore.complete()
        self.assertIsNotNone(next_chore)
        self.assertEqual(next_chore.status, ChoreStatus.UNCLAIMED)
        self.assertIsNone(next_chore.claimed_by)
        self.assertEqual(next_chore.due_date, self.today + timedelta(weeks=1))
        self.assertEqual(Chore.objects.count(), 2)


class ChoreViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="barry", password="password123")
        self.today = timezone.localdate()

    def test_board_view_renders(self):
        Chore.objects.create(
            title="Wash Dishes",
            due_date=self.today,
        )
        response = self.client.get(reverse("chores:board"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Household Task Board")
        self.assertContains(response, "Wash Dishes")

    def test_create_chore_post(self):
        response = self.client.post(
            reverse("chores:create"),
            {
                "title": "Mow the Lawn",
                "description": "Front and back yard",
                "due_date": (self.today + timedelta(days=3)).strftime("%Y-%m-%d"),
                "frequency": Frequency.WEEKLY,
                "season": Season.SUMMER,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Chore.objects.filter(title="Mow the Lawn").exists())

    def test_claim_chore_post(self):
        chore = Chore.objects.create(
            title="Sweep Patio",
            due_date=self.today + timedelta(days=2),
        )
        self.client.login(username="barry", password="password123")
        response = self.client.post(reverse("chores:claim", args=[chore.id]))
        self.assertEqual(response.status_code, 302)

        chore.refresh_from_db()
        self.assertEqual(chore.status, ChoreStatus.IN_PROGRESS)
        self.assertEqual(chore.claimed_by, self.user)

    def test_update_season_post(self):
        response = self.client.post(
            reverse("chores:update_season"),
            {"season": Season.WINTER},
        )
        self.assertEqual(response.status_code, 302)
        settings = HouseholdSettings.get_settings()
        self.assertEqual(settings.current_season, Season.WINTER)
