"""URL routes for course approval API."""

from django.urls import path

from . import views

app_name = 'course_approval'

urlpatterns = [
    path(
        'has-changes/<str:course_key_string>/',
        views.has_changes,
        name='has_changes',
    ),
    path(
        'notify/<str:course_key_string>/',
        views.notify_admin,
        name='notify_admin',
    ),
]
