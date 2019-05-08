# -*- coding: utf-8 -*-

from django.conf.urls import patterns

urlpatterns = patterns(
    'job_app.views',
    (r'^$', 'execute_job'),
    (r'^history/$', 'show_history'),
    (r'^dev-guide/$', 'dev_guide'),
    (r'^contactus/$', 'contactus'),
)
