from django.urls import path
from . import views

app_name = "web"
urlpatterns = [
    path("", views.home, name="home"),
    path("tournaments/new/", views.create_tournament, name="create_tournament"),
    path("tournaments/<slug:code>/", views.tournament_detail, name="tournament_detail"),
    path("tournaments/<slug:code>/join/", views.join_tournament, name="join_tournament"),
    path("tournaments/<slug:code>/start/", views.start_tournament, name="start_tournament"),
    path("tournaments/<slug:code>/action/", views.submit_action, name="submit_action"),
    path("tournaments/<slug:code>/finish/", views.finish_tournament, name="finish_tournament"),
    path("tournaments/<slug:code>/leaderboard/", views.leaderboard, name="leaderboard"),
]
