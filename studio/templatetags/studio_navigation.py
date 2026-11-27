from django import template
from django.urls import reverse

from studio.guest import studio_destination
from studio.models import Project

register = template.Library()


@register.simple_tag(takes_context=True)
def workbench_url(context):
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return None
    member = context.get("member")
    if not member:
        return studio_destination(request, "studio:workbench")

    project = context.get("project")
    run = context.get("run")
    if project:
        project_id = project.pk
    elif run:
        project_id = run.scenario.project_id
    else:
        project_id = (
            Project.objects.filter(organization=member.organization)
            .order_by("-created_at", "pk")
            .values_list("pk", flat=True)
            .first()
        )

    if project_id:
        return reverse("studio:workbench", args=[member.organization.slug, project_id])
    return None
