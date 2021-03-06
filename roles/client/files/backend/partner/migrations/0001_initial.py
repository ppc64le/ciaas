# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-12 15:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host', models.URLField()),
                ('port', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shortName', models.CharField(max_length=20, verbose_name='Short Name')),
                ('name', models.CharField(max_length=150, verbose_name='Name')),
                ('token', models.CharField(max_length=40)),
            ],
        ),
        migrations.AddField(
            model_name='node',
            name='site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='partner.Partner'),
        ),
    ]
