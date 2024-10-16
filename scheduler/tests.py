from django.test import TestCase, Client
from django.urls import reverse
from .models import Restaurant, Schedule
from .views import parse_time, parse_schedule, parse_user_time
from datetime import time
from django.core.files.uploadedfile import SimpleUploadedFile


class ModelTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant")
        self.schedule = Schedule.objects.create(
            restaurant=self.restaurant,
            schedule="Mon-Fri 9am - 5pm",
            is_active=True
        )

    def test_restaurant_creation(self):
        self.assertEqual(self.restaurant.name, "Test Restaurant")

    def test_schedule_creation(self):
        self.assertEqual(self.schedule.restaurant, self.restaurant)
        self.assertEqual(self.schedule.schedule, "Mon-Fri 9am - 5pm")
        self.assertTrue(self.schedule.is_active)


class UtilityFunctionTests(TestCase):
    def test_parse_time(self):
        self.assertEqual(parse_time("9am"), time(9, 0))
        self.assertEqual(parse_time("5:30pm"), time(17, 30))
        self.assertEqual(parse_time("14:00"), time(14, 0))

    def test_parse_user_time(self):
        self.assertEqual(parse_user_time("9am"), time(9, 0))
        self.assertEqual(parse_user_time("5:30pm"), time(17, 30))
        self.assertEqual(parse_user_time("14:00"), time(14, 0))

    def test_parse_schedule(self):
        schedule = "Mon-Fri 9am - 5pm / Sat 10am - 3pm"
        parsed = parse_schedule(schedule)
        self.assertEqual(parsed["Mon"], [(time(9, 0), time(17, 0))])
        self.assertEqual(parsed["Fri"], [(time(9, 0), time(17, 0))])
        self.assertEqual(parsed["Sat"], [(time(10, 0), time(15, 0))])
        self.assertEqual(parsed["Sun"], [])

    def test_parse_schedule_with_midnight_crossing(self):
        schedule = "Mon-Thu 10am - 11pm / Fri 10am - 2am"
        parsed = parse_schedule(schedule)
        self.assertEqual(parsed["Mon"], [(time(10, 0), time(23, 0))])
        self.assertEqual(parsed["Fri"], [(time(10, 0), time(23, 59, 59))])
        self.assertEqual(parsed["Sat"], [(time(0, 0), time(2, 0))])


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.restaurant1 = Restaurant.objects.create(name="Day Restaurant")
        self.restaurant2 = Restaurant.objects.create(name="Night Restaurant")
        Schedule.objects.create(
            restaurant=self.restaurant1,
            schedule="Mon-Fri 9am - 5pm",
            is_active=True
        )
        Schedule.objects.create(
            restaurant=self.restaurant2,
            schedule="Mon-Sat 6pm - 2am",
            is_active=True
        )

    def test_check_open_restaurants_view_get(self):
        response = self.client.get(reverse('check_open_restaurants'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scheduler/check_open_restaurants.html')

    def test_check_open_restaurants_view_post(self):
        response = self.client.post(reverse('check_open_restaurants'), {'datetime': 'Mon 10am'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scheduler/open_restaurants_result.html')
        self.assertContains(response, "Day Restaurant")
        self.assertNotContains(response, "Night Restaurant")

    def test_check_open_restaurants_view_post_after_midnight(self):
        response = self.client.post(reverse('check_open_restaurants'), {'datetime': 'Tue 1am'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scheduler/open_restaurants_result.html')
        self.assertContains(response, "Night Restaurant")
        self.assertNotContains(response, "Day Restaurant")

    def test_check_open_restaurants_view_post_invalid_input(self):
        response = self.client.post(reverse('check_open_restaurants'), {'datetime': 'Invalid'})
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertRedirects(response, reverse('check_open_restaurants'))

    def test_upload_schedule_view_get(self):
        response = self.client.get(reverse('upload_schedule'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scheduler/upload_schedule.html')

    def test_upload_schedule_view_post(self):
        csv_content = b"Test Restaurant,Mon-Fri 9am - 5pm"
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
        response = self.client.post(reverse('upload_schedule'), {'file': csv_file})
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertRedirects(response, reverse('check_open_restaurants'))
        self.assertTrue(Restaurant.objects.filter(name="Test Restaurant").exists())
        self.assertTrue(Schedule.objects.filter(restaurant__name="Test Restaurant", schedule="Mon-Fri 9am - 5pm").exists())

    def test_upload_schedule_view_post_no_file(self):
        response = self.client.post(reverse('upload_schedule'))
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertRedirects(response, reverse('upload_schedule'))

    def test_upload_schedule_view_post_invalid_csv(self):
        csv_content = b"Invalid CSV Content"
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
        response = self.client.post(reverse('upload_schedule'), {'file': csv_file})
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertRedirects(response, reverse('upload_schedule'))


class IntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_upload_and_check_schedule(self):
        # Upload a schedule
        csv_content = b"Integration Test Restaurant,Mon-Fri 9am - 5pm / Sat 10am - 2pm"
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
        response = self.client.post(reverse('upload_schedule'), {'file': csv_file})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('check_open_restaurants'))

        # Check if the restaurant is open on Monday at 10am
        response = self.client.post(reverse('check_open_restaurants'), {'datetime': 'Mon 10am'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Integration Test Restaurant")

        # Check if the restaurant is closed on Monday at 6pm
        response = self.client.post(reverse('check_open_restaurants'), {'datetime': 'Mon 6pm'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Integration Test Restaurant")

        # Check if the restaurant is open on Saturday at 11am
        response = self.client.post(reverse('check_open_restaurants'), {'datetime': 'Sat 11am'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Integration Test Restaurant")

        # Check if the restaurant is closed on Sunday
        response = self.client.post(reverse('check_open_restaurants'), {'datetime': 'Sun 12pm'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Integration Test Restaurant")