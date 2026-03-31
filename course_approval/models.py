"""Models for course approval workflow."""

from django.conf import settings
from django.db import models
from opaque_keys.edx.django.models import CourseKeyField


class CourseApprovalRequest(models.Model):
    """Tracks the approval state of a course."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    course_key = CourseKeyField(max_length=255, unique=True, db_index=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_courses',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_courses',
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'course_approval'
        verbose_name = 'Course Approval Request'
        verbose_name_plural = 'Course Approval Requests'

    def __str__(self):
        return f'{self.course_key} [{self.status}]'
