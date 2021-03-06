# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-25 20:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import django_revision.revision_field
import edc_base.model_fields.hostname_modification_field
import edc_base.model_fields.userfield
import edc_base.model_fields.uuid_auto_field
import edc_base.utils


class Migration(migrations.Migration):

    dependencies = [
        ('edc_sync', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReceiveDevice',
            fields=[
                ('created', models.DateTimeField(blank=True, default=edc_base.utils.get_utcnow)),
                ('modified', models.DateTimeField(blank=True, default=edc_base.utils.get_utcnow)),
                ('user_created', edc_base.model_fields.userfield.UserField(blank=True, max_length=50, verbose_name='user created')),
                ('user_modified', edc_base.model_fields.userfield.UserField(blank=True, max_length=50, verbose_name='user modified')),
                ('hostname_created', models.CharField(blank=True, default='mac2-2.local', help_text='System field. (modified on create only)', max_length=50)),
                ('hostname_modified', edc_base.model_fields.hostname_modification_field.HostnameModificationField(blank=True, help_text='System field. (modified on every save)', max_length=50)),
                ('revision', django_revision.revision_field.RevisionField(blank=True, editable=False, help_text='System field. Git repository tag:branch:commit.', max_length=75, null=True, verbose_name='Revision')),
                ('id', edc_base.model_fields.uuid_auto_field.UUIDAutoField(blank=True, editable=False, help_text='System auto field. UUID primary key.', primary_key=True, serialize=False)),
                ('hostname', models.CharField(max_length=200)),
                ('received_by', models.CharField(max_length=100)),
                ('sync_files', models.CharField(max_length=240)),
                ('received_date', models.DateField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ('-received_date',),
            },
        ),
        migrations.RenameField(
            model_name='incomingtransaction',
            old_name='batch_seq',
            new_name='prev_batch_id',
        ),
        migrations.RenameField(
            model_name='outgoingtransaction',
            old_name='batch_seq',
            new_name='prev_batch_id',
        ),
        migrations.AlterUniqueTogether(
            name='receivedevice',
            unique_together=set([('hostname', 'received_date')]),
        ),
    ]
