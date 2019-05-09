# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.CharField(max_length=50)),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('biz', models.CharField(max_length=30)),
                ('machine_numbers', models.IntegerField()),
                ('celery_id', models.CharField(max_length=30)),
                ('status', models.CharField(default=b'queue', max_length=30)),
                ('argument', models.CharField(max_length=30, null=True, blank=True)),
                ('log', models.TextField(null=True, blank=True)),
                ('result', models.BooleanField(default=False)),
                ('end_time', models.DateTimeField(null=True, blank=True)),
                ('script', models.ForeignKey(to='job_app.Script')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
    ]
