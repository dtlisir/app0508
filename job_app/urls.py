# -*- coding: utf-8 -*-

from django.conf.urls import patterns

urlpatterns = patterns(
    'job_app.views',
    (r'^$', 'execute_job'),
    (r'^history/$', 'show_history'),
    (r'^api/get_hosts/$', 'get_hosts'),
    (r'^api/execute/$', 'execute'),
    (r'^api/get_operations/$', 'get_operations'),
    (r'^api/get_log/(?P<operation_id>\d+)/$', 'get_log'),
)
