from django.conf import settings
from django.template.loader import get_template
from django.urls import reverse
from django_tables2 import columns, tables

from apps.experiments.models import (
    ConsentForm,
    Experiment,
    ExperimentRoute,
    ExperimentSession,
    SafetyLayer,
    SourceMaterial,
    Survey,
)
from apps.generics import actions


class ExperimentTable(tables.Table):
    name = columns.Column(
        linkify=True,
        attrs={
            "a": {"class": "link"},
        },
        orderable=True,
    )
    description = columns.Column(verbose_name="Description")
    owner = columns.Column(accessor="owner__username", verbose_name="Created By")
    topic = columns.Column(accessor="source_material__topic", verbose_name="Topic", orderable=True)
    is_public = columns.Column(verbose_name="Publically accessible", orderable=False)
    actions = columns.TemplateColumn(
        template_name="experiments/components/experiment_actions_column.html",
    )

    class Meta:
        model = Experiment
        fields = ("name",)
        row_attrs = settings.DJANGO_TABLES2_ROW_ATTRS
        orderable = False
        empty_text = "No experiments found."


class SafetyLayerTable(tables.Table):
    actions = actions.ActionsColumn(
        actions=[
            actions.edit_action(url_name="experiments:safety_edit"),
            actions.delete_action(url_name="experiments:safety_delete"),
        ]
    )

    class Meta:
        model = SafetyLayer
        fields = (
            "name",
            "messages_to_review",
            "actions",
        )
        row_attrs = settings.DJANGO_TABLES2_ROW_ATTRS
        orderable = False
        empty_text = "No safety layers found."


class SourceMaterialTable(tables.Table):
    owner = columns.Column(accessor="owner__username", verbose_name="Created By")
    actions = actions.ActionsColumn(
        actions=[
            actions.edit_action(url_name="experiments:source_material_edit"),
            actions.delete_action(url_name="experiments:source_material_delete"),
        ]
    )

    class Meta:
        model = SourceMaterial
        fields = (
            "topic",
            "description",
            "owner",
        )
        row_attrs = settings.DJANGO_TABLES2_ROW_ATTRS
        orderable = False
        empty_text = "No source material found."


class SurveyTable(tables.Table):
    actions = actions.ActionsColumn(
        actions=[
            actions.edit_action(url_name="experiments:survey_edit"),
            actions.delete_action(url_name="experiments:survey_delete"),
        ]
    )

    class Meta:
        model = Survey
        fields = (
            "name",
            "url",
        )
        row_attrs = settings.DJANGO_TABLES2_ROW_ATTRS
        orderable = False
        empty_text = "No surveys found."


class ConsentFormTable(tables.Table):
    actions = actions.ActionsColumn(
        actions=[
            actions.edit_action(url_name="experiments:consent_edit"),
            actions.delete_action(
                url_name="experiments:consent_delete",
                display_condition=lambda request, record: not record.is_default,
            ),
        ]
    )

    class Meta:
        model = ConsentForm
        fields = (
            "name",
            "capture_identifier",
            "identifier_label",
            "identifier_type",
            "is_default",
        )
        row_attrs = settings.DJANGO_TABLES2_ROW_ATTRS
        orderable = False
        empty_text = "No consent forms found."


class ExperimentSessionsTable(tables.Table):
    participant = actions.chip_column(
        accessor="participant", align="left", orderable=True, order_by="participant__identifier"
    )
    started = columns.Column(accessor="created_at", verbose_name="Started", orderable=True)
    last_message = columns.Column(accessor="last_message_created_at", verbose_name="Last Message", orderable=True)
    tags = columns.TemplateColumn(
        verbose_name="Tags",
        template_name="annotations/tag_ui.html",
    )
    versions = columns.Column(verbose_name="Versions", accessor="experiment_version_for_display")
    actions = actions.chip_column(label="Session Details", align="center", verbose_name="")

    def render_tags(self, record, bound_column):
        template = get_template(bound_column.column.template_name)
        return template.render({"object": record.chat})

    class Meta:
        model = ExperimentSession
        fields = []
        row_attrs = settings.DJANGO_TABLES2_ROW_ATTRS
        orderable = False
        empty_text = "No sessions yet!"


class ExperimentVersionsTable(tables.Table):
    version_number = columns.Column(verbose_name="Version Number", accessor="version_number")
    created_at = columns.Column(verbose_name="Created On", accessor="created_at")
    version_description = columns.Column(verbose_name="Description", default="")
    is_default = columns.TemplateColumn(
        template_code="""{% if record.is_default_version %}
        <span aria-label="true">✓</span>
        {% endif %}""",
        verbose_name="Deployed",
    )
    actions = columns.TemplateColumn(
        template_name="experiments/components/experiment_version_actions.html",
        verbose_name="",
        attrs={"td": {"class": "overflow-visible"}},
    )

    class Meta:
        model = Experiment
        fields = []
        row_attrs = {"class": "text-sm"}
        orderable = False
        empty_text = "No versions yet!"


def _get_route_url(url_name, request, record, value):
    return reverse(url_name, args=[request.team.slug, record.parent_id, record.pk])


class ChildExperimentRoutesTable(tables.Table):
    child = actions.chip_column(orderable=True)
    actions = actions.ActionsColumn(
        actions=[
            actions.edit_action(
                url_name="experiments:experiment_route_edit",
                url_factory=_get_route_url,
            ),
            actions.delete_action(
                url_name="experiments:experiment_route_delete",
                url_factory=_get_route_url,
            ),
        ]
    )

    class Meta:
        model = ExperimentRoute
        fields = ["child", "keyword", "is_default", "actions"]
        orderable = False
        row_attrs = settings.DJANGO_TABLES2_ROW_ATTRS
        empty_text = "No routes yet!"


class TerminalBotsTable(ChildExperimentRoutesTable):
    child = actions.chip_column(orderable=True)

    class Meta:
        model = ExperimentRoute
        fields = ["child", "is_default", "actions"]
        orderable = False
        row_attrs = settings.DJANGO_TABLES2_ROW_ATTRS
        empty_text = "No terminal bots yet!"


class ParentExperimentRoutesTable(tables.Table):
    parent = actions.chip_column(orderable=True)

    class Meta:
        model = ExperimentRoute
        fields = ["parent", "keyword", "is_default"]
        orderable = False
        row_attrs = settings.DJANGO_TABLES2_ROW_ATTRS
        empty_text = "No routes yet!"
