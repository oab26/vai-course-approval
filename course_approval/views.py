"""API views for course approval workflow."""

import logging

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from opaque_keys.edx.keys import CourseKey

from .emails import notify_admin_of_submission
from .models import CourseApprovalRequest

log = logging.getLogger(__name__)


def _has_course_access(user, course_key):
    """Check if user has any role on the course."""
    try:
        from common.djangoapps.student.models import CourseAccessRole
        return CourseAccessRole.objects.filter(
            user=user, course_id=course_key
        ).exists()
    except ImportError:
        return False


@csrf_exempt
@require_POST
def submit_for_review(request, course_key_string):
    """Instructor submits their course for admin review."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        course_key = CourseKey.from_string(course_key_string)
    except Exception:
        return JsonResponse({'error': 'Invalid course key'}, status=400)

    if not _has_course_access(request.user, course_key):
        return JsonResponse({'error': 'Access denied'}, status=403)

    approval, created = CourseApprovalRequest.objects.update_or_create(
        course_key=course_key,
        defaults={
            'status': 'pending_review',
            'submitted_by': request.user,
            'submitted_at': timezone.now(),
            'reviewed_by': None,
            'reviewed_at': None,
            'reviewer_notes': '',
        },
    )

    notify_admin_of_submission(approval)

    log.info(
        'CourseApproval: %s submitted %s for review',
        request.user.username, course_key,
    )

    return JsonResponse({
        'status': approval.status,
        'submitted_at': approval.submitted_at.isoformat() if approval.submitted_at else None,
        'message': 'Course submitted for review. The admin team will be notified.',
    })


@csrf_exempt
@require_GET
def get_approval_status(request, course_key_string):
    """Get the current approval status of a course."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        course_key = CourseKey.from_string(course_key_string)
    except Exception:
        return JsonResponse({'error': 'Invalid course key'}, status=400)

    try:
        approval = CourseApprovalRequest.objects.get(course_key=course_key)
        return JsonResponse({
            'status': approval.status,
            'submitted_at': approval.submitted_at.isoformat() if approval.submitted_at else None,
            'reviewed_at': approval.reviewed_at.isoformat() if approval.reviewed_at else None,
            'reviewer_notes': approval.reviewer_notes,
        })
    except CourseApprovalRequest.DoesNotExist:
        return JsonResponse({
            'status': 'none',
            'submitted_at': None,
            'reviewed_at': None,
            'reviewer_notes': '',
        })
