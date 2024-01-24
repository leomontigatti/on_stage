from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from academy.models import Academy, Dancer, Professor
from choreography.forms import ChoreographyForm
from event.models import Category, Contact, DanceMode, Event, Price, Schedule

OSUser = get_user_model()


class ChoreographyFormTest(TestCase):
    def setUp(self):
        self.admin = OSUser.objects.create_user(
            email="admin@test.com", password="123456", is_staff=True, is_superuser=True
        )
        self.user = OSUser.objects.create_user(email="user@test.com", password="123456")
        self.academy = Academy.objects.create(
            user=self.user,
            name="Test academy",
            phone_number="12345678",
            city="Test city",
            state="Test state",
        )
        self.contact = Contact.objects.create(
            first_name="Contact",
            last_name="Test",
            email="contact@test.com",
            phone_number="1234567890",
            bank_name="Test bank",
            account_owner="Test user",
            account_owner_id_number="12345678",
            account_type="SAVINGS",
            routing_number="123456",
            alias="Test alias",
        )
        self.event = Event.objects.create(
            name="Test event",
            start_date=date(2023, 1, 1),
            end_date=date(2050, 12, 31),
            registration_end_date=date(2050, 12, 31),
            city="Test city",
            state="Test state",
            country="Test country",
            contact=self.contact,
        )
        self.dance_mode = DanceMode.objects.create(name="Test dance mode")
        self.event.dance_modes.add(self.dance_mode)
        self.category = Category.objects.create(
            name="Test category",
            type=1,
            min_age=1,
            max_age=10,
            max_duration=timedelta(seconds=180),
        )
        self.event.categories.add(self.category)
        self.price = Price.objects.create(
            event=self.event,
            name="Test price",
            category_type=1,
            amount=100,
            due_date=self.event.end_date,
        )
        self.schedule = Schedule.objects.create(
            event=self.event, dance_mode=self.dance_mode
        )
        self.dancer = Dancer.objects.create(
            academy=self.academy,
            first_name="test",
            last_name="dancer",
            birth_date=date(2014, 8, 13),
            identification_type="ID",
            identification_number="12345678",
        )
        self.professor = Professor.objects.create(
            academy=self.academy,
            first_name="test",
            last_name="professor",
            identification_type="ID",
            identification_number="12345678",
        )
        self.test_data = {
            "dance_mode": self.dance_mode,
            "category": self.category,
            "dancers": [self.dancer],
            "professors": [self.professor],
            "name": "Test choreography",
        }

    def test_form_with_valid_data(self):
        # Try to create a Choreography instance with valid information.
        form = ChoreographyForm(
            academy=self.academy, event=self.event, data=self.test_data
        )
        self.assertTrue(form.is_valid())

    def test_form_without_required_data(self):
        # Try to create a Choreography instance without required fields.
        self.test_data["dance_mode"] = None
        self.test_data["category"] = None
        form = ChoreographyForm(
            academy=self.academy, event=self.event, data=self.test_data
        )
        self.assertFormError(
            form=form, field="dance_mode", errors="This field is required."
        )
        self.assertFormError(
            form=form, field="category", errors="This field is required."
        )

    def test_selected_dancers_amount(self):
        # Try to select more dancers than the selected category type.
        dancer = Dancer.objects.create(
            academy=self.academy,
            first_name="test",
            last_name="dancer",
            birth_date=date(2000, 8, 13),
            identification_type="ID",
            identification_number="12345679",
        )
        self.test_data["dancers"].append(dancer)
        form = ChoreographyForm(
            academy=self.academy, event=self.event, data=self.test_data
        )
        self.assertFormError(
            form=form,
            field="category",
            errors="The selected dancers amount does not match the selected category: Solo.",
        )

        # Try to select less dancers than the selected category type.
        trio_category = Category.objects.create(
            name="Test trio category",
            type=3,
            min_age=20,
            max_age=25,
            max_duration=timedelta(seconds=180),
        )
        self.event.categories.add(trio_category)
        self.test_data["category"] = trio_category
        form = ChoreographyForm(
            academy=self.academy, event=self.event, data=self.test_data
        )
        self.assertFormError(
            form=form,
            field="category",
            errors="The selected dancers amount does not match the selected category: Trio.",
        )

    def test_selected_dancers_age(self):
        # Try to add older dancers than the category max age and above the 20 percent of total dancers.
        dancers_list = [
            Dancer.objects.create(
                academy=self.academy,
                first_name="test",
                last_name=f"dancer{i}",
                birth_date=date(1990, 8, 13),
                identification_type="ID",
                identification_number=f"1234567{i}",
            )
            for i in range(4)
        ]
        for dancer in dancers_list:
            self.test_data["dancers"].append(dancer)

        group_category = Category.objects.create(
            name="Test group category",
            type=4,
            min_age=20,
            max_age=25,
            max_duration=timedelta(seconds=180),
        )
        self.event.categories.add(group_category)
        self.test_data["category"] = group_category
        form = ChoreographyForm(
            academy=self.academy, event=self.event, data=self.test_data
        )
        self.assertFormError(
            form=form,
            field="category",
            errors="The group can only have up to 20 percent of its dancers older than the category maximum age: 25.",
        )

        # Try to add an older dancer who raises the average age above the category max age.
        group_category.max_age = 35
        group_category.save()
        self.dancer.birth_date = date(1975, 8, 13)
        self.dancer.save()
        form = ChoreographyForm(
            academy=self.academy, event=self.event, data=self.test_data
        )
        self.assertFormError(
            form=form,
            field="category",
            errors="The group average age is greater than the category maximum age: 35.",
        )

        # Try to add a dancer older than the category max age.
        dancer = Dancer.objects.create(
            academy=self.academy,
            first_name="test",
            last_name="dancer",
            birth_date=date(1990, 8, 13),
            identification_type="ID",
            identification_number="12345679",
        )
        self.test_data["dancers"] = [dancer]
        self.test_data["category"] = self.category
        form = ChoreographyForm(
            academy=self.academy, event=self.event, data=self.test_data
        )
        self.assertFormError(
            form=form,
            field="category",
            errors="Some of the selected dancers is older than the category maximum age: 10.",
        )
