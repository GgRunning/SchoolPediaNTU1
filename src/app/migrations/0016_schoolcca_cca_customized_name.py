# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-02-09 06:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_schoolcca'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolcca',
            name='cca_customized_name',
            field=models.TextField(null=True),
        ),
    ]
