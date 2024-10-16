from django.urls import path
from .views import UploadScheduleView, CheckOpenRestaurantsView

urlpatterns = [
    path('', CheckOpenRestaurantsView.as_view(), name='check_open_restaurants'),
    path('upload/', UploadScheduleView.as_view(), name='upload_schedule'),
]