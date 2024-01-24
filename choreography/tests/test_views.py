from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse

from academy.models import Academy, Dancer, Professor
from choreography.forms import ChoreographyForm
from choreography.models import Choreography
from event.models import Category, Contact, DanceMode, Event, Price, Schedule

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
        self.list_view_path = reverse(
            "choreography_list", kwargs={"event_pk": self.event.pk}
        )


class ChoreographyListViewTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.choreography_list = [
            Choreography.objects.create(
                academy=self.academy,
                event=self.event,
                dance_mode=self.dance_mode,
                category=self.category,
                price=self.price,
                schedule=self.schedule,
                name=f"Test choreography {i}",
            )
            for i in range(15)
        ]
        for choreography in self.choreography_list:
            choreography.dancers.add(self.dancer)
            choreography.professors.add(self.professor)
            choreography.save()

        self.client.login(email="user@test.com", password="123456")

    def test_get_choreography_list_view(self):
        # Check that the page object is showing 10 items per page.
        response = self.client.get(self.list_view_path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("choreography_list.html")

        page_obj = response.context.get("page_obj")
        paginator = page_obj.paginator
        self.assertEqual(paginator.num_pages, 2)

        second_page = paginator.get_page(2)
        self.assertEqual(second_page.start_index(), 11)

    def test_academy_related_choreographies_queryset(self):
        # Check that the shown Choreography instances are related to the logged-in user's Academy.
        response = self.client.get(self.list_view_path)

        page_obj = response.context.get("page_obj")
        response_qs = page_obj.object_list
        test_qs = Choreography.objects.all()[:10]
        self.assertEqual(response_qs, list(test_qs))

    def test_search_input_filter(self):
        # Check that the search input value filters the queryset properly.
        get_params = {"search_input": "choreography 1"}
        response = self.client.get(self.list_view_path, get_params)

        choreographies_qs = Choreography.objects.filter(
            Q(name__icontains="choreography 1")
            | Q(dance_mode__name__icontains="choreography 1")
            | Q(professors__first_name__icontains="choreography 1")
            | Q(professors__last_name__icontains="choreography 1")
            | Q(category__name__icontains="choreography 1")
            | Q(category__type__icontains="choreography 1")
        )
        page_obj = response.context.get("page_obj")
        response_qs = page_obj.object_list
        self.assertEqual(response_qs, list(choreographies_qs))


class ChoreographyCreateViewTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.test_data = {
            "dance_mode": "1",
            "category": "1",
            "dancers": ["1"],
            "professors": ["1"],
            "name": "Test choreography",
        }

        self.client.login(email="user@test.com", password="123456")

    def test_get_choreography_create_view(self):
        # Check that the response status code is 200, the template used and the form instance are correct.
        response = self.client.get(
            reverse("choreography_create", kwargs={"event_pk": self.event.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("choreography_form.html")

        form = response.context.get("form")
        self.assertIsInstance(form, ChoreographyForm)

        # Check that the dancers field instances belong to the logged-in user.
        user = OSUser.objects.create_user(email="user2@test.com", password="123456")
        academy = Academy.objects.create(
            user=user,
            name="Test academy 2",
            phone_number="12345678",
            city="Test city",
            state="Test state",
        )
        dancer = Dancer.objects.create(
            academy=academy,
            first_name="test",
            last_name="dancer2",
            birth_date=date(2000, 8, 13),
            identification_type="ID",
            identification_number="12345678",
        )
        self.assertNotIn(dancer, form.fields["dancers"].queryset)
        self.assertIn(self.dancer, form.fields["dancers"].queryset)

    def test_choreography_creation(self):
        # Try to create a Choreography instance through a POST request.
        response = self.client.post(
            reverse("choreography_create", kwargs={"event_pk": self.event.pk}),
            self.test_data,
            follow=True,
        )
        self.assertRedirects(response, self.list_view_path)
        self.assertContains(response, "Successfully added a new choreography!")
        self.assertEqual(Choreography.objects.count(), 1)

        # Check that the price is set properly according to the selected category.
        choreography = Choreography.objects.get(pk=1)
        self.assertEqual(choreography.price, self.price)

        # Check that the schedule is set according to the selected event and dance mode.
        self.assertEqual(choreography.schedule, self.schedule)

        # Try to create a Choreography instance without a schedule set for the dance mode.
        dance_mode = DanceMode.objects.create(name="Test dance mode 2")
        self.event.dance_modes.add(self.dance_mode)
        self.schedule.dance_mode = dance_mode
        self.schedule.save()
        response = self.client.post(
            reverse("choreography_create", kwargs={"event_pk": self.event.pk}),
            self.test_data,
            follow=True,
        )
        self.assertRedirects(response, self.list_view_path)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(
            "The system could not add a new choreography since there is no schedule set for it.",
            messages,
        )

        # Try to create a Choreography instance without a price set for the category.
        self.price.due_date = self.event.start_date
        self.price.save()
        response = self.client.post(
            reverse("choreography_create", kwargs={"event_pk": self.event.pk}),
            self.test_data,
            follow=True,
        )
        self.assertRedirects(response, self.list_view_path)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(
            "The system could not add a new choreography since there is no price set for it.",
            messages,
        )

    def test_choreography_creation_without_required_data(self):
        # Try to create a Choreography instance with missing information.
        self.test_data["dance_mode"] = ""
        response = self.client.post(
            reverse("choreography_create", kwargs={"event_pk": self.event.pk}),
            self.test_data,
        )
        self.assertContains(response, "This field is required.")


class ChoreographyDetailViewTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.choreography = Choreography.objects.create(
            academy=self.academy,
            event=self.event,
            dance_mode=self.dance_mode,
            category=self.category,
            price=self.price,
            schedule=self.schedule,
            name="Test choreography 1",
        )
        self.choreography.professors.add(self.professor)
        self.choreography.dancers.add(self.dancer)

        self.client.login(email="user@test.com", password="123456")

    def test_get_choreography_detail_view(self):
        # Check that the response status code is 200 and the template used are correct.
        response = self.client.get(self.choreography.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("choreography_detail.html")

    def test_user_get_unrelated_choreography(self):
        # Check that the logged-in user cannot access a non-related Choreography instance.
        user = OSUser.objects.create_user(email="user2@test.com", password="123456")
        academy = Academy.objects.create(
            user=user,
            name="Test academy 2",
            phone_number="12345678",
            city="Test city",
            state="Test state",
        )
        choreography = Choreography.objects.create(
            academy=academy,
            event=self.event,
            dance_mode=self.dance_mode,
            category=self.category,
            price=self.price,
            schedule=self.schedule,
            name="Test choreography 1",
        )

        response = self.client.get(choreography.get_absolute_url(), follow=True)
        expected_url = reverse("home")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("You don't have permissions to perform this action.", messages)


class ChoreographyUpdateViewTest(ModuleBaseData):
    def setUp(self):
        super().setUp()
        self.choreography = Choreography.objects.create(
            academy=self.academy,
            event=self.event,
            price=self.price,
            dance_mode=self.dance_mode,
            category=self.category,
            schedule=self.schedule,
            name="Test choreography 1",
        )
        self.choreography.professors.add(self.professor)
        self.choreography.dancers.add(self.dancer)

        self.client.login(email="user@test.com", password="123456")

    def test_get_choreography_update_view(self):
        # Check that the response status code is 200, the template used and the form instance are correct.
        response = self.client.get(self.choreography.get_update_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("choreography_form.html")

        form = response.context.get("form")
        self.assertIsInstance(form, ChoreographyForm)

        # Check that the dancers field instances belong to the logged-in user.
        user = OSUser.objects.create_user(email="user2@test.com", password="123456")
        academy = Academy.objects.create(
            user=user,
            name="Test academy 2",
            phone_number="12345678",
            city="Test city",
            state="Test state",
        )
        dancer = Dancer.objects.create(
            academy=academy,
            first_name="Dancer 2",
            last_name="Test",
            birth_date=date(2000, 8, 13),
            identification_type="ID",
            identification_number="12345678",
        )
        self.assertNotIn(dancer, form.fields["dancers"].queryset)
        self.assertIn(self.dancer, form.fields["dancers"].queryset)

    def test_user_get_unrelated_choreography(self):
        # Check that the logged-in user cannot access a non-related Choreography instance.
        user = OSUser.objects.create_user(email="user2@test.com", password="123456")
        academy = Academy.objects.create(
            user=user,
            name="Test academy 2",
            phone_number="12345678",
            city="Test city",
            state="Test state",
        )
        choreography = Choreography.objects.create(
            academy=academy,
            event=self.event,
            dance_mode=self.dance_mode,
            category=self.category,
            price=self.price,
            schedule=self.schedule,
            name="Test choreography 2",
        )

        response = self.client.get(choreography.get_update_url(), follow=True)
        expected_url = reverse("home")
        self.assertRedirects(response, expected_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("You don't have permissions to perform this action.", messages)

    def test_choreography_update(self):
        # Create different test data.
        dance_mode = DanceMode.objects.create(name="Test dance mode 2")
        self.event.dance_modes.add(dance_mode)
        category = Category.objects.create(
            name="Test duo category",
            type=2,
            min_age=20,
            max_age=25,
            max_duration=timedelta(seconds=180),
        )
        self.event.categories.add(category)
        Dancer.objects.create(
            academy=self.academy,
            first_name="Dancer 2",
            last_name="Test",
            birth_date=date(2000, 8, 13),
            identification_type="PASSPORT",
            identification_number="12345678",
        )
        price = Price.objects.create(
            event=self.event,
            name="Test price",
            amount=100,
            due_date=self.event.end_date,
            category_type=category.type,
        )
        schedule = Schedule.objects.create(event=self.event, dance_mode=dance_mode)
        test_data = {
            "dance_mode": "2",
            "category": "2",
            "dancers": ["1", "2"],
            "professors": ["1"],
            "name": "Test choreography 3",
        }

        # Try to update a Choreography instance through a POST request.
        response = self.client.post(
            self.choreography.get_update_url(), test_data, follow=True
        )
        self.assertRedirects(response, self.list_view_path)
        self.assertContains(
            response, "Successfully updated the choreography information!"
        )
        self.assertEqual(Choreography.objects.count(), 1)
        self.choreography.refresh_from_db()
        self.assertEqual(self.choreography.name, "Test choreography 3")

        # Check that the price is set properly according to the selected category.
        self.assertEqual(self.choreography.price, price)

        # Check that the schedule is set according to the selected event and dance mode.
        self.assertEqual(self.choreography.schedule, schedule)

    def test_choreography_creation_without_required_data(self):
        # Try to create a Choreography instance with missing information.
        response = self.client.post(
            self.choreography.get_update_url(), {"dance_mode": ""}
        )
        self.assertContains(response, "This field is required.")
