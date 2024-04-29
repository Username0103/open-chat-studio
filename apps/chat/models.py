import logging
from enum import StrEnum
from urllib.parse import quote

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import models
from django.db.models import Case, DateTimeField, F, When
from django.utils import timezone
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _
from langchain.schema import BaseMessage, messages_from_dict

from apps.annotations.models import TaggedModelMixin, UserCommentsMixin
from apps.teams.models import BaseTeamModel
from apps.utils.django_db import MakeInterval
from apps.utils.models import BaseModel

logger = logging.getLogger(__name__)


class Chat(BaseTeamModel, TaggedModelMixin, UserCommentsMixin):
    """
    A chat instance.
    """

    class MetadataKeys(StrEnum):
        OPENAI_THREAD_ID = "openai_thread_id"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    # must match or be greater than experiment name field
    name = models.CharField(max_length=128, default="Unnamed Chat")
    metadata = models.JSONField(default=dict)

    def get_metadata(self, key: MetadataKeys):
        return self.metadata.get(key, None)

    def set_metadata(self, key: MetadataKeys, value, commit=True):
        self.metadata[key] = value
        if commit:
            self.save()

    def get_langchain_messages(self) -> list[BaseMessage]:
        return messages_from_dict([m.to_langchain_dict() for m in self.messages.all()])

    def get_langchain_messages_until_summary(self) -> list[BaseMessage]:
        messages = []
        for message in self.messages.order_by("-created_at").iterator(100):
            messages.append(message.to_langchain_dict())
            if message.summary:
                messages.append(message.summary_to_langchain_dict())
                break

        return messages_from_dict(list(reversed(messages)))


class ChatMessageType(models.TextChoices):
    #  these must correspond to the langchain values
    HUMAN = "human", "Human"
    AI = "ai", "AI"
    SYSTEM = "system", "System"

    @classproperty
    def safety_layer_choices(cls):
        return (
            (choice[0], f"{choice[1]} messages")
            for choice in ChatMessageType.choices
            if choice[0] != ChatMessageType.SYSTEM
        )


class ChatMessage(BaseModel, TaggedModelMixin, UserCommentsMixin):
    """
    A message in a chat. Analogous to the BaseMessage class in langchain.
    """

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    message_type = models.CharField(max_length=10, choices=ChatMessageType.choices)
    content = models.TextField()
    summary = models.TextField(  # noqa DJ001
        null=True, blank=True, help_text="The summary of the conversation up to this point (not including this message)"
    )

    class Meta:
        ordering = ["created_at"]

    @property
    def is_ai_message(self):
        return self.message_type == ChatMessageType.AI

    @property
    def is_human_message(self):
        return self.message_type == ChatMessageType.HUMAN

    @property
    def created_at_datetime(self):
        return quote(self.created_at.isoformat())

    def to_langchain_dict(self) -> dict:
        return self._get_langchain_dict(self.content, self.message_type)

    def summary_to_langchain_dict(self) -> dict:
        return self._get_langchain_dict(self.summary, ChatMessageType.SYSTEM)

    def _get_langchain_dict(self, content, message_type):
        return {
            "type": message_type,
            "data": {
                "content": content,
                "additional_kwargs": {
                    "id": self.id,
                },
            },
        }


class TriggerEvent(models.TextChoices):
    PARTICIPANT_JOINED_EXPERIMENT = ("participant_joined", "A new participant joined the experiment")


class TimePeriod(models.TextChoices):
    HOURS = ("hours", "Hours")
    DAYS = ("days", "Days")
    WEEKS = ("weeks", "Weeks")
    MONTHS = ("months", "Months")


class ScheduledMessageConfig(BaseTeamModel):
    name = models.CharField(max_length=64)
    experiment = models.ForeignKey(
        "experiments.Experiment", on_delete=models.CASCADE, related_name="scheduled_message_configs"
    )
    trigger_event = models.CharField(choices=TriggerEvent.choices, db_index=True, blank=False)
    recurring = models.BooleanField()
    time_period = models.CharField(choices=TimePeriod.choices)
    frequency = models.IntegerField(default=1)
    repetitions = models.IntegerField(default=0)
    prompt_text = models.TextField()

    def save(self, *args, **kwargs):
        if self.recurring and self.repetitions == 0:
            raise ValueError(_("Recurring schedules require `repetitions` to be larger than 0"))
        if not self.recurring and self.repetitions > 0:
            raise ValueError(_("Non recurring schedules cannot have `repetitions` larger than 0"))
        if self.id:
            self.update_scheduled_messages()
        return super().save(*args, **kwargs)

    def update_scheduled_messages(self):
        """
        This method updates the scheduled_messages queryset by considering the following criteria:
        - trigger_event and recurring: No effect. Users will not be able to change these at the moment

        - Number of repetitions:
            - If new repetitions are greater than total_triggers, set is_complete to False.
            - If new repetitions are less than total_triggers, set is_complete to True.

        - Frequency and time period (delta change):
            - If the scheduled message's last_triggered_at field is None (it has not fired), the created_at field
            is used as the baseline for adding the new delta
            - If the scheduled message's last_triggered_at field is not None (it has fired before), that field is
            then used as the baseline for adding the new delta
        """
        (
            self.scheduled_messages.annotate(
                new_delta=MakeInterval(self.time_period, self.frequency),
            ).update(
                is_complete=Case(
                    When(total_triggers__lt=self.repetitions, then=False),
                    When(total_triggers__gte=self.repetitions, then=True),
                    output_field=models.BooleanField(),
                ),
                next_trigger_date=Case(
                    When(last_triggered_at__isnull=True, then=F("created_at") + F("new_delta")),
                    When(last_triggered_at__isnull=False, then=F("last_triggered_at") + F("new_delta")),
                    output_field=DateTimeField(),
                ),
            )
        )


class ScheduledMessage(BaseTeamModel):
    schedule = models.ForeignKey(ScheduledMessageConfig, on_delete=models.CASCADE, related_name="scheduled_messages")
    participant = models.ForeignKey(
        "experiments.Participant", on_delete=models.CASCADE, related_name="schduled_messages"
    )
    next_trigger_date = models.DateTimeField(null=True)
    last_triggered_at = models.DateTimeField(null=True)
    total_triggers = models.IntegerField(default=0)
    is_complete = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["is_complete"])]

    def save(self, *args, **kwargs):
        if not self.next_trigger_date:
            delta = relativedelta(**{self.schedule.time_period: self.schedule.frequency})
            self.next_trigger_date = timezone.now() + delta
        super().save(*args, **kwargs)

    def safe_trigger(self):
        """This wraps a call to the _trigger method in a try-catch block"""
        try:
            self._trigger()
        except Exception as e:
            logger.exception(f"An error occured while trying to send scheduled messsage {self.id}. Error: {e}")

    def _trigger(self):
        delta = relativedelta(**{self.schedule.time_period: self.schedule.frequency})
        utc_now = timezone.now()

        experiment_session = self.participant.get_latest_session()
        experiment_session.send_bot_message(self.schedule.prompt_text, fail_silently=False)

        self.last_triggered_at = utc_now
        self.total_triggers += 1
        if self.total_triggers >= self.schedule.repetitions:
            self.is_complete = True
        else:
            self.next_trigger_date = utc_now + delta

        self.save()
