from __future__ import unicode_literals

from django.db import models

MONITOR_TYPES = ((0, 'No Monitor'), (1, 'Slurm Monitor')) # these need to match up with the list declared in monitors.py
JOB_STATES = ((0, 'not started'), (1, 'running'), (2, 'finished'), (3, 'error'))

class InputKey(models.Model):
    name = models.CharField(max_length=50, unique=True)
    include_val_in_job_title = models.BooleanField(default=False)
    default = models.CharField(max_length=500, blank=True, null=True)
    def __str__(self):
        return self.name

class Command(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)
    command_text = models.CharField(max_length=5000)
    monitor = models.PositiveSmallIntegerField(choices=MONITOR_TYPES, default=0)
    input_keys = models.ManyToManyField(InputKey)
    def __str__(self):
        return self.name
    
class Pipeline(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)
    commands = models.ManyToManyField(Command)

    def __str__(self):
        return self.name

class Job(models.Model):
    """
    A run of a pipeline
    """
    
    name = models.CharField(max_length=150, unique=True)
    description = models.CharField(max_length=200)
    pipeline = models.ForeignKey(Pipeline)
    input = models.CharField(max_length=10000, default='[]')
    log = models.CharField(max_length=10000, null=True, blank=True)
    state = models.PositiveSmallIntegerField(choices=JOB_STATES, default=0, null=True, blank=True)
    scheduler_state = models.CharField(max_length=500, null=True, blank=True)
    can_submit = models.BooleanField(blank=False, null=False, default=True)
    started = models.DateTimeField(blank=True, null=True)
    finished = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

