from django.contrib import admin
from .models import Chore, HouseholdSettings


@admin.register(HouseholdSettings)
class HouseholdSettingsAdmin(admin.ModelAdmin):
    list_display = ("name", "current_season")


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "claimed_by", "due_date", "season", "frequency", "urgency_label")
    list_filter = ("status", "season", "frequency", "due_date")
    search_fields = ("title", "description")
