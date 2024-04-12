from contextlib import nullcontext as does_not_raise
from unittest import mock

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from waffle.testutils import override_flag

from apps.experiments.models import Experiment, ExperimentSession, Participant, VoiceResponseBehaviours
from apps.experiments.views.experiment import ExperimentForm, _start_experiment_session, _validate_prompt_variables
from apps.utils.factories.assistants import OpenAiAssistantFactory
from apps.utils.factories.channels import ExperimentChannelFactory
from apps.utils.factories.experiment import ConsentFormFactory, ExperimentFactory, SourceMaterialFactory
from apps.utils.factories.service_provider_factories import LlmProviderFactory
from apps.utils.factories.team import TeamWithUsersFactory


def test_create_experiment_success(db, client, team_with_users):
    user = team_with_users.members.first()
    source_material = SourceMaterialFactory(team=team_with_users)
    consent_form = ConsentFormFactory(team=team_with_users)
    LlmProviderFactory(team=team_with_users)
    client.force_login(user)

    post_data = {
        "name": "some name",
        "description": "Some description",
        "type": "llm",
        "prompt_text": "You are a helpful assistant",
        "source_material": source_material.id if source_material else "",
        "consent_form": consent_form.id,
        "temperature": 0.7,
        "llm_provider": LlmProviderFactory(team=team_with_users).id,
        "llm": "gpt-3.5",
        "max_token_limit": 100,
        "voice_response_behaviour": VoiceResponseBehaviours.RECIPROCAL,
    }

    response = client.post(reverse("experiments:new", args=[team_with_users.slug]), data=post_data)
    assert response.status_code == 302, response.context.form.errors
    experiment = Experiment.objects.filter(owner=user).first()
    assert experiment is not None


@override_flag("assistants", active=True)
@pytest.mark.parametrize(
    ("with_assistant", "with_prompt", "with_llm_provider", "with_llm_model", "errors"),
    [
        (True, False, False, False, {}),
        (False, True, True, True, {}),
        (False, False, True, True, {"prompt_text"}),
        (False, True, False, True, {"llm_provider"}),
        (False, True, True, False, {"llm"}),
    ],
)
def test_experiment_form_with_assistants(
    with_assistant, with_prompt, with_llm_provider, with_llm_model, errors, db, team_with_users
):
    assistant = OpenAiAssistantFactory(team=team_with_users)
    request = mock.Mock()
    request.team = team_with_users
    llm_provider = LlmProviderFactory(team=team_with_users)
    form = ExperimentForm(
        request,
        data={
            "name": "some name",
            "type": "assistant" if with_assistant else "llm",
            "assistant": assistant.id if with_assistant else None,
            "prompt_text": "text" if with_prompt else None,
            "llm_provider": llm_provider.id if with_llm_provider else None,
            "llm": "gpt4" if with_llm_model else None,
            "temperature": 0.7,
            "max_token_limit": 10,
            "consent_form": ConsentFormFactory(team=team_with_users).id,
            "voice_response_behaviour": VoiceResponseBehaviours.RECIPROCAL,
        },
    )
    assert form.is_valid() == bool(not errors), form.errors
    for error in errors:
        assert error in form.errors


@pytest.mark.parametrize(
    ("source_material", "prompt_str", "expectation"),
    [
        (None, "You're an assistant", does_not_raise()),
        ("something", "You're an assistant", does_not_raise()),
        ("something", "Answer questions from this source: {source_material}", does_not_raise()),
        (None, "Answer questions from this source: {source_material}", pytest.raises(ValidationError)),
        (None, "Answer questions from this source: {bob}", pytest.raises(ValidationError)),
        ("something", "Answer questions from this source: {bob}", pytest.raises(ValidationError)),
    ],
)
def test_prompt_variable_validation(source_material, prompt_str, expectation):
    with expectation:
        _validate_prompt_variables(
            {
                "source_material": source_material,
                "prompt_text": prompt_str,
            }
        )


@pytest.mark.django_db()
def test_form_fields():
    path = settings.BASE_DIR / "templates" / "experiments" / "experiment_form.html"
    form_html = path.read_text()
    request = mock.Mock()
    for field in ExperimentForm(request).fields:
        assert field in form_html, f"{field} missing from 'experiment_form.html' template"


@pytest.mark.django_db()
@pytest.mark.parametrize("is_user", [False, True])
@mock.patch("apps.experiments.views.experiment.enqueue_static_triggers")
def test_new_participant_created_on_session_start(_trigger_mock, is_user):
    """For each new experiment session, a participant should be created and linked to the session"""
    identifier = "someone@example.com"
    experiment = ExperimentFactory(team=TeamWithUsersFactory())
    channel = ExperimentChannelFactory(experiment=experiment)
    user = None
    if is_user:
        user = experiment.team.members.first()
        identifier = user.email

    session = _start_experiment_session(
        experiment,
        experiment_channel=channel,
        participant_user=user,
        participant_identifier=identifier,
    )

    assert Participant.objects.filter(team=experiment.team, external_chat_id=identifier).count() == 1
    assert ExperimentSession.objects.filter(team=experiment.team).count() == 1
    assert session.participant.external_chat_id == identifier


@pytest.mark.django_db()
@pytest.mark.parametrize("is_user", [False, True])
@mock.patch("apps.experiments.views.experiment.enqueue_static_triggers")
def test_participant_reused_within_team(_trigger_mock, is_user):
    """Within a team, the same external chat id (or participant identifier) should result in the participant being
    reused, and not result in a new participant being created
    """
    experiment1 = ExperimentFactory(team=TeamWithUsersFactory())
    channel1 = ExperimentChannelFactory(experiment=experiment1)
    team = experiment1.team
    identifier = "someone@example.com"
    user = None
    if is_user:
        user = team.members.first()
        identifier = user.email

    session = _start_experiment_session(
        experiment1,
        experiment_channel=channel1,
        participant_user=user,
        participant_identifier=identifier,
    )

    assert Participant.objects.filter(team=team, external_chat_id=identifier).count() == 1
    assert ExperimentSession.objects.filter(team=team).count() == 1
    assert session.participant.external_chat_id == identifier

    # user starts a second session in the same team
    experiment2 = ExperimentFactory(team=team)
    channel2 = ExperimentChannelFactory(experiment=experiment2)

    session = _start_experiment_session(
        experiment2,
        experiment_channel=channel2,
        participant_user=user,
        participant_identifier=identifier,
    )

    assert Participant.objects.filter(team=team, external_chat_id=identifier).count() == 1
    assert ExperimentSession.objects.filter(team=team).count() == 2
    assert session.participant.external_chat_id == identifier


@pytest.mark.django_db()
@pytest.mark.parametrize("is_user", [False, True])
@mock.patch("apps.experiments.views.experiment.enqueue_static_triggers")
def test_new_participant_created_for_different_teams(_trigger_mock, is_user):
    """A new participant should be created for each team when a user uses the same identifier"""
    experiment1 = ExperimentFactory(team=TeamWithUsersFactory())
    channel1 = ExperimentChannelFactory(experiment=experiment1)
    team = experiment1.team
    identifier = "someone@example.com"
    user = None
    if is_user:
        user = team.members.first()
        identifier = user.email

    session = _start_experiment_session(
        experiment1,
        experiment_channel=channel1,
        participant_user=user,
        participant_identifier=identifier,
    )

    assert Participant.objects.filter(team=team, external_chat_id=identifier).count() == 1
    assert ExperimentSession.objects.filter(team=team).count() == 1
    assert session.participant.external_chat_id == identifier

    # user starts a second session in another team
    if is_user:
        new_team = TeamWithUsersFactory(member__user=user)
    else:
        new_team = TeamWithUsersFactory()

    experiment2 = ExperimentFactory(team=new_team)
    channel2 = ExperimentChannelFactory(experiment=experiment2)

    session = _start_experiment_session(
        experiment2,
        experiment_channel=channel2,
        participant_user=user,
        participant_identifier=identifier,
    )

    assert Participant.objects.filter(team=new_team, external_chat_id=identifier).count() == 1
    assert ExperimentSession.objects.filter(team=new_team).count() == 1

    # There should be two participants with external_chat_id = identifier accross all teams
    assert Participant.objects.filter(external_chat_id=identifier).count() == 2
    assert session.participant.external_chat_id == identifier
