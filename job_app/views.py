# -*- coding: utf-8 -*-

import base64
import datetime
import json
import time
from common.mymako import render_mako_context, render_json, render_mako_tostring
from blueking.component.shortcuts import get_client_by_request
from job_app.models import Script, Operation
from celery.task import task


def execute_job(request):
    """
    首页
    """
    result, biz_list, message = get_biz_list(request)
    scripts = Script.objects.all()
    return render_mako_context(request, '/job_app/execute.html', {'biz_list': biz_list, 'scripts': scripts})


def show_history(request):
    """
    开发指引
    """
    result, biz_list, message = get_biz_list(request)
    scripts = Script.objects.all()
    operators = set(Operation.objects.values_list('user', flat=True))
    return render_mako_context(request, '/job_app/history.html',
                               {'biz_list': biz_list, 'scripts': scripts, 'operators': operators})


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


def get_hosts(request):
    biz_id = request.GET.get("biz_id", 0)
    if biz_id:
        biz_id = int(biz_id)
    else:
        return render_json({
            'result': False,
            'message': "must provide biz_id to get hosts"
        })

    client = get_client_by_request(request)
    resp = client.cc.search_host({
        "page": {"start": 0, "limit": 5, "sort": "bk_host_id"},
        "ip": {
            "flag": "bk_host_innerip|bk_host_outerip",
            "exact": 1,
            "data": []
        },
        "condition": [
            {
                "bk_obj_id": "host",
                "fields": [
                    # "bk_cloud_id",
                    # "bk_host_id",
                    # "bk_host_name",
                    # "bk_os_name",
                    # "bk_os_type",
                    # "bk_host_innerip",
                ],
                "condition": []
            },
            # {"bk_obj_id": "module", "fields": [], "condition": []},
            # {"bk_obj_id": "set", "fields": [], "condition": []},
            {
                "bk_obj_id": "biz",
                "fields": [
                    "default",
                    "bk_biz_id",
                    "bk_biz_name",
                ],
                "condition": [
                    {
                        "field": "bk_biz_id",
                        "operator": "$eq",
                        "value": biz_id
                    }
                ]
            }
        ]
    })
    hosts = [{
        "ip": host['host']['bk_host_innerip'],
        "os": host['host']['bk_os_name'],
        "bk_cloud_id": host['host']['bk_cloud_id'][0]["id"],
    } for host in resp['data']['info']]
    table_data = render_mako_tostring('/job_app/execute_tbody.html', {
        'hosts': hosts,
    })
    return render_json({
        'result': True,
        'data': table_data,
        'message': "success"
    })


def execute(request):
    """执行任务"""

    biz_id = request.POST.get("biz_id")
    script_type = request.POST.get("script_type")
    script_param = request.POST.get("script_param", "")
    ips = request.POST.getlist("ips[]")

    if biz_id:
        biz_id = int(biz_id)

    if script_type:
        script_type = int(script_type)

    try:
        script_content = Script.objects.get(id=script_type).script
    except Script.DoesNotExist:
        return render_json({"result": False, "message": "script not exist!"})

    client = get_client_by_request(request)

    execute_task = run_script.delay(client, biz_id, script_content, script_param, ips)

    opt = Operation.objects.create(
        biz=biz_id,
        script=Script.objects.get(id=script_type),
        machine_numbers=len(ips),
        celery_id=execute_task.id,
        argument=script_param,
        user=request.user.username
    )

    return render_json({"result": True, "data": opt.celery_id, "message": "success"})


@task
def run_script(client, biz_id, script_content, script_param, ips):
    """快速执行脚本"""

    # 执行中
    Operation.objects.filter(celery_id=run_script.request.id).update(
        status="running"
    )

    resp = client.job.fast_execute_script(
        bk_biz_id=biz_id,
        account="root",
        script_param=base64.b64encode(script_param),
        script_content=base64.b64encode(script_content),
        ip_list=[{"bk_cloud_id": 0, "ip": ip} for ip in ips]
    )

    # 启动失败
    if not resp.get('result', False):
        Operation.objects.filter(celery_id=run_script.request.id).update(
            log=json.dumps([resp.get("message")]),
            end_time=datetime.datetime.now(),
            result=False,
            status="start_failed"
        )

    task_id = resp.get('data').get('job_instance_id')
    poll_job_task(client, biz_id, task_id)

    # 查询日志
    resp = client.job.get_job_instance_log(job_instance_id=task_id, bk_biz_id=biz_id)
    ip_logs = resp['data'][0]['step_results'][0]['ip_logs']
    status = resp['data'][0]['status']

    result = True if status == 3 else False
    Operation.objects.filter(celery_id=run_script.request.id).update(
        log=json.dumps(ip_logs),
        end_time=datetime.datetime.now(),
        result=result,
        status="successed" if result else "failed"
    )


def poll_job_task(client, biz_id, job_instance_id):
    """true/false/timeout"""

    count = 0

    res = client.job.get_job_instance_status(job_instance_id=job_instance_id, bk_biz_id=biz_id)

    while res.get('data', {}).get('is_finished') is False and count < 30:
        res = client.job.get_job_instance_status(job_instance_id=job_instance_id, bk_biz_id=biz_id)
        count += 1
        time.sleep(3)

    return res


def get_operations(request):
    """
    Ajax加载操作记录
    """
    biz = request.GET.get('biz')
    script = request.GET.get('script')
    operator = request.GET.get('operator')
    time_range = request.GET.get('timerange')

    operations = Operation.objects.all()
    if biz and biz != 'all':
        operations = operations.filter(biz=int(biz))
    if script and script != 'all':
        operations = operations.filter(script_id=int(script))
    if operator and operator != 'all':
        operations = operations.filter(user=operator)
    if time_range:
        start_time, end_time = time_range.split('~')
        start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        operations = operations.filter(start_time__range=(start_time, end_time))

    data = [opt.to_dict() for opt in operations]
    return render_json({
        'result': True,
        'data': data,
        'message': "success"
    })


def get_log(request, operation_id):
    """查询日志"""

    operation = Operation.objects.get(id=operation_id)

    try:
        logs = json.loads(operation.log)
    except TypeError as e:
        logs = []

    log_content = '<div class="log-content">'
    for log_item in logs:
        job_log_content = log_item.get('log_content')
        log_content += '<div class="ip-start"><prev>IP: {}</prev></div>'.format(log_item.get('ip', ''))
        log_content += ''.join(
            map(lambda x: '<prev>{}</prev><br>'.format(x), job_log_content.split('\n'))
        )
        log_content += '<div class="ip-end"></div>'
    log_content += '</div>'

    return render_json({
        'result': True,
        'data': log_content
    })

