"""CMS middleware to block publish, export, and advanced settings for non-admin users."""

import json
import logging
import re

from django.http import JsonResponse

log = logging.getLogger(__name__)


class CourseApprovalMiddleware:
    """
    Blocks users who are NOT an admin of the course from:
    - Publishing course content (units, sections, subsections)
    - Exporting courses (IP protection)
    - Writing to Advanced Settings (prevents visibility/start date changes)

    A user is treated as an admin (and bypasses all restrictions) if ANY of:
    - Django global staff / superuser (platform-wide admin), OR
    - Studio Course Team "Admin" of the course being acted on — internally the
      course-level ``instructor`` role (CourseInstructorRole).

    Studio Course Team "Staff" (course-level ``staff`` role) is NOT an admin and
    is blocked — those users must use "Notify Admin for Review".
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _course_key_from_path(self, path):
        """Extract the CourseKey a request acts on, from a course-v1 or block-v1 key in the path."""
        from opaque_keys.edx.keys import CourseKey, UsageKey
        m = re.search(r'course-v1:[^/?]+', path)
        if m:
            try:
                return CourseKey.from_string(m.group(0))
            except Exception:
                pass
        m = re.search(r'block-v1:[^/?]+', path)
        if m:
            try:
                return UsageKey.from_string(m.group(0)).course_key
            except Exception:
                pass
        return None

    def _is_course_admin(self, user, course_key):
        """True if the user is a Studio Course Team Admin (instructor role) of this course."""
        if course_key is None:
            return False
        try:
            from common.djangoapps.student.models import CourseAccessRole
            return CourseAccessRole.objects.filter(
                user=user, course_id=course_key, role='instructor'
            ).exists()
        except Exception:
            log.exception('CourseApproval: error checking course-admin role for %s', course_key)
            return False

    def __call__(self, request):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return self.get_response(request)

        # Global staff (superusers/platform admins) bypass all restrictions
        if request.user.is_staff or request.user.is_superuser:
            return self.get_response(request)

        path = request.path
        method = request.method

        # Course Admins (Studio Course Team "Admin" = instructor role) bypass
        # restrictions for THEIR OWN course — they may publish and export it.
        if self._is_course_admin(request.user, self._course_key_from_path(path)):
            return self.get_response(request)

        # Block course export
        if ('/export/' in path or '/course_export/' in path) and method in ('GET', 'POST'):
            log.info(
                'CourseApproval: blocked export for user=%s path=%s',
                request.user.username, path,
            )
            return JsonResponse(
                {'error': 'Course export requires administrator approval. Please contact the VAI admin team.'},
                status=403,
            )

        # Block Advanced Settings writes
        if '/advanced_settings/' in path and method in ('POST', 'PATCH', 'PUT'):
            log.info(
                'CourseApproval: blocked advanced settings write for user=%s path=%s',
                request.user.username, path,
            )
            return JsonResponse(
                {'error': 'Changing advanced settings requires administrator approval. Please contact the VAI admin team.'},
                status=403,
            )

        # Block publish actions on xblocks
        if '/xblock/' in path and method == 'POST':
            if self._is_publish_request(request):
                log.info(
                    'CourseApproval: blocked publish for user=%s path=%s',
                    request.user.username, path,
                )
                return JsonResponse(
                    {'error': 'Publishing requires administrator approval. Please notify the admin for review.'},
                    status=403,
                )

        return self.get_response(request)

    def _is_publish_request(self, request):
        """Check if the POST to /xblock/ is a publish action."""
        try:
            body = request.body.decode('utf-8')
            data = json.loads(body)
            # Studio sends publish actions with "publish" field
            return data.get('publish') in ('make_public', 'make_private')
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            return False
