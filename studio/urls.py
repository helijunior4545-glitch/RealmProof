from django.urls import path
from . import views, review, suites, builder

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
    path("organizations/<slug:slug>/demo/", views.create_demo, name="create_demo"),
    path("organizations/<slug:slug>/scenarios/<uuid:scenario_id>/execute/", views.execute_scenario, name="execute_scenario"),
    path("organizations/<slug:slug>/projects/<uuid:project_id>/review/", review.publish, name="publish_review"),
    path("review/<str:token>/", review.open_review, name="open_review"),
    path("review/<str:token>/replay/", review.replay, name="replay_review"),
    path("organizations/<slug:slug>/reviews/<uuid:event_id>/revoke/", review.revoke, name="revoke_review"),
    path("organizations/<slug:slug>/projects/<uuid:project_id>/suite/", suites.queue_suite, name="queue_suite"),
    path("organizations/<slug:slug>/projects/<uuid:project_id>/export/", suites.export_project, name="export_project"),
    path("organizations/<slug:slug>/builder/", builder.create, name="demo_builder"),
    path("health/", views.health, name="health"),
]
