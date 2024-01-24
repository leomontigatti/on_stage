from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from academy.forms import DancerForm, OSUserRegistrationForm, ProfessorForm

OSUser = get_user_model()


class DancerFormTest(TestCase):
    def setUp(self):
        self.test_data = {
            "first_name": "test",
            "last_name": "dancer",
            "birth_date": date(2000, 8, 13),
            "identification_type": "ID",
            "identification_number": "12345678",
        }

    def test_identification_number_length_when_ID(self):
        # Check that the identification_number is 8 characters long when identification_type is 'ID'.
        self.test_data["identification_number"] = "12345"
        form = DancerForm(data=self.test_data)
        self.assertFormError(
            form=form,
            field="identification_number",
            errors="ID must have 8 numeric characters.",
        )

    def test_identification_number_isnumeric_when_ID(self):
        # Check that identification_number has only numeric characters when identification_type is 'ID'.
        self.test_data["identification_number"] = "1234567a"
        form = DancerForm(data=self.test_data)
        self.assertFormError(
            form=form,
            field="identification_number",
            errors="ID must have 8 numeric characters.",
        )


class ProfessorFormTest(TestCase):
    def setUp(self):
        self.test_data = {
            "first_name": "test",
            "last_name": "professor",
            "identification_type": "ID",
            "identification_number": "12345678",
        }

    def test_identification_number_length_when_ID(self):
        # Check that the identification_number is 8 characters long when identification_type is 'ID'.
        self.test_data["identification_number"] = "12345"
        form = ProfessorForm(data=self.test_data)
        self.assertFormError(
            form=form,
            field="identification_number",
            errors="ID must have 8 numeric characters.",
        )

    def test_identification_number_isnumeric_when_ID(self):
        # Check that identification_number has only numeric characters when identification_type is 'ID'.
        self.test_data["identification_number"] = "1234567a"
        form = ProfessorForm(data=self.test_data)
        self.assertFormError(
            form=form,
            field="identification_number",
            errors="ID must have 8 numeric characters.",
        )


class OSUserRegistrationFormTest(TestCase):
    def setUp(self):
        self.test_data = {
            "email": "user@test.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "123456",
            "password2": "123456",
            "academy_name": "Test academy",
            "phone_number": "12345678",
            "city": "Test city",
            "state": "Test state",
            "terms": True,
        }

    def test_required_field(self):
        # Check that an empty required field adds an error to the form.
        self.test_data["first_name"] = None
        form = OSUserRegistrationForm(data=self.test_data)
        self.assertFormError(
            form=form,
            field="first_name",
            errors="This field is required.",
        )

    def test_user_unique_email(self):
        # Try to create another user instance with the same email.
        OSUser.objects.create_user(email="user@test.com", password="123456")
        form = OSUserRegistrationForm(data=self.test_data)
        self.assertFormError(
            form=form,
            field="email",
            errors="User with this Email address already exists.",
        )
