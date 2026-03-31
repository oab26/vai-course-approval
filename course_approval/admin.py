"""Django admin — read-only notification log."""

from django.contrib import admin

from .models import CourseNotification


@admin.register(CourseNotification)
class CourseNotificationAdmin(admin.ModelAdmin):
    list_display = ('course_key', 'notified_by', 'notified_at', 'published_at', 'status_display')
    list_filter = ('published_at',)
    search_fields = ('course_key',)
    readonly_fields = ('course_key', 'notified_by', 'notified_at', 'published_at')

    def status_display(self, obj):
        return 'Published' if obj.published_at else 'Pending'
    status_display.short_description = 'Status'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
