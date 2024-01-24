from django.contrib.auth import get_user_model
from django.forms import (
    BaseInlineFormSet,
    CheckboxSelectMultiple,
    ModelForm,
    ValidationError,
    inlineformset_factory,
)
from django.utils.translation import gettext_lazy as _

from choreography.models import Award, Choreography, Discount, Payment, Score
from event.models import AwardType, Category, DanceMode, Schedule

OSUser = get_user_model()


class ChoreographyForm(ModelForm):
    """
    ModelForm for creating and updating a :model:`choreography.Choreography` instance.
    """

    def __init__(self, *args, academy, event, **kwargs):
        super().__init__(*args, **kwargs)
        self.academy = academy
        self.event = event

        for field in ["category", "dance_mode", "professors", "dancers"]:
            if self.instance.is_locked:
                self.fields[field].disabled = True

        self.fields["category"].queryset = Category.objects.filter(event=self.event)
        self.fields["dance_mode"].queryset = DanceMode.objects.filter(event=self.event)
        self.fields["professors"].queryset = self.academy.professors.all()
        self.fields["dancers"].queryset = self.academy.dancers.all().order_by(
            "-birth_date"
        )

    class Meta:
        model = Choreography
        fields = [
            "dance_mode",
            "category",
            "dancers",
            "professors",
            "name",
            "music_track",
        ]
        widgets = {
            "dancers": CheckboxSelectMultiple(),
            "professors": CheckboxSelectMultiple(),
        }

    def clean(self):
        super().clean()
        category = self.cleaned_data.get("category")
        dance_mode = self.cleaned_data.get("dance_mode")

        try:
            schedule = Schedule.objects.filter(
                event=self.event, dance_mode=dance_mode
            ).first()

            selected_dancers = self.cleaned_data.get("dancers")
            ages_list, over_age = [], 0

            # Check selected dancers amount according to the selected category.
            if (
                (category.type == 1 and not selected_dancers.count() == 1)
                or (category.type == 2 and not selected_dancers.count() == 2)
                or (category.type == 3 and not selected_dancers.count() == 3)
                or (category.type == 4 and not selected_dancers.count() >= 4)
            ):
                raise ValidationError(
                    {
                        "category": ValidationError(
                            _(
                                "The selected dancers amount does not match the selected category: %(value)s."
                            ),
                            code="invalid",
                            params={"value": category.get_type_display()},
                        )
                    }
                )

            # Check selected dancers age at the beginning of the related schedule.
            for dancer in selected_dancers:
                dancer_age = (
                    schedule.date.year
                    - dancer.birth_date.year
                    - (
                        (schedule.date.month, schedule.date.day)
                        < (dancer.birth_date.month, dancer.birth_date.day)
                    )
                )
                ages_list.append(dancer_age)
                if dancer_age > category.max_age:
                    over_age += 1

            # Check selected dancers average age according to the selected category.
            if category.type in [3, 4]:
                round_average = round(sum(ages_list) / len(ages_list))
                if len(ages_list) * 0.2 < over_age:
                    raise ValidationError(
                        {
                            "category": ValidationError(
                                _(
                                    "The group can only have up to 20 percent of its dancers older than the category maximum age: %(value)s."
                                ),
                                code="invalid",
                                params={"value": category.max_age},
                            )
                        }
                    )
                elif round_average > category.max_age:
                    raise ValidationError(
                        {
                            "category": ValidationError(
                                _(
                                    "The group average age is greater than the category maximum age: %(value)s."
                                ),
                                code="invalid",
                                params={"value": category.max_age},
                            )
                        }
                    )
            else:
                if over_age:
                    raise ValidationError(
                        {
                            "category": ValidationError(
                                _(
                                    "Some of the selected dancers is older than the category maximum age: %(value)s."
                                ),
                                code="invalid",
                                params={"value": category.max_age},
                            )
                        }
                    )
        except AttributeError:
            # Means that some required field was not filled and Django will show the form error.
            pass


class AwardAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self.instance, "choreography"):
            event = self.instance.choreography.event
            self.fields["award_type"].queryset = AwardType.objects.filter(event=event)

    class Meta:
        model = Award
        fields = "__all__"

    def clean(self):
        if any(self.errors):
            return

        choreography = self.cleaned_data.get("choreography")
        if not choreography:
            choreography = self.instance.choreography

        if choreography.awards.filter(assigned_by_id=1).exists():
            raise ValidationError(
                {
                    "assigned_by": ValidationError(
                        _(
                            "The selected choreography already has an award assigned by the System."
                        ),
                        code="invalid",
                    )
                }
            )


class AwardInlineForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self.instance, "assigned_by") and self.instance.assigned_by_id == 1:
            for field in self.fields:
                self.fields[field].disabled = True

    class Meta:
        model = Award
        fields = ["assigned_by", "award_type"]


class AwardBaseFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return

        # Check that there is only one award assigned by the System.
        system_awards = 0
        for form in self.forms:
            assigned_by = form.cleaned_data.get("assigned_by")
            if assigned_by.id == 1:
                system_awards += 1

        if system_awards > 1:
            raise ValidationError(
                _(
                    "You don't have permissions to create an award assigned by the System."
                ),
                code="invalid",
            )


AwardFormSet = inlineformset_factory(
    Choreography, Award, AwardInlineForm, AwardBaseFormSet
)


class DiscountAdminForm(ModelForm):
    class Meta:
        model = Discount
        fields = "__all__"

    def clean(self):
        if any(self.errors):
            return

        amount = self.cleaned_data.get("amount")
        choreography = self.cleaned_data.get("choreography")
        if not choreography:
            choreography = self.instance.choreography

        # Check that the discount amount is not greater than the choreography balance.
        discounted_amount = 0
        for discount in choreography.discounts.exclude(pk=self.instance.pk):
            discounted_amount += discount.amount
        amount = self.cleaned_data.get("amount")
        total_amount = discounted_amount + amount

        if total_amount > choreography.balance_without_discounts:
            raise ValidationError(
                {
                    "amount": ValidationError(
                        _(
                            "The discounts total amount cannot be greater than the choreography balance."
                        ),
                        code="invalid",
                    )
                }
            )


class DiscountBaseFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return

        # Check that the discounts total amount is not greater than the choreography balance.
        total_amount = 0
        for form in self.forms:
            total_amount += form.cleaned_data.get("amount")

        if total_amount > self.instance.balance_without_discounts:
            raise ValidationError(
                _(
                    "The discounts total amount cannot be greater than the choreography balance."
                ),
                code="invalid",
            )


DiscountFormSet = inlineformset_factory(
    Choreography, Discount, formset=DiscountBaseFormSet, fields="__all__"
)


class PaymentAdminForm(ModelForm):
    class Meta:
        model = Payment
        fields = "__all__"

    def clean(self):
        if any(self.errors):
            return

        amount = self.cleaned_data.get("amount")
        choreography = self.cleaned_data.get("choreography")
        if not choreography:
            choreography = self.instance.choreography

        # Check that the payment amount is not greater than the choreography total price.
        paid_amount = 0
        for payment in choreography.payments.exclude(pk=self.instance.pk):
            paid_amount += payment.amount
        total_amount = paid_amount + amount

        if total_amount > choreography.total_price:
            raise ValidationError(
                {
                    "amount": ValidationError(
                        _(
                            "The payments total amount cannot be greater than the choreography total price."
                        ),
                        code="invalid",
                    )
                }
            )


class PaymentBaseFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return

        # Check that the payments total amount is not greater than the choreography total price.
        total_amount = 0
        for form in self.forms:
            total_amount += form.cleaned_data.get("amount")

        if total_amount > self.instance.total_price:
            raise ValidationError(
                _(
                    "The payments total amount cannot be greater than the choreography total price."
                ),
                code="invalid",
            )


PaymentFormSet = inlineformset_factory(
    Choreography, Payment, formset=PaymentBaseFormSet, fields="__all__"
)


class ScoreInlineForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["judge"].disabled = True
        self.fields["value"].disabled = True

    class Meta:
        model = Score
        fields = ["judge", "value", "is_locked"]
