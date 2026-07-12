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
    path("tournaments/<slug:code>/hands/<int:hand_number>/wait/", views.hand_wait, name="hand_wait"),
    path("tournaments/<slug:code>/hands/<int:hand_number>/status/", views.hand_status, name="hand_status"),
    path("tournaments/<slug:code>/hands/<int:hand_number>/results/", views.hand_results, name="hand_results"),
    path("tournaments/<slug:code>/hands/<int:hand_number>/reveal-status/", views.reveal_status, name="reveal_status"),
    path("tournaments/<slug:code>/next-hand/", views.next_hand, name="next_hand"),
    path("tournaments/<slug:code>/finish/", views.finish_tournament, name="finish_tournament"),
    path("tournaments/<slug:code>/leaderboard/", views.leaderboard, name="leaderboard"),
]
