"""CMS middleware to block publish, export, and advanced settings for non-admin users."""

import json
import logging

from django.http import JsonResponse

log = logging.getLogger(__name__)


class CourseApprovalMiddleware:
    """
    Blocks non-global-staff users from:
    - Publishing course content (units, sections, subsections)
    - Exporting courses (IP protection)
    - Writing to Advanced Settings (prevents visibility/start date changes)

    Django User.is_staff (global admin flag) is checked.
    Course-level "Staff" role does NOT set is_staff — those users are blocked.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return self.get_response(request)

        # Global staff (superusers/admins) bypass all restrictions
        if request.user.is_staff or request.user.is_superuser:
            return self.get_response(request)

        path = request.path
        method = request.method

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
