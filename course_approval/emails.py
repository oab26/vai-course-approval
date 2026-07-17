"""Email notifications for course approval workflow."""

import logging

from django.conf import settings
from django.core.mail import send_mail

log = logging.getLogger(__name__)


def get_admin_recipients(course_key):
    """
    Resolve the set of admin email addresses that should be notified for a course.

    Dynamic — derived from live roles, nothing hardcoded:
    1. Studio Course Team "Admin" of THIS course (course-level ``instructor`` role)
    2. Global staff + superusers (platform admins, safety net)
    3. COURSE_APPROVAL_ADMIN_EMAIL, if configured (optional extra recipient)

    Returns a sorted, de-duplicated list of non-empty emails.
    """
    from django.contrib.auth import get_user_model
    from django.db.models import Q

    User = get_user_model()
    emails = set()

    # 1) Course Admins (instructor role) for this specific course
    try:
        from common.djangoapps.student.models import CourseAccessRole
        admin_ids = list(
            CourseAccessRole.objects.filter(
                course_id=course_key, role='instructor'
            ).values_list('user_id', flat=True)
        )
        if admin_ids:
            emails.update(
                User.objects.filter(id__in=admin_ids, is_active=True)
                .exclude(email='').values_list('email', flat=True)
            )
    except Exception:
        log.exception('CourseApproval: error collecting course admins for %s', course_key)

    # 2) Global staff + superusers (platform admins)
    try:
        emails.update(
            User.objects.filter(Q(is_staff=True) | Q(is_superuser=True), is_active=True)
            .exclude(email='').values_list('email', flat=True)
        )
    except Exception:
        log.exception('CourseApproval: error collecting global admins')

    # 3) Optional configured fallback address
    configured = getattr(settings, 'COURSE_APPROVAL_ADMIN_EMAIL', '')
    if configured:
        emails.add(configured)

    return sorted(e for e in emails if e)


def notify_admin_review_requested(course_key, course_name, instructor_user):
    """Send email to admins when an instructor requests review."""
    recipients = get_admin_recipients(course_key)
    if not recipients:
        log.warning('CourseApproval: no admin recipients resolved for %s', course_key)
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
            from_email=getattr(settings, 'COURSE_APPROVAL_FROM_EMAIL', 'noreply@updates.bytecrew.net'),
            recipient_list=recipients,
            fail_silently=True,
        )
        log.info('CourseApproval: sent review request email for %s to %s', course_key, ', '.join(recipients))
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
            from_email=getattr(settings, 'COURSE_APPROVAL_FROM_EMAIL', 'noreply@updates.bytecrew.net'),
            recipient_list=[instructor_user.email],
            fail_silently=True,
        )
        log.info(
            'CourseApproval: sent published notification to %s for %s',
            instructor_user.email, course_key,
        )
    except Exception:
        log.exception('CourseApproval: failed to send instructor notification')
