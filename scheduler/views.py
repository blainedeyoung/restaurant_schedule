import csv
import io
from datetime import datetime, time, timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.views import View
from .models import Restaurant, Schedule


def parse_time(time_str):
    """
    takes a standard time string as a human would write it and returns a datetime object
    :param time_str: a string we're expecting to contain a time
    :return: datetime removed from string
    """
    time_str = time_str.strip().lower().replace(' ', '')
    try:
        if 'am' in time_str or 'pm' in time_str:
            try:
                return datetime.strptime(time_str, '%I:%M%p').time()
            except ValueError:
                return datetime.strptime(time_str, '%I%p').time()
        else:
            try:
                return datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                return datetime.strptime(time_str, '%H').time()
    except ValueError as e:
        raise ValueError(f"Time data '{time_str}' is not in a recognized format.") from e


class CheckOpenRestaurantsView(View):
    def get(self, request):
        """
        Display a form to check open restaurants.
        """
        return render(request, 'scheduler/check_open_restaurants.html')

    def post(self, request):
        """
        Enter a query of what restaurants are open at a certain day and time
        """
        input_str = request.POST.get('datetime')
        try:
            day, time_str = input_str.split(None, 1)
            day = day[:3].capitalize()
            check_time = parse_time(time_str)
        except (ValueError, IndexError):
            messages.error(
                request,
                'Invalid datetime format. Please enter in "Day Time" format, e.g., "Monday 9 AM".'
            )
            return redirect('check_open_restaurants')

        # Query the database for active schedules matching the day and time
        open_restaurants = set()
        active_schedules = Schedule.objects.filter(
            is_active=True,
            day_of_week=day
        ).select_related('restaurant')  # Optimize query with select_related

        # Efficiently filter schedules for normal and overnight hours
        for schedule in active_schedules:
            if schedule.opening_time <= schedule.closing_time:
                # Normal opening hours
                if schedule.opening_time <= check_time < schedule.closing_time:
                    open_restaurants.add(schedule.restaurant.name)
            else:
                # Overnight opening hours (e.g., 10 PM - 2 AM)
                if check_time >= schedule.opening_time or check_time < schedule.closing_time:
                    open_restaurants.add(schedule.restaurant.name)

        context = {
            'input': input_str,
            'open_restaurants': list(open_restaurants),
        }
        return render(request, 'scheduler/open_restaurants_result.html', context)


class UploadScheduleView(View):
    def get(self, request):
        """
        Display the form to upload a schedule CSV.
        """
        return render(request, 'scheduler/upload_schedule.html')

    def post(self, request):
        """
        Handle CSV upload and create schedule objects from the uploaded file.
        """
        csv_file = request.FILES.get('file')
        if not csv_file:
            messages.error(request, 'No file uploaded')
            return redirect('upload_schedule')

        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)

            with transaction.atomic():
                for row in reader:
                    if len(row) != 2:
                        raise ValueError(f"Invalid row: {row}")

                    restaurant_name, schedule_str = row
                    restaurant, _ = Restaurant.objects.get_or_create(name=restaurant_name)

                    # Inactivate old schedules for this restaurant
                    Schedule.objects.filter(restaurant=restaurant, is_active=True).update(is_active=False)

                    # Parse and create new schedules
                    schedules = schedule_str.split('/')
                    for schedule in schedules:
                        days_part, times_part = schedule.strip().split(' ', 1)
                        time_ranges = times_part.split(',')

                        # Handle day ranges (e.g., Mon-Fri)
                        day_range = days_part.split('-')
                        all_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                        if len(day_range) == 1:
                            day_list = [day_range[0][:3].capitalize()]
                        else:
                            start_day = all_days.index(day_range[0][:3].capitalize())
                            end_day = all_days.index(day_range[1][:3].capitalize())
                            day_list = all_days[start_day:end_day + 1]

                        # Create Schedule objects for each time range and day
                        for time_range in time_ranges:
                            open_time, close_time = map(parse_time, time_range.strip().split('-'))
                            for day in day_list:
                                Schedule.objects.create(
                                    restaurant=restaurant,
                                    day_of_week=day,
                                    opening_time=open_time,
                                    closing_time=close_time,
                                    is_active=True
                                )

            messages.success(request, 'Schedule uploaded successfully')
            return redirect('check_open_restaurants')

        except Exception as e:
            messages.error(request, f'Error uploading schedule: {str(e)}')
            return redirect('upload_schedule')
