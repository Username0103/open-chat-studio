from unittest import mock
from unittest.mock import patch

import pytest

from apps.annotations.models import TagCategories
from apps.chat.bots import TopicBot
from apps.chat.models import ChatMessage, ChatMessageType
from apps.experiments.models import ExperimentRoute, ExperimentRouteType, ExperimentSession, SafetyLayer
from apps.service_providers.tracing.trace_service import TracingServiceWrapper
from apps.utils.factories.experiment import ExperimentFactory, ExperimentSessionFactory
from apps.utils.langchain import build_fake_llm_service, mock_experiment_llm


@pytest.mark.django_db()
@patch("apps.chat.bots.SafetyBot.is_safe")
def test_safety_response(is_safe_mock):
    is_safe_mock.return_value = False
    session = ExperimentSessionFactory()
    experiment = session.experiment
    layer = SafetyLayer.objects.create(
        prompt_text="Is this message safe?", team=experiment.team, prompt_to_bot="Unsafe reply"
    )
    experiment.safety_layers.add(layer)

    expected = "Sorry I can't help with that."
    experiment.get_llm_service = lambda: build_fake_llm_service([expected], token_counts=[1])

    bot = TopicBot(session)
    with patch.object(TopicBot, "_get_safe_response", wraps=bot._get_safe_response) as mock_get_safe_response:
        response = bot.process_input("It's my way or the highway!")

    mock_get_safe_response.assert_called()
    assert response == expected


@pytest.mark.django_db()
@patch("apps.service_providers.llm_service.runnables.SimpleLLMChat._get_output_check_cancellation")
def test_bot_with_terminal_bot(get_output_check_cancellation):
    get_output_check_cancellation.side_effect = ["let's barbecue!", "kom ons braai!"]
    session = ExperimentSessionFactory()
    experiment = session.experiment
    ExperimentRoute.objects.create(
        team=experiment.team,
        parent=experiment,
        child=ExperimentFactory(team=experiment.team),
        type=ExperimentRouteType.TERMINAL,
    )

    expected = "Sorry I can't help with that."
    bot = TopicBot(session)
    with mock_experiment_llm(experiment, responses=[expected]):
        bot.process_input("What are we going to do?")

    assert session.chat.messages.count() == 2
    assert session.chat.messages.get(message_type="human").content == "What are we going to do?"
    assert session.chat.messages.get(message_type="ai").content == "kom ons braai!"


@pytest.mark.django_db()
def test_get_safe_response_creates_ai_message_for_default_messages():
    session = ExperimentSessionFactory()
    layer = SafetyLayer.objects.create(prompt_text="Is this message safe?", team=session.experiment.team)
    session.experiment.safety_layers.add(layer)

    bot = TopicBot(session)
    bot._get_safe_response(layer)
    message = ChatMessage.objects.get(chat__team=session.team, message_type=ChatMessageType.AI)
    assert message.content == "Sorry, I can't answer that. Please try something else."
    assert message.tags.get(category=TagCategories.SAFETY_LAYER_RESPONSE) is not None


@pytest.mark.django_db()
def test_tracing_service():
    session = ExperimentSessionFactory()
    with mock_experiment_llm(None, responses=["response"]):
        tracer = mock.Mock(wraps=TracingServiceWrapper([]))
        bot = TopicBot(session, tracer=tracer)
        assert bot.process_input("test") == "response"
        tracer.get_langchain_callbacks.assert_called_once()
        assert tracer.get_current_trace_info.call_count == 2
    bot.process_input("test")


@pytest.mark.django_db()
def test_tracing_service_reentry():
    """This tests simulates successive messages being processed by the bot and
    verifies that the trace service is not called reentrantly."""
    session = ExperimentSessionFactory()

    def _run_bot_with_wrapped_service(session, response):
        """This configures the bot with a wrapped trace provider so that we can
        verify that it was called. The calls to the provider are still passed
        through to the actual service."""
        bot = TopicBot(session, tracer=TracingServiceWrapper([]))
        assert bot.tracer is not None

        # spy on the service
        mock_service = mock.Mock(wraps=bot.tracer)
        bot.tracer = mock_service

        assert bot.process_input("test") == response
        mock_service.get_langchain_callbacks.assert_called_once()

    with mock_experiment_llm(None, responses=["response1", "response2"]):
        _run_bot_with_wrapped_service(session, "response1")

        # reload the session from the DB
        session = ExperimentSession.objects.get(id=session.id)
        _run_bot_with_wrapped_service(session, "response2")
