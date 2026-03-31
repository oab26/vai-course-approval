"""App configuration for VAI Course Approval."""

from django.apps import AppConfig


class CourseApprovalConfig(AppConfig):
    name = 'course_approval'
    verbose_name = 'Course Approval Workflow'

    plugin_app = {
        'url_config': {
            'cms.djangoapp': {
                'namespace': 'course_approval',
                'regex': r'^api/course-approval/',
                'relative_path': 'urls',
            },
        },
        'settings_config': {
            'cms.djangoapp': {
                'common': {'relative_path': 'settings.common'},
            },
            'lms.djangoapp': {
                'common': {'relative_path': 'settings.common'},
            },
        },
    }

    def ready(self):
        from . import signals  # noqa: F401
