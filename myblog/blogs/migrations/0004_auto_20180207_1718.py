# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-02-07 17:18
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0003_auto_20171223_1943'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='createdate',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 7, 17, 18, 42, 673251), verbose_name='Create time'),
        ),
        migrations.AlterField(
            model_name='blog',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 7, 17, 18, 42, 673273), verbose_name='Modify time'),
        ),
    ]