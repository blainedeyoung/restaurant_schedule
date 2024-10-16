from django.db import models


class Restaurant(models.Model):
    """
    Stores the name of each restaurant.
    """
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Schedule(models.Model):
    """
    Stores the operating hours for each restaurant for specific days.
    """
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
