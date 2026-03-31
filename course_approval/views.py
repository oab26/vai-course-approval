"""API views for course approval workflow."""

import functools
import logging

from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from opaque_keys.edx.keys import CourseKey

from .emails import notify_admin_review_requested
from .models import CourseNotification


def cors_response(response, request=None):
    """Add CORS headers so MFE can call these endpoints cross-origin."""
    origin = ''
    if request:
        origin = request.META.get('HTTP_ORIGIN', '')
    response['Access-Control-Allow-Origin'] = origin or '*'
    response['Access-Control-Allow-Credentials'] = 'true'
    response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken'
    return response


def cors_api(view_func):
    """Decorator that adds CORS headers and handles OPTIONS preflight."""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method == 'OPTIONS':
            response = JsonResponse({})
            return cors_response(response, request)
        response = view_func(request, *args, **kwargs)
        return cors_response(response, request)
    return wrapper

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


def _get_course_name(course_key):
    """Get course display name from modulestore."""
    try:
        from xmodule.modulestore.django import modulestore
        course = modulestore().get_course(course_key)
        return course.display_name if course else str(course_key)
    except Exception:
        return str(course_key)


def _check_user_has_unpublished_changes(user, course_key):
    """
    Check if the given user has made draft edits that are not yet published.

    Walks the course structure and checks each item's draft vs published state.
    Returns True if the user has unpublished changes.
    """
    cache_key = f'course_approval:has_changes:{user.id}:{course_key}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        from xmodule.modulestore.django import modulestore
        from xmodule.modulestore import ModuleStoreEnum

        store = modulestore()
        has_changes = False

        # Get the course with draft branch to see unpublished items
        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course_key):
            course = store.get_course(course_key)
            if not course:
                return False

            # Walk all items in the course
            items = store.get_items(
                course_key,
                revision=ModuleStoreEnum.RevisionOption.draft_only,
            )

            for item in items:
                # Check if this item has unpublished changes
                if not store.has_changes(item):
                    continue

                # Check if the item was last edited by this user
                edited_by = getattr(item, 'edited_by', None)
                if edited_by and str(edited_by) == str(user.id):
                    has_changes = True
                    break

        # Cache for 5 minutes to avoid slow modulestore walks on every page load
        cache.set(cache_key, has_changes, 300)
        return has_changes

    except Exception:
        log.exception('CourseApproval: error checking user changes for %s', course_key)
        return False


@csrf_exempt
@cors_api
def has_changes(request, course_key_string):
    """Check if current user has unpublished changes in the course."""
    if request.method not in ('GET', 'OPTIONS'):
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        course_key = CourseKey.from_string(course_key_string)
    except Exception:
        return JsonResponse({'error': 'Invalid course key'}, status=400)

    # Check for unpublished changes by this user
    has_unpublished = _check_user_has_unpublished_changes(request.user, course_key)

    # Check notification state
    notification_active = False
    last_notified_at = None
    try:
        notif = CourseNotification.objects.get(
            course_key=course_key, notified_by=request.user
        )
        notification_active = notif.is_active
        last_notified_at = notif.notified_at.isoformat() if notif.notified_at else None
    except CourseNotification.DoesNotExist:
        pass

    return JsonResponse({
        'has_unpublished_changes': has_unpublished,
        'notification_active': notification_active,
        'last_notified_at': last_notified_at,
    })


@csrf_exempt
@cors_api
def notify_admin(request, course_key_string):
    """Instructor notifies admin that changes are ready for review."""
    if request.method not in ('POST', 'OPTIONS'):
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        course_key = CourseKey.from_string(course_key_string)
    except Exception:
        return JsonResponse({'error': 'Invalid course key'}, status=400)

    if not _has_course_access(request.user, course_key):
        return JsonResponse({'error': 'Access denied'}, status=403)

    now = timezone.now()

    # Create or update notification
    notif, created = CourseNotification.objects.update_or_create(
        course_key=course_key,
        notified_by=request.user,
        defaults={
            'notified_at': now,
            'published_at': None,  # Reset published state
        },
    )

    # Send email to admin
    course_name = _get_course_name(course_key)
    notify_admin_review_requested(course_key, course_name, request.user)

    log.info(
        'CourseApproval: %s notified admin for %s',
        request.user.username, course_key,
    )

    return JsonResponse({
        'status': 'notified',
        'notified_at': now.isoformat(),
    })
