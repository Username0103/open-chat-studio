from uuid import UUID

from celery.app import shared_task
from django.contrib.contenttypes.models import ContentType
from django.db.models import Subquery
from taskbadger.celery import Task as TaskbadgerTask

from apps.channels.clients.connect_client import ConnectClient
from apps.channels.models import ChannelPlatform, ExperimentChannel
from apps.experiments.models import Experiment, ParticipantData


@shared_task(bind=True, base=TaskbadgerTask, ignore_result=True)
def setup_connect_channels_for_bots(self, connect_id: UUID, experiment_data_map: dict):
    """
    Set up Connect channels for experiments that are using the ConnectMessaging channel

    experiment_data_map: {experiment_id: participant_data_id}
    """

    experiment_ids = list(experiment_data_map.keys())
    participant_data_ids = list(experiment_data_map.values())
    connect_specific_data = ParticipantData.objects.filter(
        id__in=participant_data_ids, participant__platform=ChannelPlatform.CONNECT_MESSAGING
    ).values_list("id", flat=True)

    # Only create channels for experiments that are using the ConnectMessaging channel
    experiments_using_connect = ExperimentChannel.objects.filter(
        platform=ChannelPlatform.CONNECT_MESSAGING,
        experiment__id__in=experiment_ids,
    ).values_list("experiment_id", flat=True)

    participant_data = (
        ParticipantData.objects.filter(
            id__in=Subquery(connect_specific_data),
            participant__platform=ChannelPlatform.CONNECT_MESSAGING,
            object_id__in=Subquery(experiments_using_connect),
            content_type=ContentType.objects.get_for_model(Experiment),
        )
        .exclude(system_metadata__has_key="channel_id")
        .all()
    )

    connect_client = ConnectClient()

    for participant_datum in participant_data:
        experiment = participant_datum.content_object
        channel_id = connect_client.create_channel(
            connect_id=connect_id, channel_source=f"{experiment.team}-{experiment.name}"
        )
        participant_datum.system_metadata["channel_id"] = channel_id
        participant_datum.save(update_fields=["system_metadata"])
