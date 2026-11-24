from django.urls import path
from . import views

app_name = "studio"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("organizations/new/", views.create_organization, name="create_organization"),
    path("organizations/<slug:slug>/", views.organization, name="organization"),
    path("organizations/<slug:slug>/projects/new/", views.create_project, name="create_project"),
    path("organizations/<slug:slug>/projects/<uuid:project_id>/", views.project, name="project"),
    path("organizations/<slug:slug>/projects/<uuid:project_id>/scenarios/new/", views.create_scenario, name="create_scenario"),
    path("organizations/<slug:slug>/runs/<uuid:run_id>/", views.run_detail, name="run_detail"),
    path("organizations/<slug:slug>/scenarios/<uuid:scenario_id>/run/", views.start_run, name="start_run"),
    path("organizations/<slug:slug>/runs/<uuid:run_id>/evaluate/", views.evaluate_run, name="evaluate_run"),
    path("health/", views.health, name="health"),
]
