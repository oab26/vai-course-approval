"""Replace CourseApprovalRequest with CourseNotification."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('course_approval', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(name='CourseApprovalRequest'),
        migrations.CreateModel(
            name='CourseNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_key', opaque_keys.edx.django.models.CourseKeyField(db_index=True, max_length=255)),
                ('notified_at', models.DateTimeField()),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('notified_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('course_key', 'notified_by')},
            },
        ),
    ]
