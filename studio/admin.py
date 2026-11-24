from django.contrib import admin
from .models import Organization, Membership, Project, Scenario, TestRun, AuditEvent

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role")
    list_filter = ("role",)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "created_at")

@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "organization", "family")

@admin.register(TestRun)
class RunAdmin(admin.ModelAdmin):
    list_display = ("scenario", "status", "execution_status", "started_at")
    readonly_fields = [f.name for f in TestRun._meta.fields]

@admin.register(AuditEvent)
class AuditAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "organization", "created_at")
    readonly_fields = [f.name for f in AuditEvent._meta.fields]
