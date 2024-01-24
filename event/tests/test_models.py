from datetime import date, time, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from event.models import Category, Contact, DanceMode, Event, Schedule


class ContactModelTest(TestCase):
    def test_routing_number_length(self):
        # Try to create a contact instance with invalid routing number.
        with self.assertRaises(ValidationError):
            contact = Contact(
                first_name="Contact",
                last_name="Test",
                email="email@test.com",
                phone_number="1234567890",
                bank_name="Test bank",
                account_owner="Test user",
                account_owner_id_number="12345678",
                account_type="SAVINGS",
                routing_number="123456",
                alias="Test alias",
            )
            contact.full_clean()


class ModuleBaseData(TestCase):
    def setUp(self):
        self.contact = Contact.objects.create(
            first_name="Contact",
            last_name="Test",
            email="email@test.com",
            phone_number="1234567890",
            bank_name="Test bank",
            account_owner="Test user",
            account_owner_id_number="12345678",
            account_type="SAVINGS",
            routing_number="1234567890123456789012",
            alias="Test alias",
        )
        self.test_data = {
            "name": "Test event",
            "start_date": date(2023, 1, 1),
            "end_date": date(2050, 12, 31),
            "registration_end_date": date(2050, 12, 31),
            "city": "Test city",
            "state": "Test state",
            "country": "Test country",
            "contact": self.contact,
        }
        self.event = Event.objects.create(**self.test_data)


class EventModelTest(ModuleBaseData):
    def setUp(self):
        super().setUp()

    def test_event_uniqueness(self):
        # Try to create another Event instance with the same name, start and end date.
        event = Event(**self.test_data)
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_event_start_and_end_dates(self):
        # Check that the event end date is not before its start date.
        self.event.start_date = date(2050, 12, 31)
        self.event.end_date = date(2023, 1, 1)
        with self.assertRaises(ValidationError):
            self.event.full_clean()

    def test_event_started_and_ended(self):
        # Check that the event has started or ended depending on dates.
        self.assertTrue(self.event.started)
        self.assertFalse(self.event.ended)


class CategoryModelTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(
            name="Test category",
            type=4,
            min_age=1,
            max_age=10,
            max_duration=timedelta(seconds=180),
        )
        self.event.categories.add(self.category)

    def test_category_type_display_name(self):
        # Check that the get_type_display shows the display name.
        self.assertEqual(self.category.get_type_display(), "Group")

    def test_category_max_and_min_age(self):
        # Check that the category minimum age is not greater than the maximum.
        self.category.min_age = 10
        self.category.max_age = 1
        with self.assertRaises(ValidationError):
            self.category.full_clean()


class ScheduleModelTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.dance_mode = DanceMode.objects.create(name="Test dance mode")
        self.event.dance_modes.add(self.dance_mode)
        self.schedule = Schedule.objects.create(
            event=self.event,
            dance_mode=self.dance_mode,
            date=date(2023, 6, 1),
            time=time(12),
        )

    def test_schedule_and_event_dates(self):
        # Try to change the schedule date to be lesser than the event start date.
        self.schedule.date = date(2022, 6, 1)
        with self.assertRaises(ValidationError):
            self.schedule.full_clean()

        # Try to change the schedule date to be greater than the event end date.
        self.schedule.date = date(2051, 1, 1)
        with self.assertRaises(ValidationError):
            self.schedule.full_clean()
