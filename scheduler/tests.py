from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from .models import Restaurant, Schedule
from .views import parse_time
from datetime import time


class ParseTimeTests(TestCase):
    def test_parse_12_hour_format_with_minutes(self):
        self.assertEqual(parse_time('9:00 AM'), time(9, 0))
        self.assertEqual(parse_time('12:30 PM'), time(12, 30))
        self.assertEqual(parse_time('9:15pm'), time(21, 15))

    def test_parse_24_hour_format_with_minutes(self):
        self.assertEqual(parse_time('14:00'), time(14, 0))
        self.assertEqual(parse_time('23:45'), time(23, 45))

    def test_parse_12_hour_format_without_minutes(self):
        self.assertEqual(parse_time('12 AM'), time(0, 0))
        self.assertEqual(parse_time('12 PM'), time(12, 0))
        self.assertEqual(parse_time('9AM'), time(9, 0))
        self.assertEqual(parse_time('9pm'), time(21, 0))

    def test_parse_24_hour_format_without_minutes(self):
        self.assertEqual(parse_time('21'), time(21, 0))
        self.assertEqual(parse_time('0'), time(0, 0))
        self.assertEqual(parse_time('14'), time(14, 0))

    def test_invalid_time_format(self):
        with self.assertRaises(ValueError):
            parse_time('invalid time')
        with self.assertRaises(ValueError):
            parse_time('25:00')
        with self.assertRaises(ValueError):
            parse_time('13:60')
        with self.assertRaises(ValueError):
            parse_time('')


class CheckOpenRestaurantsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.check_url = reverse('check_open_restaurants')

        # Create a restaurant and schedules
        self.restaurant = Restaurant.objects.create(name='Test Restaurant')

        # Schedule: Mon-Fri 9 AM - 5 PM
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        for day in days:
            Schedule.objects.create(
                restaurant=self.restaurant,
                day_of_week=day,
                opening_time=time(9, 0),
                closing_time=time(17, 0),
                is_active=True
            )

    def test_get_request(self):
        response = self.client.get(self.check_url)
        self.assertEqual(response.status_code, 200)

    def test_post_valid_datetime(self):
        response = self.client.post(self.check_url, {'datetime': 'Monday 10 AM'})
        content = response.content.decode()
        self.assertIn('Test Restaurant', content)

    def test_post_datetime_outside_hours(self):
        response = self.client.post(self.check_url, {'datetime': 'Monday 8 AM'})
        content = response.content.decode()
        self.assertNotIn('Test Restaurant', content)

    def test_post_invalid_datetime(self):
        response = self.client.post(self.check_url, {'datetime': 'Invalid Input'}, follow=True)
        messages = list(get_messages(response.wsgi_request))
        for message in messages:
            print(f"Message: {message.message}")
        self.assertTrue(
            any(
                'Invalid datetime format' in message.message for message in messages
            )
        )


class UploadScheduleViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse('upload_schedule')

    def test_get_request(self):
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)

    def test_post_valid_csv(self):
        csv_content = 'Test Restaurant,Mon-Fri 9 AM - 5 PM\n'
        csv_file = SimpleUploadedFile('schedule.csv', csv_content.encode('utf-8'), content_type='text/csv')

        response = self.client.post(self.upload_url, {'file': csv_file}, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Schedule uploaded successfully' in message.message for message in messages))

        # Check that the restaurant and schedules were created
        restaurant = Restaurant.objects.get(name='Test Restaurant')
        schedules = Schedule.objects.filter(restaurant=restaurant)
        self.assertEqual(schedules.count(), 5)  # Mon-Fri

    def test_post_no_file_uploaded(self):
        response = self.client.post(self.upload_url, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('No file uploaded' in message.message for message in messages))

    def test_post_invalid_csv(self):
        csv_content = 'Invalid Content'
        csv_file = SimpleUploadedFile('schedule.csv', csv_content.encode('utf-8'), content_type='text/csv')

        response = self.client.post(self.upload_url, {'file': csv_file}, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Error uploading schedule' in message.message for message in messages))
