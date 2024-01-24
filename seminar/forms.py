from django.forms import (
    BaseInlineFormSet,
    BaseModelFormSet,
    FloatField,
    ModelForm,
    Select,
    TextInput,
    ValidationError,
    inlineformset_factory,
    modelformset_factory,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from academy.models import Dancer
from event.models import Event
from seminar.models import Seminar, SeminarPayment, SeminarRegistration


class SeminarRegistrationForm(ModelForm):
    def __init__(self, *args, academy, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["dancer"].queryset = academy.dancers.all()

        try:
            self.fields["deposit_amount"].initial = self.instance.deposit_amount
            self.fields["total_price"].initial = self.instance.total_price
            self.fields["balance"].initial = self.instance.balance
        except Dancer.DoesNotExist:
            pass

    deposit_amount = FloatField(
        required=False,
        widget=TextInput(
            attrs={"readonly": "", "class": "text-center", "size": 6, "tabindex": "-1"}
        ),
    )
    total_price = FloatField(
        required=False,
        widget=TextInput(
            attrs={"readonly": "", "class": "text-center", "size": 6, "tabindex": "-1"}
        ),
    )
    balance = FloatField(
        required=False,
        widget=TextInput(
            attrs={"readonly": "", "class": "text-center", "size": 6, "tabindex": "-1"}
        ),
    )

    class Meta:
        model = SeminarRegistration
        exclude = ["academy", "seminar"]
        widgets = {
            "dancer": Select(
                attrs={
                    "class": "form-select",
                },
            ),
        }


class RegistrationBaseFormSet(BaseModelFormSet):
    def clean(self):
        if any(self.errors):
            return

        dancers = []
        for form in self.forms:
            dancer = form.cleaned_data.get("dancer")
            if dancer in dancers:
                raise ValidationError(
                    _("The selected dancer is already registered in this seminar.")
                )
            dancers.append(dancer)


SeminarRegistrationFormSet = modelformset_factory(
    SeminarRegistration,
    SeminarRegistrationForm,
    formset=RegistrationBaseFormSet,
    extra=0,
    min_num=1,
)


class SeminarAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "event" in self.fields.keys():
            self.fields["event"].queryset = Event.objects.filter(
                end_date__gte=timezone.now().date()
            )

    class Meta:
        model = Seminar
        fields = "__all__"


class SeminarPaymentAdminForm(ModelForm):
    class Meta:
        model = SeminarPayment
        fields = "__all__"

    def clean(self):
        if any(self.errors):
            return

        amount = self.cleaned_data.get("amount")
        seminar_registration = self.cleaned_data.get("seminar_registration")
        if not seminar_registration:
            seminar_registration = self.instance.seminar_registration

        # Check that the payment amount is not greater than the seminar registration total price.
        paid_amount = 0
        for payment in seminar_registration.seminar_payments.exclude(
            pk=self.instance.pk
        ):
            paid_amount += payment.amount
        total_amount = paid_amount + amount

        if total_amount > seminar_registration.total_price:
            raise ValidationError(
                {
                    "amount": ValidationError(
                        _(
                            "The payments total amount cannot be greater than the seminar registration total price."
                        ),
                        code="invalid",
                    )
                }
            )


class SeminarPaymentBaseFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return

        # Check that the payments total amount is not greater than the seminar registration total price.
        total_amount = 0
        for form in self.forms:
            total_amount += form.cleaned_data.get("amount")

        if total_amount > self.instance.total_price:
            raise ValidationError(
                _(
                    "The payments total amount cannot be greater than the seminar registration total price."
                ),
                code="invalid",
            )


SeminarPaymentFormSet = inlineformset_factory(
    SeminarRegistration,
    SeminarPayment,
    formset=SeminarPaymentBaseFormSet,
    fields="__all__",
)
