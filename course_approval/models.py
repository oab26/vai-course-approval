"""Models for course approval workflow."""

from django.conf import settings
from django.db import models
from opaque_keys.edx.django.models import CourseKeyField


class CourseNotification(models.Model):
    """Tracks when an instructor requests admin review for a course."""

    course_key = CourseKeyField(max_length=255, db_index=True)
    notified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_notifications',
    )
    notified_at = models.DateTimeField()
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'course_approval'
        unique_together = ('course_key', 'notified_by')

    def __str__(self):
        status = 'published' if self.published_at else 'pending'
        return f'{self.course_key} by {self.notified_by.username} [{status}]'

    @property
    def is_active(self):
        """Notification is active if notified but not yet published."""
        return self.notified_at is not None and self.published_at is None
