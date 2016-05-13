# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-12 13:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runner', '0014_inputkey_include_val_in_job_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='finished',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='started',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
