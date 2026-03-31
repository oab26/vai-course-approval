"""Email notifications for course approval workflow."""

import logging

from django.conf import settings
from django.core.mail import send_mail

log = logging.getLogger(__name__)


def notify_admin_of_submission(approval):
    """Send email to admin when an instructor submits a course for review."""
    admin_email = getattr(settings, 'COURSE_APPROVAL_ADMIN_EMAIL', '')
    if not admin_email:
        log.warning('CourseApproval: COURSE_APPROVAL_ADMIN_EMAIL not configured')
        return

    lms_base = getattr(settings, 'LMS_ROOT_URL', 'https://lms.bytecrew.net')
    admin_url = f'{lms_base}/admin/course_approval/courseapprovalrequest/{approval.pk}/change/'

    submitter_email = approval.submitted_by.email if approval.submitted_by else 'Unknown'
    submitter_name = approval.submitted_by.username if approval.submitted_by else 'Unknown'

    try:
        send_mail(
            subject=f'[VAI] Course Review Request: {approval.course_key}',
            message=(
                f'A course has been submitted for review.\n\n'
                f'Course: {approval.course_key}\n'
                f'Submitted by: {submitter_name} ({submitter_email})\n'
                f'Submitted at: {approval.submitted_at}\n\n'
                f'Review and approve/reject at:\n{admin_url}\n'
            ),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bytecrew.net'),
            recipient_list=[admin_email],
            fail_silently=True,
        )
        log.info('CourseApproval: sent review notification to admin for %s', approval.course_key)
    except Exception:
        log.exception('CourseApproval: failed to send admin notification')


def notify_instructor_of_decision(approval):
    """Send email to instructor when admin approves or rejects their course."""
    if not approval.submitted_by or not approval.submitted_by.email:
        log.warning('CourseApproval: no instructor email for %s', approval.course_key)
        return

    status_text = 'APPROVED' if approval.status == 'approved' else 'REJECTED'
    notes_section = ''
    if approval.reviewer_notes:
        notes_section = f'\nReviewer notes:\n{approval.reviewer_notes}\n'

    if approval.status == 'approved':
        action_text = 'Your course is now visible to students.'
    else:
        action_text = 'Please address the reviewer feedback and resubmit when ready.'

    try:
        send_mail(
            subject=f'[VAI] Your course has been {status_text.lower()}',
            message=(
                f'Your course "{approval.course_key}" has been {status_text}.\n\n'
                f'{action_text}\n'
                f'{notes_section}'
            ),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bytecrew.net'),
            recipient_list=[approval.submitted_by.email],
            fail_silently=True,
        )
        log.info(
            'CourseApproval: sent %s notification to %s for %s',
            status_text, approval.submitted_by.email, approval.course_key,
        )
    except Exception:
        log.exception('CourseApproval: failed to send instructor notification')
