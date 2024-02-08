from typing import Sequence

import freezegun
import pytest
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from apps.chat.models import Chat, ChatMessage, ChatMessageType
from apps.experiments.models import SourceMaterial
from apps.service_providers.llm_service.runnables import AgentExperimentRunnable, ChainOutput
from apps.utils.factories.experiment import ExperimentSessionFactory
from apps.utils.langchain import FakeLlm, FakeLlmService


@pytest.fixture()
def fake_llm():
    return FakeLlm(responses=["this is a test message"], token_counts=[30, 20, 10])


@pytest.fixture()
def session(fake_llm):
    session = ExperimentSessionFactory()
    session.experiment.llm_provider.get_llm_service = lambda: FakeLlmService(llm=fake_llm)
    session.experiment.tools_enabled = True
    return session


@pytest.fixture()
def chat(team_with_users):
    chat = Chat.objects.create(team=team_with_users)
    ChatMessage.objects.create(chat=chat, content="Hello", message_type=ChatMessageType.HUMAN)
    return chat


@pytest.mark.django_db
@freezegun.freeze_time("2024-02-08 13:00:08.877096+00:00")
def test_agent_runnable(session, fake_llm):
    runnable = AgentExperimentRunnable(experiment=session.experiment, session=session)
    result = runnable.invoke("hi")
    assert result == ChainOutput(output="this is a test message", prompt_tokens=30, completion_tokens=20)
    assert fake_llm.get_call_messages() == [
        [
            SystemMessage(content="You are a helpful assistant"),
            HumanMessage(content="hi"),
            SystemMessage(content="2024-02-08 13:00:08.877096+00:00"),
        ]
    ]
    assert "tools" in fake_llm.get_calls()[0].kwargs


@pytest.mark.django_db
def test_agent_runnable_with_source_material(session, fake_llm):
    session.experiment.source_material = SourceMaterial(material="this is the source material")
    session.experiment.prompt_text = "System prompt with {source_material}"
    runnable = AgentExperimentRunnable(experiment=session.experiment, session=session)
    result = runnable.invoke("hi")
    assert result == ChainOutput(output="this is a test message", prompt_tokens=30, completion_tokens=20)
    assert fake_llm.get_call_messages()[0][0] == SystemMessage(content="System prompt with this is the source material")


@pytest.mark.django_db
def test_agent_runnable_with_source_material_missing(session, fake_llm):
    session.experiment.prompt_text = "System prompt with {source_material}"
    runnable = AgentExperimentRunnable(experiment=session.experiment, session=session)
    result = runnable.invoke("hi")
    assert result == ChainOutput(output="this is a test message", prompt_tokens=30, completion_tokens=20)
    assert fake_llm.get_call_messages()[0][0] == SystemMessage(content="System prompt with ")


@pytest.mark.django_db
def test_agent_runnable_runnable_format_input(session, fake_llm):
    runnable = AgentExperimentRunnable(experiment=session.experiment, session=session)
    session.experiment.input_formatter = "foo {input} bar"
    result = runnable.invoke("hi")
    assert result == ChainOutput(output="this is a test message", prompt_tokens=30, completion_tokens=20)
    assert len(fake_llm.get_calls()) == 1
    assert _messages_to_dict(fake_llm.get_call_messages()[0])[1] == {"human": "foo hi bar"}


@pytest.mark.django_db
def test_agent_runnable_save_input_to_history(session, chat, fake_llm):
    runnable = AgentExperimentRunnable(experiment=session.experiment, session=session)
    session.chat = chat
    assert chat.messages.count() == 1

    result = runnable.invoke("hi", config={"configurable": {"save_input_to_history": False}})

    assert result.output == "this is a test message"
    assert len(fake_llm.get_calls()) == 1
    assert chat.messages.count() == 2


@pytest.mark.django_db
@freezegun.freeze_time("2024-02-08 13:00:08.877096+00:00")
def test_agent_runnable_with_history(session, chat, fake_llm):
    experiment = session.experiment
    experiment.max_token_limit = 0  # disable compression
    session.chat = chat
    assert chat.messages.count() == 1
    runnable = AgentExperimentRunnable(experiment=experiment, session=session)
    result = runnable.invoke("hi")
    assert result == ChainOutput(output="this is a test message", prompt_tokens=30, completion_tokens=20)
    assert len(fake_llm.get_calls()) == 1
    assert _messages_to_dict(fake_llm.get_call_messages()[0]) == [
        {"system": experiment.prompt_text},
        {"human": "Hello"},
        {"human": "hi"},
        {"system": "2024-02-08 13:00:08.877096+00:00"},
    ]
    assert chat.messages.count() == 3


def _messages_to_dict(messages: Sequence[BaseMessage]) -> list[dict]:
    return [{message.type: message.content} for message in messages]
