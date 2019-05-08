# -*- coding: utf-8 -*-

from common.mymako import render_mako_context
from blueking.component.shortcuts import get_client_by_request


def execute_job(request):
    """
    首页
    """
    result, biz_list, message = get_biz_list(request)
    return render_mako_context(request, '/job_app/execute.html', {'biz_list': biz_list})


def show_history(request):
    """
    开发指引
    """
    return render_mako_context(request, '/job_app/history.html')


def get_biz_list(request):
    biz_list = []
    client = get_client_by_request(request)
    kwargs = {
        'fields': ['bk_biz_id', 'bk_biz_name']
    }
    resp = client.cc.search_business(**kwargs)

    if resp.get('result'):
        data = resp.get('data', {}).get('info', {})
        for _d in data:
            biz_list.append({
                'name': _d.get('bk_biz_name'),
                'id': _d.get('bk_biz_id'),
            })
    return resp.get('result'), biz_list, resp.get('message')