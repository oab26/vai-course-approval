"""Common settings for VAI Course Approval."""


def plugin_settings(settings):
    settings.COURSE_APPROVAL_ADMIN_EMAIL = getattr(
        settings, 'COURSE_APPROVAL_ADMIN_EMAIL', 'admin@bytecrew.net'
    )
