Restaurant Scheduler
This project is a Django-based web application designed to manage restaurant schedules and allow users to check which restaurants are open at a given day and time. The application enables the upload of restaurant schedules via CSV files and provides an interface for users to query open restaurants based on their input.

Overview
The Restaurant Scheduler application consists of two main functionalities:

Upload Schedule: Allows administrators to upload a CSV file containing restaurant names and their operating hours.
Check Open Restaurants: Enables users to input a specific day and time to find out which restaurants are open.
Models
Restaurant Model
class Restaurant(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name
Purpose: Stores the name of each restaurant.
Fields:
name: The unique name of the restaurant.
Schedule Model
class Schedule(models.Model):
    DAYS_OF_WEEK = [
        ('Mon', 'Monday'),
        ('Tue', 'Tuesday'),
        ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'),
        ('Fri', 'Friday'),
        ('Sat', 'Saturday'),
        ('Sun', 'Sunday'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.restaurant.name} - {self.get_day_of_week_display()} ({self.opening_time} to {self.closing_time})"
Purpose: Stores the operating hours for each restaurant for specific days.
Fields:
restaurant: Foreign key linking to the Restaurant model.
day_of_week: The day of the week for the schedule.
opening_time: The time the restaurant opens.
closing_time: The time the restaurant closes.
is_active: Indicates if the schedule is active.
Views
UploadScheduleView
Purpose: Handles the upload and processing of the CSV file containing restaurant schedules.
Methods:
get: Renders the upload schedule form.
post: Processes the uploaded CSV file and updates the database.
Key Functionalities:

CSV Parsing: Reads the CSV file, handling cases where schedules contain commas.
Data Validation: Ensures that each row has the correct format and necessary data.
Database Transactions: Uses atomic transactions to maintain data integrity during the upload process.
Schedule Creation: Parses schedules and creates Schedule objects for each restaurant and day.
CheckOpenRestaurantsView
Purpose: Allows users to check which restaurants are open at a given day and time.
Methods:
get: Renders the form for user input.
post: Processes the input and displays the list of open restaurants.
Key Functionalities:

Input Parsing: Parses the user's input for day and time, handling various time formats.
Error Handling: Provides user-friendly error messages for invalid inputs.
Query Optimization: Uses select_related and efficient filtering to retrieve relevant schedules.
Overnight Hours Handling: Correctly identifies restaurants that are open overnight (e.g., 10 PM - 4 AM).
parse_time Function
def parse_time(time_str):
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
Purpose: Parses time strings in both 12-hour and 24-hour formats.
Handles:
Times with and without minutes.
12-hour formats with 'AM'/'PM'.
24-hour formats.
Templates
base.html
Structure: Provides a common structure for all pages, including navigation links and message display.
check_open_restaurants.html
Purpose: Renders the form for users to input a day and time to check open restaurants.
open_restaurants_result.html
Purpose: Displays the list of open restaurants based on the user's input.
upload_schedule.html
Purpose: Renders the form for administrators to upload a schedule CSV file.
Tests
Overview
I implemented unit tests to ensure the reliability and correctness of the application's functionalities. The tests cover key components without overcomplicating the test suite.

parse_time Tests
Purpose: Verify that the parse_time function correctly parses various time formats.
Test Cases:
12-hour format with and without minutes.
24-hour format with and without minutes.
Invalid time formats to ensure exceptions are raised.
CheckOpenRestaurantsViewTests
Purpose: Test the CheckOpenRestaurantsView functionality.
Test Cases:
GET request returns a 200 status code.
Valid POST request returns open restaurants.
Time outside operating hours does not return the restaurant.
Invalid datetime input returns an error message.
UploadScheduleViewTests
Purpose: Test the UploadScheduleView functionality.
Test Cases:
GET request returns a 200 status code.
Valid CSV upload creates restaurants and schedules.
No file uploaded returns an error message.
Invalid CSV content returns an error message.
Challenges Faced
Time Parsing Complexity
Issue: Handling various time formats in user input and CSV files was challenging due to inconsistencies in formatting (e.g., '9 AM', '9AM', '21', '14:00').

Solution:

Developed a robust parse_time function that can handle multiple time formats.
Implemented extensive tests to cover different scenarios and ensure reliability.
Error Handling and User Feedback
Issue: Providing clear and consistent error messages to users when they input invalid data.

Solution:

Standardized error messages across views.
Updated exception handling to catch specific errors and inform users accordingly.
Adjusted tests to expect the new error messages.
CSV Parsing
Issue: Parsing CSV files with complex schedule strings that contain commas and slashes, which could interfere with CSV parsing.

Solution:

Modified the CSV reading logic to join remaining columns after the restaurant name back into a single schedule string.
Ensured that the CSV parser can handle schedules with commas and multiple time ranges.
Test Failures Due to Mismatched Error Messages
Issue: Tests were failing because the expected error messages did not match the actual messages generated by the application.

Solution:

Updated the application to provide consistent and user-friendly error messages.
Adjusted tests to check for the specific error messages.
Added print statements in tests to debug and verify the content of messages.
Exception Handling
Issue: Unhandled exceptions were causing the application to crash instead of gracefully informing the user.

Solution:

Expanded exception handling in views to catch multiple types of exceptions.
Ensured that appropriate error messages are displayed to the user.
Updated tests to cover these scenarios.
Installation
Clone the Repository:
bash git clone https://github.com/yourusername/restaurant_scheduler.git cd restaurant_scheduler

Create a Virtual Environment:
bash python -m venv venv source venv/bin/activate # On Windows, use `venv\Scripts\activate`

Install Dependencies:
bash pip install -r requirements.txt

Apply Migrations:
bash python manage.py migrate

Run the Server:
bash python manage.py runserver

Usage
Upload Schedule:

Navigate to http://localhost:8000/upload/.
Upload a CSV file containing restaurant schedules.
Ensure the CSV follows the format: "Restaurant Name","Schedule".
Check Open Restaurants:

Navigate to http://localhost:8000/.
Enter a day and time in the format "Monday 9 AM".
View the list of restaurants open at that time.
Conclusion
Creating the Restaurant Scheduler application was an enlightening experience that involved overcoming several challenges related to time parsing, error handling, and data validation. By structuring the models, views, and tests carefully, I was able to build a robust application that meets the project's requirements.

I hope this application serves as a useful tool for managing restaurant schedules and provides a foundation for further development and enhancements.