from django.urls import path
from . import views

app_name = "chores"

urlpatterns = [
    path("", views.board_view, name="board"),
    path("create/", views.create_chore, name="create"),
    path("<int:pk>/claim/", views.claim_chore, name="claim"),
    path("<int:pk>/unclaim/", views.unclaim_chore, name="unclaim"),
    path("<int:pk>/complete/", views.complete_chore, name="complete"),
    path("season/update/", views.update_season, name="update_season"),
]
