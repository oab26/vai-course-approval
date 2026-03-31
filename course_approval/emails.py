"""Email notifications for course approval workflow."""

import logging

from django.conf import settings
from django.core.mail import send_mail

log = logging.getLogger(__name__)


def notify_admin_review_requested(course_key, course_name, instructor_user):
    """Send email to admin when an instructor requests review."""
    admin_email = getattr(settings, 'COURSE_APPROVAL_ADMIN_EMAIL', '')
    if not admin_email:
        log.warning('CourseApproval: COURSE_APPROVAL_ADMIN_EMAIL not configured')
        return

    cms_base = getattr(settings, 'CMS_BASE', 'studio.lms.bytecrew.net')
    scheme = 'https' if getattr(settings, 'HTTPS', 'on') == 'on' else 'http'
    studio_url = f'{scheme}://{cms_base}/course/{course_key}'

    instructor_name = instructor_user.get_full_name() or instructor_user.username
    instructor_email = instructor_user.email

    try:
        send_mail(
            subject=f'[VAI] Course review request: {course_name}',
            message=(
                f'{instructor_name} ({instructor_email}) has made changes to '
                f'"{course_name}" and is requesting your review.\n\n'
                f'Review in Studio:\n{studio_url}\n'
            ),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bytecrew.net'),
            recipient_list=[admin_email],
            fail_silently=True,
        )
        log.info('CourseApproval: sent review request email to admin for %s', course_key)
    except Exception:
        log.exception('CourseApproval: failed to send admin notification')


def notify_instructor_published(course_key, course_name, instructor_user):
    """Send email to instructor when admin publishes their changes."""
    if not instructor_user or not instructor_user.email:
        log.warning('CourseApproval: no instructor email for %s', course_key)
        return

    try:
        send_mail(
            subject=f'[VAI] Your course changes are now live: {course_name}',
            message=(
                f'The changes you made to "{course_name}" have been reviewed '
                f'and published.\n\n'
                f'Students can now see the updated content.\n'
            ),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bytecrew.net'),
            recipient_list=[instructor_user.email],
            fail_silently=True,
        )
        log.info(
            'CourseApproval: sent published notification to %s for %s',
            instructor_user.email, course_key,
        )
    except Exception:
        log.exception('CourseApproval: failed to send instructor notification')
