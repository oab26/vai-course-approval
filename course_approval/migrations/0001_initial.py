"""Initial migration for course_approval."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseApprovalRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_key', opaque_keys.edx.django.models.CourseKeyField(db_index=True, max_length=255, unique=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('pending_review', 'Pending Review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='draft', max_length=20)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('reviewer_notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('submitted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_courses', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_courses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Course Approval Request',
                'verbose_name_plural': 'Course Approval Requests',
            },
        ),
    ]
