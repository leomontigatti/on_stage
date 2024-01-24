from django.forms import BaseForm, ModelForm
from django.utils import timezone

from event.models import AwardType, Category, DanceMode, Event, Price, Schedule


class BaseAdminForm(BaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "event" in self.fields.keys():
            self.fields["event"].queryset = Event.objects.filter(
                end_date__gte=timezone.now().date()
            )


class AwardTypeAdminForm(BaseAdminForm, ModelForm):
    class Meta:
        model = AwardType
        fields = "__all__"


class CategoryAdminForm(BaseAdminForm, ModelForm):
    class Meta:
        model = Category
        fields = "__all__"


class DanceModeAdminForm(BaseAdminForm, ModelForm):
    class Meta:
        model = DanceMode
        fields = "__all__"


class PriceAdminForm(BaseAdminForm, ModelForm):
    class Meta:
        model = Price
        fields = "__all__"


class ScheduleAdminForm(BaseAdminForm, ModelForm):
    class Meta:
        model = Schedule
        fields = "__all__"
