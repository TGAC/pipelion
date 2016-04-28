from django.conf.urls import url, url, include
from django.contrib.auth.decorators import login_required, permission_required
from runner.views import CommandCreate, CommandList, CommandDelete, JobCreate, \
    JobList, JobDelete, LoginOrHome, miso, PipelineCreate, PipelineList, \
    PipelineDelete, run_job


urlpatterns = [
    url('^', include('django.contrib.auth.urls')),
    url(r'^$', LoginOrHome, name='login_or_home'),

    url(r'^miso/$', miso, name='miso'),
    url(r'^new/command/$', login_required(CommandCreate.as_view()), name='command_create'),
    url(r'^new/pipeline/$', login_required(PipelineCreate.as_view()), name='pipeline_create'),
    url(r'^new/job/$', login_required(JobCreate.as_view()), name='job_create'),

    url(r'^list/command/$', login_required(CommandList.as_view()), name='command_list'),
    url(r'^list/pipeline/$', login_required(PipelineList.as_view()), name='pipeline_list'),
    url(r'^list/job/$', login_required(JobList.as_view()), name='job_list'),
    
    url(r'^delete/command/(?P<pk>\d+)/$', login_required(CommandDelete.as_view()), name="command_delete"),
    url(r'^delete/pipeline/(?P<pk>\d+)/$', login_required(PipelineDelete.as_view()), name="pipeline_delete"),
    url(r'^delete/job/(?P<pk>\d+)/$', login_required(JobDelete.as_view()), name="job_delete"),

    url(r'^run/job/(?P<pk>\d+)/$', run_job, name="run_job"),
]