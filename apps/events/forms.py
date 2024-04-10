from django import forms

from apps.generics.type_select_form import TypeSelectForm

from .models import EventAction, StaticTrigger, TimeoutTrigger


class SummarizeConversationForm(forms.Form):
    prompt = forms.CharField(widget=forms.TextInput, label="With the following prompt:", required=False)


class SendMessageToBotForm(forms.Form):
    message_to_bot = forms.CharField(widget=forms.TextInput, label="With the following prompt:", required=False)


class EmptyForm(forms.Form):
    pass


class EventActionForm(forms.ModelForm):
    class Meta:
        model = EventAction
        fields = ["action_type"]
        labels = {"action_type": "Then..."}

    def save(self, commit=True, *args, **kwargs):
        experiment_id = kwargs.pop("experiment_id")
        instance = super().save(commit=False, *args, **kwargs)
        instance.experiment_id = experiment_id
        if commit:
            instance.save()
        return instance


class EventActionTypeSelectForm(TypeSelectForm):
    def save(self, *args, **kwargs):
        instance = self.primary.save(*args, **kwargs, commit=False)
        instance.params = self.active_secondary().cleaned_data
        instance.save()
        return instance


def get_action_params_form(data=None, instance=None):
    return EventActionTypeSelectForm(
        primary=EventActionForm(data=data, instance=instance),
        secondary={
            "log": EmptyForm(data=data, initial=instance.params if instance else None),
            "send_message_to_bot": SendMessageToBotForm(data=data, initial=instance.params if instance else None),
            "end_conversation": EmptyForm(data=data, initial=instance.params if instance else None),
            "summarize": SummarizeConversationForm(data=data, initial=instance.params if instance else None),
        },
        secondary_key_field="action_type",
    )


class BaseTriggerForm(forms.ModelForm):
    def save(self, commit=True, *args, **kwargs):
        experiment_id = kwargs.pop("experiment_id")
        instance = super().save(commit=False, *args, **kwargs)
        instance.experiment_id = experiment_id
        if commit:
            instance.save()
        return instance


class StaticTriggerForm(BaseTriggerForm):
    class Meta:
        model = StaticTrigger
        fields = ["type"]
        labels = {"type": "When..."}


class TimeoutTriggerForm(BaseTriggerForm):
    class Meta:
        model = TimeoutTrigger
        fields = ["delay", "total_num_triggers"]
        labels = {"total_num_triggers": "Trigger count", "delay": "Wait time"}
