# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-23 18:28
from __future__ import unicode_literals

import ckeditor_uploader.fields
import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=32, verbose_name='标题')),
                ('content', ckeditor_uploader.fields.RichTextUploadingField(verbose_name='内容')),
                ('createdate', models.DateTimeField(default=datetime.datetime(2017, 12, 23, 18, 28, 29, 576741), verbose_name='Create time')),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 12, 23, 18, 28, 29, 576766), verbose_name='Modify time')),
                ('readcount', models.IntegerField(default=0)),
                ('commentcount', models.IntegerField(default=0)),
                ('draft', models.BooleanField(default=True)),
                ('auther', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='users.Users')),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('categoryname', models.CharField(max_length=8, unique=True)),
                ('blogcount', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('createtime', models.DateTimeField(verbose_name='Comment Create time')),
                ('attachedblog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blogs.Blog')),
                ('auther', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='users.Users')),
            ],
        ),
        migrations.AddField(
            model_name='blog',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='blogs.Category'),
        ),
    ]
