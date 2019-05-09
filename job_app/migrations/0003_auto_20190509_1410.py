# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job_app', '0002_operation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='celery_id',
            field=models.CharField(max_length=100),
        ),
    ]
