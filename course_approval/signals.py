"""Signal handlers for course approval workflow."""

import logging

from django.dispatch import receiver
from django.utils import timezone

log = logging.getLogger(__name__)


try:
    from xmodule.modulestore.django import SignalHandler

    @receiver(SignalHandler.course_published)
    def on_course_published(sender, course_key, **kwargs):
        """
        When admin publishes a course, notify any instructors who
        had requested review and reset their notification state.
        """
        from .emails import notify_instructor_published
        from .models import CourseNotification

        # Find active notifications (instructor requested review, not yet published)
        active_notifications = CourseNotification.objects.filter(
            course_key=course_key,
            published_at__isnull=True,
        ).select_related('notified_by')

        if not active_notifications.exists():
            return

        # Get course name for email
        try:
            from xmodule.modulestore.django import modulestore
            course = modulestore().get_course(course_key)
            course_name = course.display_name if course else str(course_key)
        except Exception:
            course_name = str(course_key)

        now = timezone.now()

        for notif in active_notifications:
            # Email the instructor
            notify_instructor_published(course_key, course_name, notif.notified_by)

            # Mark as published (resets the button for future edits)
            notif.published_at = now
            notif.save(update_fields=['published_at'])

            log.info(
                'CourseApproval: notified %s that %s was published',
                notif.notified_by.username, course_key,
            )

except ImportError:
    log.info('CourseApproval: xmodule not available, skipping signal registration')
