"""Signal handlers for course approval workflow."""

import logging

from django.dispatch import receiver

log = logging.getLogger(__name__)


try:
    from xmodule.modulestore.django import SignalHandler, modulestore

    @receiver(SignalHandler.course_published)
    def on_course_published(sender, course_key, **kwargs):
        """
        Safety net: if a course is published without approval,
        revert catalog_visibility to 'none' so it stays hidden.
        """
        from .models import CourseApprovalRequest

        try:
            approval = CourseApprovalRequest.objects.get(course_key=course_key)
        except CourseApprovalRequest.DoesNotExist:
            # No approval record = course managed by admin directly, allow
            return

        if approval.status == 'approved':
            return

        # Not approved — revert visibility
        try:
            store = modulestore()
            course = store.get_course(course_key)
            if course and getattr(course, 'catalog_visibility', None) != 'none':
                course.catalog_visibility = 'none'
                store.update_item(course, None)
                log.warning(
                    'CourseApproval: reverted catalog_visibility for unapproved course %s',
                    course_key,
                )
        except Exception:
            log.exception(
                'CourseApproval: failed to revert visibility for %s', course_key
            )

except ImportError:
    # xmodule not available (e.g. during pip install or tests outside edx-platform)
    log.info('CourseApproval: xmodule not available, skipping signal registration')
