import os
import shutil
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.test import TestCase, TransactionTestCase
from django.urls import reverse, reverse_lazy

from academy.forms import DancerForm, ProfessorForm
from academy.models import Academy, Dancer, Professor

OSUser = get_user_model()


class HomeViewTest(TestCase):
    def setUp(self):
        self.user = OSUser.objects.create_user(
            email="user@test.com", password="123456", is_staff=True
        )
        self.path = reverse("home")

    def test_user_redirection_if_admin(self):
        # Check that the user is redirected to the admin index page when it belongs to the 'Admin' group.
        admin_group = Group.objects.create(name="Admin")
        self.user.groups.add(admin_group)
        self.client.login(email="user@test.com", password="123456")
        response = self.client.get(self.path)
        expected_url = reverse_lazy("admin:index")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url)

    def test_user_redirection_if_judge(self):
        # Check that the user is redirected to the 'score_list' page when it belongs to the 'Judge' group.
        self.user.groups.clear()
        judge_group = Group.objects.create(name="Judge")
        self.user.groups.add(judge_group)
        self.client.login(email="user@test.com", password="123456")
        response = self.client.get(self.path)
        expected_url = reverse("event_list", kwargs={"sender": "score"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url)

    def test_user_redirection_if_soundman(self):
        # Check that the user is redirected to the 'music_list' page when it belongs to the 'Soundman' group.
        self.user.groups.clear()
        soundman_group = Group.objects.create(name="Soundman")
        self.user.groups.add(soundman_group)
        self.client.login(email="user@test.com", password="123456")
        response = self.client.get(self.path)
        expected_url = reverse("event_list", kwargs={"sender": "music"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url)

    def test_message_if_user_has_no_academy(self):
        # Check that a message is shown when a logged-in user is not related to an Academy.
        self.user.groups.clear()
        self.user.is_staff = False
        self.user.save()
        self.client.login(email="user@test.com", password="123456")
        response = self.client.get(self.path)
        expected_url = reverse_lazy("login")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(
            "The logged user does not have a related academy. Try another one or contact us.",
            messages,
        )

    def test_template_rendering_if_user_has_academy(self):
        # Check that the correct template is being used when a logged-in user is related to an Academy.
        Academy.objects.create(
            user=self.user,
            name="Test academy",
            phone_number="12345678",
            city="Test city",
            state="Test state",
        )
        self.client.login(email="user@test.com", password="123456")
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")


class ModuleBaseData(TestCase):
    def setUp(self):
        self.user = OSUser.objects.create_user(email="user@test.com", password="123456")
        self.academy = Academy.objects.create(user=self.user, name="Test academy")


class DancerListViewTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.dancers_list = [
            Dancer(
                academy=self.academy,
                first_name="test",
                last_name=f"dancer {i}",
                birth_date=date(2000, 8, 13),
                identification_type="ID",
                identification_number=f"12345678{i}",
            )
            for i in range(15)
        ]
        Dancer.objects.bulk_create(self.dancers_list)

        self.client.login(email="user@test.com", password="123456")
        self.path = reverse("dancer_list")

    def test_get_dancer_list_view(self):
        # Check that the page object is showing 10 items per page.
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("dancer_list.html")

        page_obj = response.context.get("page_obj")
        paginator = page_obj.paginator
        self.assertEqual(paginator.num_pages, 2)

        second_page = paginator.get_page(2)
        self.assertEqual(second_page.start_index(), 11)

    def test_academy_related_dancers_queryset(self):
        # Check that the shown Dancer instances are related to the logged-in user's Academy.
        response = self.client.get(self.path)

        page_obj = response.context.get("page_obj")
        response_qs = page_obj.object_list
        test_qs = Dancer.objects.all()[:10]
        self.assertEqual(response_qs, list(test_qs))

    def test_search_input_filter(self):
        # Check that the search input value filters the queryset properly.
        get_params = {"search_input": "dancer 1"}
        response = self.client.get(self.path, get_params)

        dancers_qs = Dancer.objects.filter(
            Q(identification_number__icontains="dancer 1")
            | Q(first_name__icontains="dancer 1")
            | Q(last_name__icontains="dancer 1")
        )
        page_obj = response.context.get("page_obj")
        response_qs = page_obj.object_list
        self.assertEqual(response_qs, list(dancers_qs))


class DancerCreateViewTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.test_data = {
            "first_name": "test",
            "last_name": "dancer",
            "birth_date": "2000-8-13",
            "identification_type": "ID",
            "identification_number": "12345678",
        }

        self.path = reverse("dancer_create")
        self.client.login(email="user@test.com", password="123456")

    def test_get_dancer_create_view(self):
        # Check that the response status code is 200, the template used and the form instance are correct.
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("dancer_form.html")

        form = response.context.get("form")
        self.assertIsInstance(form, DancerForm)

    def test_dancer_creation_with_image_upload(self):
        # Create a mock image for sending in the request.
        image_content = b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00"
        self.test_data["identification_front_image"] = SimpleUploadedFile(
            "test_file.gif", image_content
        )

        # Try to create a Dancer instance through a POST request.
        response = self.client.post(self.path, self.test_data, follow=True)
        expected_url = reverse("dancer_list")
        self.assertRedirects(response, expected_url)
        self.assertContains(response, "Successfully added a new dancer!")
        self.assertEqual(Dancer.objects.count(), 1)

        # Remove the file and the created media folder.
        academy_name_snaked = self.academy.name.replace(" ", "_")
        dancer = Dancer.objects.get(pk=1)
        dancer.identification_front_image.delete(save=True)
        test_media_folder_path = f"{settings.MEDIA_ROOT}/{academy_name_snaked}/"
        if os.path.isdir(test_media_folder_path):
            shutil.rmtree(test_media_folder_path)
            if not any(os.scandir(settings.MEDIA_ROOT)):
                os.rmdir(settings.MEDIA_ROOT)

    def test_dancer_creation_without_required_data(self):
        # Try to create a Dancer instance with missing information.
        self.test_data["identification_number"] = ""
        response = self.client.post(self.path, self.test_data)
        self.assertContains(response, "This field is required.")


class DancerCreateTransactionTest(TransactionTestCase):
    def setUp(self):
        self.test_data = {
            "first_name": "test",
            "last_name": "dancer",
            "birth_date": "2000-8-13",
            "identification_type": "ID",
            "identification_number": "12345678",
        }

        self.path = reverse("dancer_create")

    def test_unique_constraint_integrity_error(self):
        # Try to create a Dancer instance with duplicated identification_type, number and academy.
        user = OSUser.objects.create_user(email="user@test.com", password="123456")
        academy = Academy.objects.create(user=user, name="Test academy")
        Dancer.objects.create(academy=academy, **self.test_data)

        self.client.login(email="user@test.com", password="123456")

        response = self.client.post(self.path, self.test_data, follow=True)
        expected_url = reverse("dancer_list")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(
            "A dancer with that identification type and number already exists.",
            messages,
        )
        self.assertEqual(Dancer.objects.count(), 1)


class DancerUpdateViewTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.test_data = {
            "first_name": "test",
            "last_name": "dancer",
            "birth_date": "2000-8-13",
            "identification_type": "ID",
            "identification_number": "12345678",
        }
        self.dancer = Dancer.objects.create(academy=self.academy, **self.test_data)

        self.client.login(email="user@test.com", password="123456")

    def test_get_dancer_update_view(self):
        # Check that the response status code is 200, the template used and the form instance are correct.
        response = self.client.get(self.dancer.get_update_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("dancer_form.html")

        object = response.context.get("object")
        self.assertIsInstance(object, Dancer)

        form = response.context.get("form")
        self.assertIsInstance(form, DancerForm)

    def test_get_nonexisting_dancer(self):
        # Check that the response status code is 404 when trying to access an unexistent instance information.
        path = reverse("dancer_update", kwargs={"dancer_pk": 88})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed("404.html")

    def test_user_get_verified_dancer(self):
        # Check that the user cannot access a verified Dancer instance.
        self.dancer.is_verified = True
        self.dancer.save()

        response = self.client.get(self.dancer.get_update_url(), follow=True)
        expected_url = reverse("home")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("You don't have permissions to perform this action.", messages)

    def test_user_get_unrelated_dancer(self):
        # Check that the logged-in user cannot access a non-related Dancer instance.
        user = OSUser.objects.create_user(email="user2@test.com", password="123456")
        academy = Academy.objects.create(user=user, name="Test academy2")
        dancer = Dancer.objects.create(academy=academy, **self.test_data)

        response = self.client.get(dancer.get_update_url(), follow=True)
        expected_url = reverse("home")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("You don't have permissions to perform this action.", messages)

    def test_dancer_update_without_required_data(self):
        # Try to update a Dancer instance with missing information.
        self.test_data["identification_number"] = ""
        response = self.client.post(
            self.dancer.get_update_url(), self.test_data, follow=True
        )
        self.assertContains(response, "This field is required.")

    def test_dancer_update(self):
        # Check that the Dancer instance is being updated.
        self.test_data["identification_number"] = "87654321"
        response = self.client.post(
            self.dancer.get_update_url(), self.test_data, follow=True
        )
        expected_url = reverse("dancer_list")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Successfully updated the dancer information!", messages)
        self.assertEqual(Dancer.objects.count(), 1)


class DancerUpdateTransactionTest(TransactionTestCase):
    def setUp(self):
        self.test_data = {
            "first_name": "test",
            "last_name": "dancer",
            "birth_date": "2000-8-13",
            "identification_type": "ID",
            "identification_number": "12345678",
        }

    def test_unique_constraint_integrity_error(self):
        # Try to update a Dancer instance with duplicated identification_type, number and academy.
        user = OSUser.objects.create_user(email="user@test.com", password="123456")
        academy = Academy.objects.create(user=user, name="Test academy")
        Dancer.objects.create(academy=academy, **self.test_data)
        self.test_data["identification_type"] = "PASSPORT"
        dancer2 = Dancer.objects.create(academy=academy, **self.test_data)

        self.client.login(email="user@test.com", password="123456")

        self.test_data["identification_type"] = "ID"
        response = self.client.post(
            dancer2.get_update_url(), self.test_data, follow=True
        )
        expected_url = reverse("dancer_list")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(
            "A dancer with that identification type and number already exists.",
            messages,
        )


class DancerDetailViewTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.test_data = {
            "first_name": "test",
            "last_name": "dancer",
            "birth_date": "2000-8-13",
            "identification_type": "ID",
            "identification_number": "12345678",
        }
        self.dancer = Dancer.objects.create(academy=self.academy, **self.test_data)

        self.client.login(email="user@test.com", password="123456")

    def test_get_dancer_detail_view(self):
        # Check that the response status code is 200 and the template used are correct.
        response = self.client.get(self.dancer.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("dancer_detail.html")

        object = response.context.get("object")
        self.assertIsInstance(object, Dancer)

    def test_user_get_unrelated_dancer(self):
        # Check that the logged-in user cannot access a non-related Dancer instance.
        user2 = OSUser.objects.create_user(email="user2@test.com", password="123456")
        academy2 = Academy.objects.create(user=user2, name="Test academy2")
        dancer2 = Dancer.objects.create(academy=academy2, **self.test_data)

        response = self.client.get(dancer2.get_absolute_url(), follow=True)
        expected_url = reverse("home")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("You don't have permissions to perform this action.", messages)

    def test_dancer_related_choreographies(self):
        response = self.client.get(self.dancer.get_absolute_url())
        choreographies_qs = response.context.get("choreographies_qs")
        dancer_choreographies = self.dancer.choreographies.all()
        self.assertEqual(list(choreographies_qs), list(dancer_choreographies))


class ProfessorListViewTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.professors_list = [
            Professor(
                academy=self.academy,
                first_name="test",
                last_name=f"professor {i}",
                identification_type="ID",
                identification_number=f"12345678{i}",
            )
            for i in range(15)
        ]
        Professor.objects.bulk_create(self.professors_list)

        self.client.login(email="user@test.com", password="123456")
        self.path = reverse("professor_list")

    def test_get_professor_list_view(self):
        # Check that the page object is showing 10 items per page.
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("professor_list.html")

        page_obj = response.context.get("page_obj")
        paginator = page_obj.paginator
        self.assertEqual(paginator.num_pages, 2)

        second_page = paginator.get_page(2)
        self.assertEqual(second_page.start_index(), 11)

    def test_academy_related_professors_queryset(self):
        # Check that the shown Professor instances are related to the logged-in user's Academy.
        response = self.client.get(self.path)

        page_obj = response.context.get("page_obj")
        response_qs = page_obj.object_list
        test_qs = Professor.objects.all()[:10]
        self.assertEqual(response_qs, list(test_qs))

    def test_search_input_filter(self):
        # Check that the search input value filters the queryset properly.
        get_params = {"search_input": "professor 1"}
        response = self.client.get(self.path, get_params)

        professor_qs = Professor.objects.filter(
            Q(identification_number__icontains="professor 1")
            | Q(first_name__icontains="professor 1")
            | Q(last_name__icontains="professor 1")
        )
        page_obj = response.context.get("page_obj")
        response_qs = page_obj.object_list
        self.assertEqual(response_qs, list(professor_qs))


class ProfessorCreateViewTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.test_data = {
            "first_name": "test",
            "last_name": "professor",
            "identification_type": "ID",
            "identification_number": "12345678",
        }

        self.path = reverse("professor_create")
        self.client.login(email="user@test.com", password="123456")

    def test_get_professor_create_view(self):
        # Check that the response status code is 200, the template used and the form instance are correct.
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("professor_form.html")

        form = response.context.get("form")
        self.assertIsInstance(form, ProfessorForm)

    def test_professor_creation_with_image_upload(self):
        # Create a mock image for sending in the request.
        image_content = b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00"
        self.test_data["identification_front_image"] = SimpleUploadedFile(
            "test_file.gif", image_content
        )

        # Try to create a Professor instance through a POST request.
        response = self.client.post(self.path, self.test_data, follow=True)
        expected_url = reverse("professor_list")
        self.assertRedirects(response, expected_url)
        self.assertContains(response, "Successfully added a new professor!")
        self.assertEqual(Professor.objects.count(), 1)

        # Remove the file and the created media folder.
        academy_name_snaked = self.academy.name.replace(" ", "_")
        professor = Professor.objects.get(pk=1)
        professor.identification_front_image.delete(save=True)
        test_media_folder_path = f"{settings.MEDIA_ROOT}/{academy_name_snaked}/"
        if os.path.isdir(test_media_folder_path):
            shutil.rmtree(test_media_folder_path)
            if not any(os.scandir(settings.MEDIA_ROOT)):
                os.rmdir(settings.MEDIA_ROOT)

    def test_professor_creation_without_required_data(self):
        # Try to create a Professor instance with missing information.
        self.test_data["identification_number"] = ""
        response = self.client.post(self.path, self.test_data)
        self.assertContains(response, "This field is required.")


class ProfessorCreateTransactionTest(TransactionTestCase):
    def setUp(self):
        self.test_data = {
            "first_name": "test",
            "last_name": "professor",
            "identification_type": "ID",
            "identification_number": "12345678",
        }

        self.path = reverse("professor_create")

    def test_unique_constraint_integrity_error(self):
        # Try to create a Professor instance with duplicated identification_type, number and academy.
        user = OSUser.objects.create_user(email="user@test.com", password="123456")
        academy = Academy.objects.create(user=user, name="Test academy")
        Professor.objects.create(academy=academy, **self.test_data)

        self.client.login(email="user@test.com", password="123456")

        response = self.client.post(self.path, self.test_data, follow=True)
        expected_url = reverse("professor_list")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(
            "A professor with that identification type and number already exists.",
            messages,
        )
        self.assertEqual(Professor.objects.count(), 1)


class ProfessorUpdateViewTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.test_data = {
            "first_name": "test",
            "last_name": "professor",
            "identification_type": "ID",
            "identification_number": "12345678",
        }
        self.professor = Professor.objects.create(
            academy=self.academy, **self.test_data
        )

        self.client.login(email="user@test.com", password="123456")

    def test_get_professor_update_view(self):
        # Check that the response status code is 200, the template used and the form instance are correct.
        response = self.client.get(self.professor.get_update_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("professor_form.html")

        object = response.context.get("object")
        self.assertIsInstance(object, Professor)

        form = response.context.get("form")
        self.assertIsInstance(form, ProfessorForm)

    def test_get_nonexisting_professor(self):
        # Check that the response status code is 404 when trying to access an unexistent instance information.
        path = reverse("professor_update", kwargs={"professor_pk": 88})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed("404.html")

    def test_user_get_unrelated_professor(self):
        # Check that the logged-in user cannot access a non-related Professor instance.
        user2 = OSUser.objects.create_user(email="user2@test.com", password="123456")
        academy2 = Academy.objects.create(user=user2, name="Test academy2")
        professor2 = Professor.objects.create(academy=academy2, **self.test_data)

        response = self.client.get(professor2.get_update_url(), follow=True)
        expected_url = reverse("home")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("You don't have permissions to perform this action.", messages)

    def test_professor_update_without_required_data(self):
        # Try to update a Professor instance with missing information.
        self.test_data["identification_number"] = ""
        response = self.client.post(
            self.professor.get_update_url(), self.test_data, follow=True
        )
        self.assertContains(response, "This field is required.")

    def test_professor_update(self):
        # Check that the Professor instance is being updated.
        self.test_data["identification_number"] = "87654321"
        response = self.client.post(
            self.professor.get_update_url(), self.test_data, follow=True
        )
        expected_url = reverse("professor_list")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Successfully updated the professor information!", messages)
        self.assertEqual(Professor.objects.count(), 1)


class ProfessorUpdateTransactionTest(TransactionTestCase):
    def setUp(self):
        self.test_data = {
            "first_name": "test",
            "last_name": "professor",
            "identification_type": "ID",
            "identification_number": "12345678",
        }

    def test_unique_constraint_integrity_error(self):
        # Try to update a Professor instance with duplicated identification_type, number and academy.
        user = OSUser.objects.create_user(email="user@test.com", password="123456")
        academy = Academy.objects.create(user=user, name="Test academy")
        Professor.objects.create(academy=academy, **self.test_data)
        self.test_data["identification_type"] = "PASSPORT"
        professor2 = Professor.objects.create(academy=academy, **self.test_data)

        self.client.login(email="user@test.com", password="123456")

        self.test_data["identification_type"] = "ID"
        response = self.client.post(
            professor2.get_update_url(), self.test_data, follow=True
        )
        expected_url = reverse("professor_list")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(
            "A professor with that identification type and number already exists.",
            messages,
        )


class ProfessorDetailViewTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.test_data = {
            "first_name": "test",
            "last_name": "professor",
            "identification_type": "ID",
            "identification_number": "12345678",
        }
        self.professor = Professor.objects.create(
            academy=self.academy, **self.test_data
        )

        self.client.login(email="user@test.com", password="123456")

    def test_get_professor_detail_view(self):
        # Check that the response status code is 200 and the template used are correct.
        response = self.client.get(self.professor.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("professor_detail.html")

        object = response.context.get("object")
        self.assertIsInstance(object, Professor)

    def test_user_get_unrelated_professor(self):
        # Check that the logged-in user cannot access a non-related Professor instance.
        user2 = OSUser.objects.create_user(email="user2@test.com", password="123456")
        academy2 = Academy.objects.create(user=user2, name="Test academy2")
        professor2 = Professor.objects.create(academy=academy2, **self.test_data)

        response = self.client.get(professor2.get_absolute_url(), follow=True)
        expected_url = reverse("home")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("You don't have permissions to perform this action.", messages)

    def test_professor_related_choreographies(self):
        response = self.client.get(self.professor.get_absolute_url())
        choreographies_qs = response.context.get("choreographies_qs")
        professor_choreographies = self.professor.choreographies.all()
        self.assertEqual(list(choreographies_qs), list(professor_choreographies))
