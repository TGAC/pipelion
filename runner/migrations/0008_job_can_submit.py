# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-21 16:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runner', '0007_auto_20160421_1115'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='can_submit',
            field=models.BooleanField(default=True),
        ),
    ]
