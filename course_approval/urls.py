"""URL routes for course approval API."""

from django.urls import path

from . import views

app_name = 'course_approval'

urlpatterns = [
    path(
        'submit/<str:course_key_string>/',
        views.submit_for_review,
        name='submit_for_review',
    ),
    path(
        'status/<str:course_key_string>/',
        views.get_approval_status,
        name='approval_status',
    ),
]
