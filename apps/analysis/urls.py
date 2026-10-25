from django.urls import path

from . import views

app_name = "analysis"

urlpatterns = [
    path("assets/", views.assets, name="assets"),
    path("history/<str:symbol>/", views.history, name="history"),
    path("refresh/", views.refresh, name="refresh"),
]
