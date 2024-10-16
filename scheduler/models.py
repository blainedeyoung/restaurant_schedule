from django.db import models


class Restaurant(models.Model):
    """
    We could do without a separate model for Restaurants,
    this seemed better to me. We may want to expand functionality later.
    """
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Schedule(models.Model):
    """
    The restaurant is the name. The schedule is the whole block of text from the csv file.
    The way I set this up allows you to input a new csv file which completely replaces
    any old schedules. They are still in the database just marked inactive. I figure it would
    be easy to go back later and allow you to switch between stored schedules.
    """
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='schedules')
    schedule = models.TextField()  # Store the full schedule string
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.restaurant.name} - {'Active' if self.is_active else 'Inactive'}"