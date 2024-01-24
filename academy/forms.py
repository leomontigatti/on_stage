from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MinLengthValidator
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

from academy.models import Academy, Dancer, Professor, numeric_string_validator

OSUser = get_user_model()


def add_class_to_label(original_function):
    """Modify required form fields HTML attributes."""

    def class_to_label_tag(self, *args, **kwargs):
        required_field = {"class": "fw-bold"}
        attrs = required_field if self.field.required else {}
        return original_function(self, attrs=attrs, label_suffix="")

    return class_to_label_tag


forms.BoundField.label_tag = add_class_to_label(forms.BoundField.label_tag)


class OSUserRegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    class Meta:
        model = OSUser
        fields = ["email", "first_name", "last_name", "password1", "password2"]

    academy_name = forms.CharField(
        max_length=50,
        label=_("Academy name"),
    )
    phone_number = forms.CharField(
        max_length=10,
        label=_("Phone number"),
        validators=[MinLengthValidator(10), numeric_string_validator],
    )
    city = forms.CharField(max_length=100, label=_("City"))
    state = forms.CharField(max_length=100, label=_("State"))
    terms = forms.BooleanField(label=_("Terms and conditions"))

    def clean(self):
        super().clean()
        academy_name = self.cleaned_data.get("academy_name")

        # Check academy name is unique.
        if Academy.objects.filter(name=academy_name.lower()).exists():
            raise ValidationError(
                {
                    "academy_name": ValidationError(
                        _(
                            "There already is a registered academy with this name: %(value)s."
                        ),
                        code="invalid",
                        params={"value": academy_name},
                    )
                }
            )


class DancerForm(forms.ModelForm):
    """
    ModelForm for creating and updating a :model:`academy.Dancer` instance.
    """

    class Meta:
        model = Dancer
        exclude = ["academy"]
        widgets = {
            "birth_date": forms.DateInput(
                format=("%Y-%m-%d"),
                attrs={
                    "class": "form-control rounded-end",
                    "type": "date",
                },
            ),
        }

    def clean(self):
        super().clean()
        identification_type = self.cleaned_data.get("identification_type")
        identification_number = self.cleaned_data.get("identification_number")

        # Check identification_type and identification_number length.
        if all(
            [identification_type, identification_type == "ID", identification_number]
        ):
            if any(
                [len(identification_number) != 8, not identification_number.isnumeric()]
            ):
                raise ValidationError(
                    {
                        "identification_number": ValidationError(
                            _("ID must have 8 numeric characters.")
                        ),
                    }
                )


class ProfessorForm(forms.ModelForm):
    """
    ModelForm for creating and updating a :model:`academy.Professor` instance.
    """

    class Meta:
        model = Professor
        exclude = ["academy"]

    def clean(self):
        super().clean()
        identification_type = self.cleaned_data.get("identification_type")
        identification_number = self.cleaned_data.get("identification_number")

        # Check identification_type and identification_number length.
        if all(
            [identification_type, identification_type == "ID", identification_number]
        ):
            if any(
                [len(identification_number) != 8, not identification_number.isnumeric()]
            ):
                raise ValidationError(
                    {
                        "identification_number": ValidationError(
                            _("ID must have 8 numeric characters.")
                        ),
                    }
                )
