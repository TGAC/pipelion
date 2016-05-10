import StringIO
from datetime import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.core import exceptions
import json
from runner.models import Command, Pipeline, Job, JOB_STATES
from subprocess import CalledProcessError
import subprocess
import thread
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from runner.monitors import monitors, decodestatus
import drmaa
from django.http import JsonResponse
# Non-restful API for integration


def _get_data_for_state(jobs, serialize=True):
    rtn = []
    for job in jobs:
        jobject = {'id': job.pk, 
            'name': job.name,
            'log': job.log,
            'statusMessage': job.scheduler_state,
            'startDate': job.last_run,
            'pipeline': {'name': job.pipeline.name,
                'processes': []
            }
        }
        for command in job.pipeline.commands.all():
            jobject['pipeline']['processes'].append({'name': command.name})
        rtn.append(jobject)
    if serialize:
        return JsonResponse(rtn, safe=False)
    else:
        return rtn

def get_completed_jobs(request):
    """
    Returns all jobs that have been marked by the scheduler as completed.
    """

    jobs = Job.objects.filter(scheduler_state=decodestatus[drmaa.JobState.DONE]).filter(state=2)
    return _get_data_for_state(jobs)

def get_failed_jobs(request):
    """
    Returns all jobs that have been marked by the scheduler as failed.
    """
    #TODO: add jobs failed for other reasons
    jobs = Job.objects.filter(scheduler_state=decodestatus[drmaa.JobState.FAILED]) | Job.objects.filter(state=3)

    return _get_data_for_state(jobs.distinct())

def get_running_jobs(request):
    """
    Returns all jobs that have been marked by the scheduler as running.
    """

    running_jobs = Job.objects.filter(scheduler_state=decodestatus[drmaa.JobState.RUNNING]).filter(state__in=(1,2))

    return _get_data_for_state(running_jobs)

def get_pending_jobs(request):
    """
    Returns all jobs that have been marked by the scheduler as pending.
    """
    
    jobs = Job.objects.filter(scheduler_state__in=[decodestatus[drmaa.JobState.QUEUED_ACTIVE],
        decodestatus[drmaa.JobState.SYSTEM_ON_HOLD],
        decodestatus[drmaa.JobState.USER_ON_HOLD],
        decodestatus[drmaa.JobState.USER_SYSTEM_ON_HOLD],
        decodestatus[drmaa.JobState.UNDETERMINED]]) | Job.objects.filter(state=0)

    return _get_data_for_state(jobs.distinct())

def get_jobs(request):
    """
    Return all the jobs!
    """
    raise NotImplementedError()
    #return _serialize_objs(Job.objects.all())

def get_job(request):
    """
    Get a job by id.
    POST should look like:
    `{
        'query': 'getPipeline',
        'params': {
           'name': 'taskid'
       }
    }`
    """
    raise NotImplementedError()
#     params = json.loads(request.POST.get('params'))
#     name = params.get("name")
#     return _serialize_objs([Job.objects.get(pk=name)])

def get_pipeline(request):
    """
    Get a pipeline by name.
    POST should look like:
    `{
        'query': 'getPipeline',
        'params': {
           'name': 'pipeline name'
       }
    }`
    """
    rtn = {}
    params = request.POST.get('params')
    name = params.get("name")

    pipeline = Pipeline.objects.get(name=name)
    rtn['name'] = pipeline.name
    processes = []
    all_required_parameters = []
    for command in pipeline.commands.all():
        input_keys = []
        for input_key in command.input_keys.all():
            input_obj = { 'name': input_key.name, 'default_text': input_key.default }
            if input_obj not in input_keys:
                input_keys.append(input_obj)
            if input_obj not in all_required_parameters:
                all_required_parameters.append(input_obj)
        processes.append({'name': command.name, 'parameters': input_keys})
    rtn['processes'] = processes
    rtn['allRequiredParameters'] = all_required_parameters
    return JsonResponse(rtn, safe=False) 

def get_pipelines(request):
    """
    Return all pipeline objects.
    """
    rtn = []
    for pipeline in Pipeline.objects.all():
        obj = {}
        obj['name'] = pipeline.name
        obj['processes'] = []
        for command in pipeline.commands.all():
            obj['processes'].append(command.name)
        rtn.append(obj)
        
    return JsonResponse(rtn, safe=False) 
        
    #return _serialize_objs(Pipeline.objects.all())

def submit_job(request):
    """
    Creates a job from a request object and submits it.
    The request should contain everything needed to start a job:
    """

    print 'POST {}'.format(request.POST)
    print 'params {}'.format(request.POST.get('params'))
    description = "pipelion submitted job"

    request.POST = request.POST.get('submitTask')

    pipeline_name = request.POST.get("pipeline")
    params = request.POST.get("params")
    run = True
    name = "miso {} - {}".format(pipeline_name, datetime.now())
    if "name" in params:
        name = params.get("name")
    if "description" in params:
        description = params.get("description")
    if "run" in params:
        run = params.get("run")
    job = Job(name=name, description=description, pipeline=Pipeline.objects.get(name=pipeline_name))
    # be clever and only store params that are associated input keys.
    input_arr = []

    for command in job.pipeline.commands.all():
        for input_key in command.input_keys.all():
            obj = { input_key.name: params.get(input_key.name) }
            if obj not in input_arr:
                input_arr.append(obj)
    job.input = json.dumps(input_arr)
    job.save()
    if run:
        run_job(None, job.pk)
    rtn = {'success': True, 'id': job.pk}
    return JsonResponse(rtn, safe=False) 


@csrf_exempt
def miso(request):
    """
    Marshalls between miso specific API methods based on query.
    """

    query = ''

    if 'submitTask' not in  request.POST and 'query' not in  request.POST:
        # it came from miso.  Fix post.
        request.POST = json.loads(request.body)

    if request.POST.get('submitTask'):
        query = 'submitTask'
    elif request.POST.get('query'):
        query = request.POST.get('query')
    else:
        pass

    views = {
        "getCompletedTasks": get_completed_jobs,
        "getFailedTasks": get_failed_jobs,
        "getPendingTasks": get_pending_jobs,
        "getPipeline": get_pipeline,
        "getPipelines": get_pipelines,
        "getRunningTasks": get_running_jobs,
        "getTask": get_job,
        "getTasks": get_jobs,
        "submitTask": submit_job,
    }

    result = views[query](request)
    print  'GETTING {} '.format( query )
    print 'Returning {} '.format( result ) 
    return result
# end of miso specific code.

def run_job(request, pk):
    success_url = '/runner/list_job'
    def run_commands(job):
        # run each command in the pipeline
        job.last_run = datetime.now()
        job.state = 1
        job.log = ""
        job.save()
        job_log = {}
        commands_executed = []
        for command in job.pipeline.commands.all():
            command_log = { 'messages': {}, 'system_errors': []}
            command_log.get('messages')['start_time'] = str(datetime.now())
            std_out = ""
            std_err = ""
            exit_code = ""
            success = False
            raw_command = command.command_text
            input = json.loads(job.input)
            for item in input:
                for placeholder, value in item.iteritems():
                    raw_command = raw_command.replace(placeholder, value)

            command_log.get('messages')['raw_command'] = raw_command
            polling = False
            try:
                p = subprocess.Popen(raw_command, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                std_out, std_err = p.communicate()
                exit_code = p.returncode
                if command.monitor != 0:
                    monitor = monitors.get(command.monitor)()
                    ref = monitor.get_job_reference(std_out)
                    command_log.get('messages')['scheduler_ref'] = ref
                    command_log.get('messages')['monitoring'] = command.monitor
                    job_log[command.name] = command_log
                    job.log = json.dumps(job_log)
                    job.save()
                    polling = True
                    success = _retry_command(3,job, std_out, monitor)
                else:
                    success = True
            except CalledProcessError as cpe:
                exit_code = cpe.returncode
                command_log['system_errors'].append(str(e))
            except OSError as ose:
                exit_code = ose.errno
                command_log['system_errors'].append(str(ose))
            except Exception as ex:
                exit_code = -1
                command_log['system_errors'].append(str(ex))
            finally:
                polling = False
                command_log.get('messages')['std_out'] = std_out
                command_log.get('messages')['std_err'] = std_err
                command_log.get('messages')['exit_code'] = exit_code
                command_log.get('messages')['end_time'] = str(datetime.now())

                command_log['success'] = success
                job_log[command.name] = command_log
                job.log = json.dumps(job_log)
                job.save()
                if not success:
                    job.state = 3
                    break;
        if job.state != 3:
            job.state = 2
        job.log = json.dumps(job_log)
        job.save()
    job = Job.objects.get(id=pk)
    thread.start_new_thread (run_commands, (job,))

    return redirect('job_list')

def _retry_command(retries, job, std_out, monitor):
    success = False
    for i in range(0, retries):
        while True: 
            try:
                success = monitor.monitor(job, std_out)
            except Exception as try_ex:
                if i == retries:
                    print 'Giving up {}, tried {} times.'.format(job.name, retries)
                    raise try_ex
                else:
                    print 'Retrying, caught a {}'.format(try_ex)
                    continue
            break
    return success
# Views for pipelion ui

class CommandList(ListView):
    queryset = Command.objects.order_by('-id')
    model = Command
    def get_context_data(self, **kwargs):
        context = super(CommandList, self).get_context_data(**kwargs)
        return context

class CommandCreate(CreateView):
    model = Command
    success_url = '/'
    fields = ['name', "description", "command_text"]

class CommandDelete(DeleteView):
    model = Command
    success_url = '/list/command'

class JobCreate(CreateView):
    success_url = '/list/job'
    model = Job
    fields = ['name', "description", "pipeline"]
    def post(self, request):
        new_model = Job()
        new_model.name = request.POST.get('name')
        new_model.description = request.POST.get('description')
        new_model.input = request.POST.get('input_json')
        new_model.pipeline = Pipeline.objects.get(pk=request.POST.get('pipeline'))
        new_model.save()
        return HttpResponseRedirect(self.success_url)

class JobList(ListView):
    queryset = Job.objects.order_by('-id')
    model = Job
    def get_context_data(self, **kwargs):
        context = super(JobList, self).get_context_data(**kwargs)
        return context

class JobDelete(DeleteView):
    model = Job
    success_url = '/list/job'

class PipelineList(ListView):
    model = Pipeline
    def get_context_data(self, **kwargs):
        context = super(PipelineList, self).get_context_data(**kwargs)
#         context['now'] = timezone.now()
        return context

class PipelineCreate(CreateView):
    success_url = '/list/pipeline'
    model = Pipeline
    fields = ['name', "description"]
    def post(self, request):
        new_model = Pipeline()
        new_model.name = request.POST.get('name')
        new_model.description = request.POST.get('description')
        new_model.save()
        commands = request.POST.getlist('commands[]')
        for command in commands:
            new_model.commands.add(command)
        new_model.save()
        return HttpResponseRedirect(self.success_url)
    def get_context_data(self, **kwargs):
        context = super(PipelineCreate, self).get_context_data(**kwargs)
        context['commands']= Command.objects.all()
        return context

class PipelineDelete(DeleteView):
    model = Pipeline
    success_url = '/list/pipeline'

def Login(request):
    success_url = '/runner/list_job'

def LoginOrHome(request):
    if request.user.is_authenticated():
        return redirect('job_list')
    else:
        return redirect('/login')
