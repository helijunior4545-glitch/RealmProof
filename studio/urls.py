from django.urls import path
from . import views, review, suites, builder, public_demo, guest

from . import network, ledger_views, catalog_views, universal_views

from . import source_views, transfer_bench

app_name = "studio"
urlpatterns = [
    path("", guest.entry, name="public_demo"),
    path("test/", transfer_bench.bench, name="test_bench"),
    path("guest/start/", guest.start, name="guest_start"),
    path("reference/", public_demo.home, name="reference_demo"),
    path("workspace/", views.dashboard, name="dashboard"),
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
    path("organizations/<slug:slug>/network/", network.overview, name="network"),
    path("organizations/<slug:slug>/ledger-lab/", ledger_views.overview, name="ledger_lab"),
    path("organizations/<slug:slug>/native-tests/", catalog_views.overview, name="native_catalog"),
    path("organizations/<slug:slug>/universal/", universal_views.overview, name="universal"),
    path("organizations/<slug:slug>/projects/<uuid:project_id>/source/", source_views.overview, name="source_discovery"),
    path("health/", views.health, name="health"),
]
