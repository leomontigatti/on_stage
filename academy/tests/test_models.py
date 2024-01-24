import os
import shutil
from datetime import date
from unittest.mock import Mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase

from academy.models import Academy, Dancer, Professor

OSUser = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = OSUser.objects.create_user(
            email="user@test.com",
            password="123456",
            first_name="Test",
            last_name="User",
        )

    def test_user_full_name(self):
        # Check that it is showing the user's first and last name if exist.
        self.assertEqual(self.user.__str__(), "Test User")


class ModuleBaseData(TestCase):
    def setUp(self):
        self.user = OSUser.objects.create_user(email="user@test.com", password="123456")
        self.academy = Academy.objects.create(
            user=self.user,
            name="Test academy",
            phone_number="12345678",
            city="Test city",
            state="Test state",
        )


class AcademyModelTest(ModuleBaseData):
    def setUp(self):
        super().setUp()

    def test_lowercase_name(self):
        # Check that the name is automatically converted to lowercase.
        self.assertEqual(self.academy.name, "test academy")

    def test_duplicate_name(self):
        # Try to create a new Academy instance with the same name.
        academy2 = Academy(
            user=self.user,
            name="Test academy",
            phone_number="12345678",
            city="Test city",
            state="Test state",
        )
        with self.assertRaises(ValidationError):
            academy2.full_clean()

    def test_phone_number_length_and_type(self):
        # Try to add a longer phone number.
        self.academy.phone_number = "123456789"
        with self.assertRaises(ValidationError):
            self.academy.full_clean()

        # Try to add a phone number with a letter in it.
        self.academy.phone_number = "1234a567"
        with self.assertRaises(ValidationError):
            self.academy.full_clean()


class DancerModelTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.test_data = {
            "academy": self.academy,
            "first_name": "test",
            "last_name": "dancer",
            "birth_date": date(2000, 8, 1),
            "identification_type": "ID",
            "identification_number": "12345678",
        }
        self.dancer = Dancer.objects.create(**self.test_data)

    def test_creation_without_academy(self):
        # Check that there is an academy instance when creating a new Dancer instance.
        self.test_data["academy"] = None
        dancer = Dancer(**self.test_data)
        with self.assertRaises(IntegrityError):
            dancer.save()

    def test_capitalize_name(self):
        # Check that the first and last name initials are automatically converted to capital.
        self.assertEqual(self.dancer.__str__(), "Dancer, Test")

    def test_dancer_age(self):
        # Check that the age calculation is correct.
        self.assertEqual(self.dancer.age, 23)

    def test_max_file_size(self):
        # Try to upload a file larger than the max allowed.
        test_file = Mock(size=10485761)
        self.dancer.identification_front_image = test_file
        with self.assertRaises(ValidationError):
            self.dancer.full_clean()

    def test_uploaded_file_renaming_and_location(self):
        # Check that the uploaded file is renamed and uploaded to the related academy media folder.
        image_content = b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00"
        test_file = SimpleUploadedFile("test_file.gif", image_content)
        academy_name_snaked = self.academy.name.replace(" ", "_")
        self.dancer.identification_front_image = test_file
        self.dancer.save()
        self.assertEqual(
            self.dancer.identification_front_image.name,
            f"{academy_name_snaked}/Dancer/{self.dancer.identification_number}_front.gif",
        )

        # Remove the file and the created media folder.
        self.dancer.identification_front_image.delete(save=True)
        test_media_folder_path = f"{settings.MEDIA_ROOT}/{academy_name_snaked}/"
        if os.path.isdir(test_media_folder_path):
            shutil.rmtree(test_media_folder_path)
            if not any(os.scandir(settings.MEDIA_ROOT)):
                os.rmdir(settings.MEDIA_ROOT)

    def test_dancer_uniqueness(self):
        # Try to create another Dancer instance with the same Academy, identification type and number.
        dancer = Dancer(**self.test_data)
        with self.assertRaises(ValidationError):
            dancer.full_clean()


class ProfessorModelTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.test_data = {
            "academy": self.academy,
            "first_name": "test",
            "last_name": "professor",
            "identification_type": "ID",
            "identification_number": "12345678",
        }
        self.professor = Professor.objects.create(**self.test_data)

    def test_creation_without_academy(self):
        # Check that there is an academy instance when creating a new Professor instance.
        self.test_data["academy"] = None
        professor = Professor(**self.test_data)
        with self.assertRaises(IntegrityError):
            professor.save()

    def test_capitalize_name(self):
        # Check that the first and last name initials are automatically converted to capital.
        self.assertEqual(self.professor.__str__(), "Professor, Test")

    def test_max_file_size(self):
        # Try to upload a file larger than the max allowed.
        uploaded_file = Mock(size=10485761)
        self.professor.identification_back_image = uploaded_file
        with self.assertRaises(ValidationError):
            self.professor.full_clean()

    def test_uploaded_file_renaming_and_location(self):
        # Check that the uploaded file is renamed and uploaded to the related academy media folder.
        image_content = b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00"
        test_file = SimpleUploadedFile("test_file.gif", image_content)
        academy_name_snaked = self.academy.name.replace(" ", "_")
        self.professor.identification_front_image = test_file
        self.professor.save()
        self.assertEqual(
            self.professor.identification_front_image.name,
            f"{academy_name_snaked}/Professor/{self.professor.identification_number}_front.gif",
        )

        # Remove the file and the created media folder.
        self.professor.identification_front_image.delete(save=True)
        test_media_folder_path = f"{settings.MEDIA_ROOT}/{academy_name_snaked}/"
        if os.path.isdir(test_media_folder_path):
            shutil.rmtree(test_media_folder_path)
            if not any(os.scandir(settings.MEDIA_ROOT)):
                os.rmdir(settings.MEDIA_ROOT)

    def test_professor_uniqueness(self):
        # Try to create another professor with the same Academy, identification type and number.
        professor = Professor(**self.test_data)
        with self.assertRaises(ValidationError):
            professor.full_clean()
