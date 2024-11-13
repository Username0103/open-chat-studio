from unittest import mock

import pytest

from apps.analysis.core import StepContext
from apps.analysis.models import Analysis, AnalysisRun, RunGroup, RunStatus
from apps.analysis.tasks import PipelineSplitSignal, RunStatusContext, run_context
from apps.analysis.tests.demo_steps import Multiply
from apps.service_providers.models import LlmProvider
from apps.utils.factories.service_provider_factories import LlmProviderModelFactory


@pytest.fixture()
def llm_provider(team_with_users):
    return LlmProvider.objects.create(
        name="test",
        type="openai",
        team=team_with_users,
        config={
            "openai_api_key": "123123123",
        },
    )


@pytest.fixture()
def llm_provider_model(team_with_users):
    return LlmProviderModelFactory(team=team_with_users, name="test")


@pytest.fixture()
def analysis(team_with_users, llm_provider, llm_provider_model):
    return Analysis.objects.create(
        team=team_with_users,
        name="test",
        source="test",
        llm_provider=llm_provider,
        llm_provider_model=llm_provider_model,
    )


@pytest.fixture()
def mock_run_group(llm_provider_model):
    analysis = Analysis(llm_provider=LlmProvider(), llm_provider_model=llm_provider_model)
    analysis.llm_provider.get_llm_service = mock.MagicMock()
    group = RunGroup(analysis=analysis, params={})
    group.save = mock.MagicMock()
    group.refresh_from_db = mock.MagicMock()
    return group


@pytest.fixture()
def mock_analysis_run(mock_run_group):
    run = AnalysisRun(group=mock_run_group)
    run.save = mock.MagicMock()
    run.refresh_from_db = mock.MagicMock()
    return run


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({}, {"llm_model": "test"}),
        ({"llm_model": "test2"}, {"llm_model": "test"}),
        ({"foo": "bar"}, {"llm_model": "test", "foo": "bar"}),
    ],
)
# @pytest.mark.django_db
def test_run_context_params(params, expected, mock_analysis_run):
    mock_analysis_run.group.params = params
    with run_context(mock_analysis_run) as pipeline_context:
        assert pipeline_context.params == expected


def test_run_context(mock_analysis_run):
    with run_context(mock_analysis_run) as pipeline_context:
        assert mock_analysis_run.start_time is not None
        assert mock_analysis_run.status == RunStatus.RUNNING
        pipeline_context.params = {"factor": 2}
        step = Multiply()
        step.invoke(StepContext.initial(1), pipeline_context)

    assert mock_analysis_run.end_time is not None
    assert mock_analysis_run.status == RunStatus.SUCCESS
    logs = [(entry["logger"], entry["message"]) for entry in mock_analysis_run.log["entries"]]
    assert logs == [
        ("Multiply", "Running step Multiply"),
        ("Multiply", "Params: factor=2 say=None"),
        ("Multiply", "Step Multiply complete"),
    ]


def test_run_context_error(mock_analysis_run):
    with pytest.raises(Exception, match="test exception"):
        with run_context(mock_analysis_run):
            raise Exception("test exception")

    assert mock_analysis_run.end_time is not None
    assert mock_analysis_run.status == RunStatus.ERROR
    assert mock_analysis_run.error == """Exception('test exception')"""


def test_run_status_context(mock_run_group):
    with RunStatusContext(mock_run_group):
        assert mock_run_group.start_time is not None
        assert mock_run_group.status == RunStatus.RUNNING

    assert mock_run_group.end_time is not None
    assert mock_run_group.status == RunStatus.SUCCESS
    assert mock_run_group.error == ""


def test_run_status_context_error(mock_run_group):
    with RunStatusContext(mock_run_group, bubble_errors=False):
        raise Exception("test exception")

    assert mock_run_group.end_time is not None
    assert mock_run_group.status == RunStatus.ERROR
    assert mock_run_group.error == """Exception('test exception')"""


def test_run_status_context_split(mock_run_group):
    with RunStatusContext(mock_run_group):
        raise PipelineSplitSignal()

    assert mock_run_group.end_time is None
    assert mock_run_group.status == RunStatus.RUNNING
    assert mock_run_group.error == ""
