from django.contrib import admin

from .models import Command, Pipeline, Job, InputKey

admin.site.register(InputKey)
admin.site.register(Command)
admin.site.register(Pipeline)
admin.site.register(Job)