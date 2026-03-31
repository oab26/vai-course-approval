"""Django admin for course approval workflow."""

import logging

from django.contrib import admin
from django.utils import timezone

from .emails import notify_instructor_of_decision
from .models import CourseApprovalRequest

log = logging.getLogger(__name__)


def _set_course_visibility(course_key, visibility):
    """Set catalog_visibility on a course via modulestore."""
    try:
        from xmodule.modulestore.django import modulestore
        store = modulestore()
        course = store.get_course(course_key)
        if course:
            course.catalog_visibility = visibility
            store.update_item(course, None)
            log.info(
                'CourseApproval: set catalog_visibility=%s for %s',
                visibility, course_key,
            )
    except Exception:
        log.exception(
            'CourseApproval: failed to set visibility for %s', course_key
        )


@admin.register(CourseApprovalRequest)
class CourseApprovalRequestAdmin(admin.ModelAdmin):
    list_display = (
        'course_key', 'status', 'submitted_by_display',
        'submitted_at', 'reviewed_by', 'reviewed_at',
    )
    list_filter = ('status',)
    search_fields = ('course_key',)
    readonly_fields = (
        'course_key', 'submitted_by', 'submitted_at',
        'created_at', 'updated_at',
    )
    fields = (
        'course_key', 'status', 'submitted_by', 'submitted_at',
        'reviewed_by', 'reviewed_at', 'reviewer_notes',
        'created_at', 'updated_at',
    )
    actions = ['approve_courses', 'reject_courses']

    def submitted_by_display(self, obj):
        if obj.submitted_by:
            return f'{obj.submitted_by.username} ({obj.submitted_by.email})'
        return '-'
    submitted_by_display.short_description = 'Submitted By'

    @admin.action(description='Approve selected courses')
    def approve_courses(self, request, queryset):
        count = 0
        for approval in queryset.filter(status='pending_review'):
            approval.status = 'approved'
            approval.reviewed_by = request.user
            approval.reviewed_at = timezone.now()
            approval.save()
            notify_instructor_of_decision(approval)
            _set_course_visibility(approval.course_key, 'both')
            count += 1
        self.message_user(
            request, f'{count} course(s) approved and made visible.'
        )

    @admin.action(description='Reject selected courses')
    def reject_courses(self, request, queryset):
        count = 0
        for approval in queryset.filter(status='pending_review'):
            approval.status = 'rejected'
            approval.reviewed_by = request.user
            approval.reviewed_at = timezone.now()
            approval.save()
            notify_instructor_of_decision(approval)
            count += 1
        self.message_user(
            request, f'{count} course(s) rejected. Instructors have been notified.'
        )
