# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-23 18:28
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Users',
            fields=[
                ('username', models.CharField(max_length=8, primary_key=True, serialize=False, unique=True, verbose_name='用户名')),
                ('password', models.CharField(max_length=16, verbose_name='密码')),
                ('logoimage', models.ImageField(blank=True, null=True, upload_to='logoimages', verbose_name='头像')),
                ('birthday', models.DateTimeField(blank=True, null=True, verbose_name='生日')),
                ('email', models.CharField(blank=True, max_length=255, null=True, verbose_name='电子邮件')),
                ('mobilephone', models.CharField(blank=True, max_length=11, null=True, verbose_name='手机号码')),
                ('registertime', models.DateTimeField(default=datetime.datetime(2017, 12, 23, 18, 28, 29, 567298))),
            ],
        ),
    ]
