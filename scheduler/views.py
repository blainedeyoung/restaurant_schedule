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
    time_str = time_str.lower().replace(' ', '')
    try:
        if 'am' in time_str or 'pm' in time_str:
            return datetime.strptime(time_str, '%I%p').time()
        return datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        # If parsing fails, try with minutes
        if 'am' in time_str or 'pm' in time_str:
            return datetime.strptime(time_str, '%I:%M%p').time()
        return datetime.strptime(time_str, '%H:%M').time()


def parse_schedule(schedule_str):
    """
    takes the schedule string from the csv file and builds a dictionary
    of days and times that the program can check
    :param schedule_str: the entire input string from the csv file
    :return: parsed_schedule: a dictionary of days and times
    """
    parsed_schedule = {day: [] for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}
    parts = schedule_str.split('/')
    all_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    for part in parts:
        days, times = part.strip().split(' ', 1)
        day_range = days.split('-')
        if len(day_range) == 1:
            days = [day_range[0][:3].capitalize()]
        else:
            start_day, end_day = day_range
            start_index = all_days.index(start_day[:3].capitalize())
            end_index = all_days.index(end_day[:3].capitalize())
            days = all_days[start_index:] + all_days[:end_index + 1] if start_index > end_index else all_days[
                                                                                                     start_index:end_index + 1]

        open_time, close_time = map(parse_time, times.split('-'))

        for i, day in enumerate(days):
            if close_time <= open_time:  # Closes after midnight
                parsed_schedule[day].append((open_time, time(23, 59, 59)))
                next_day = all_days[(all_days.index(day) + 1) % 7]
                parsed_schedule[next_day].insert(0, (time(0, 0, 0), close_time))
            else:
                parsed_schedule[day].append((open_time, close_time))

    return parsed_schedule


def parse_user_time(time_str):
    """
    parses the time that the user inputs to query the schedule
    :param time_str: a string that we assume will include a time
    :return: a datetime object derived from the user input
    """
    time_str = time_str.lower().replace(' ', '')
    try:
        if ':' in time_str:
            if 'am' in time_str or 'pm' in time_str:
                return datetime.strptime(time_str, '%I:%M%p').time()
            return datetime.strptime(time_str, '%H:%M').time()
        else:
            if 'am' in time_str or 'pm' in time_str:
                return datetime.strptime(time_str, '%I%p').time()
            return datetime.strptime(time_str, '%H').time()
    except ValueError as e:
        raise ValueError(
            f"Invalid time format: {time_str}. Please use formats like '9am', '2:30pm', or '14:00'.") from e


class CheckOpenRestaurantsView(View):
    def get(self, request):
        """
        displays the blank form in the template
        """
        return render(request, 'scheduler/check_open_restaurants.html')

    def post(self, request):
        """
        converts user input into a datetime object check_time,
        retrieves the active_schedules from the database,
        converts the schedule into a searchable object,
        finds the open restaurants from the parsed_schedule object
        """
        input_str = request.POST.get('datetime')
        try:
            day, time_str = input_str.split(None, 1)
            day = day[:3].capitalize()
            check_time = parse_user_time(time_str)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('check_open_restaurants')

        open_restaurants = []
        active_schedules = Schedule.objects.filter(is_active=True).select_related('restaurant')

        for schedule in active_schedules:
            try:
                parsed_schedule = parse_schedule(schedule.schedule)
                if day in parsed_schedule:
                    for open_time, close_time in parsed_schedule[day]:
                        if open_time <= check_time < close_time:
                            open_restaurants.append(schedule.restaurant.name)
                            break
            except Exception as e:
                messages.warning(request, f"Error processing schedule for {schedule.restaurant.name}: {str(e)}")

        context = {
            'input': input_str,
            'open_restaurants': open_restaurants,
        }
        return render(request, 'scheduler/open_restaurants_result.html', context)


class UploadScheduleView(View):
    def get(self, request):
        """
        displays the blank form for schedule upload
        """
        return render(request, 'scheduler/upload_schedule.html')

    def post(self, request):
        """
        uploads a csv file and creates a schedule object from it
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

                    # Inactivate old schedules
                    Schedule.objects.filter(restaurant=restaurant, is_active=True).update(is_active=False)

                    # Create new schedule
                    Schedule.objects.create(restaurant=restaurant, schedule=schedule_str, is_active=True)

            messages.success(request, 'Schedule uploaded successfully')
            return redirect('check_open_restaurants')

        except Exception as e:
            messages.error(request, f'Error uploading schedule: {str(e)}')
            return redirect('upload_schedule')