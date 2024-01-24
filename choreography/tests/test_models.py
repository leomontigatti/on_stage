import os
import shutil
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase

from academy.models import Academy, Dancer, Professor
from choreography.models import Choreography, Discount, Payment, Score
from event.models import AwardType, Category, Contact, DanceMode, Event, Price, Schedule

OSUser = get_user_model()


class ModuleBaseData(TestCase):
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
            birth_date=date(2000, 8, 13),
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
            "academy": self.academy,
            "event": self.event,
            "dance_mode": self.dance_mode,
            "category": self.category,
            "price": self.price,
            "schedule": self.schedule,
            "name": "Test choreography",
        }
        self.choreography = Choreography.objects.create(**self.test_data)
        self.choreography.dancers.add(self.dancer)
        self.choreography.professors.add(self.professor)


class ChoreographyModelTest(ModuleBaseData):
    def setUp(self):
        super().setUp()

    def test_choreography_upper_name(self):
        self.assertEqual(
            self.choreography.__str__(), "Test Academy | Test choreography"
        )

    def test_creation_without_academy(self):
        # Check that there is an academy instance when creating a new Choreography instance.
        self.test_data["academy"] = None
        choreography = Choreography(**self.test_data)
        with self.assertRaises(IntegrityError):
            choreography.save()

    def test_choreography_duration(self):
        # Check that the choreography duration is set by its related Category instance.
        self.assertEqual(self.choreography.duration, self.category.max_duration)

    def test_file_uploading_and_renaming(self):
        # Check that the uploaded file is renamed and uploaded to the related academy media folder.
        audio_content = b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xAC\x00\x00\x44\xAC\x00\x00\x01\x00\x10\x00data\x00\x00\x00\x00"
        test_file = SimpleUploadedFile("test_file.wav", audio_content)
        self.choreography.music_track = test_file
        self.choreography.save()
        self.assertEqual(
            self.choreography.music_track,
            "test_academy/music_track/test_choreography.wav",
        )

        # Check that the music track is renamed after the order number changed.
        self.choreography.order_number = 22
        self.choreography.save()
        self.assertEqual(
            self.choreography.music_track,
            "test_academy/music_track/00022_test_choreography.wav",
        )

        # Check that the music track is renamed after the instance name changed.
        self.choreography.order_number = None
        self.choreography.name = 'Some OTHER "test" name'
        self.choreography.save()
        self.assertEqual(
            self.choreography.music_track,
            "test_academy/music_track/some_other_test_name.wav",
        )

        # Remove the file and the created media folder.
        academy_name_snaked = self.academy.name.replace(" ", "_")
        self.choreography.music_track.delete(save=True)
        test_media_folder_path = f"{settings.MEDIA_ROOT}/{academy_name_snaked}/"
        if os.path.isdir(test_media_folder_path):
            shutil.rmtree(test_media_folder_path)
            if not any(os.scandir(settings.MEDIA_ROOT)):
                os.rmdir(settings.MEDIA_ROOT)

    def test_deposit_total_prices(self):
        self.assertEqual(self.choreography.deposit_amount, 50)
        self.assertEqual(self.choreography.total_price, 100)


class DiscountModelTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.discount = Discount.objects.create(
            choreography=self.choreography, amount=30
        )

    def test_choreography_total_price_and_deposit(self):
        # Check if a choreography total price is modified after a Discount instance is related.
        self.assertEqual(self.choreography.deposit_amount, 35)
        self.assertEqual(self.choreography.total_price, 70)


class PaymentModelTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.payment = Payment.objects.create(choreography=self.choreography, amount=50)

    def test_fully_paid_and_deposit_paid(self):
        # Check if a choreography deposit is paid when a related Payment instance amount is equal to the deposit amount.
        self.assertTrue(self.choreography.deposit_paid)
        self.assertFalse(self.choreography.fully_paid)

        # Check if a choreography is fully paid when a related Payment instance amount is equal to the total price.
        self.payment.amount = 100
        self.payment.save()
        self.assertTrue(self.choreography.fully_paid)

        # Check if a choreography is not paid when a related Payment instance is deleted.
        self.payment.delete()
        self.assertFalse(self.choreography.deposit_paid)
        self.assertFalse(self.choreography.fully_paid)


class ScoreModelTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.test_gold_award = AwardType.objects.create(
            name="Test gold award",
            min_average_score=90,
            max_average_score=100,
        )
        self.test_silver_award = AwardType.objects.create(
            name="Test silver award",
            min_average_score=70,
            max_average_score=89,
        )
        self.event.award_types.add(self.test_gold_award, self.test_silver_award)
        self.score = Score.objects.create(
            choreography=self.choreography, judge=self.user, value=90
        )

    def test_value_field_validator(self):
        # Try to change the value to an invalid one.
        self.score.value = 111
        with self.assertRaises(ValidationError):
            self.score.full_clean()

    def test_average_score_and_award_type_signal(self):
        # Check if a choreography average score and award type change when another Score instance is related.
        self.assertEqual(self.choreography.average_score, 90)
        Score.objects.create(choreography=self.choreography, judge=self.user, value=80)
        self.assertEqual(self.choreography.average_score, 85)
        award = self.choreography.awards.get(assigned_by=self.admin)
        award.refresh_from_db()
        self.assertEqual(award.award_type, self.test_silver_award)
