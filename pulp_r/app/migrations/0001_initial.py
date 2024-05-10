# Generated by Django 4.2.13 on 2024-05-10 19:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0117_task_unblocked_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='RDistribution',
            fields=[
                ('distribution_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.distribution')),
            ],
            options={
                'default_related_name': '%(app_label)s_%(model_name)s',
            },
            bases=('core.distribution',),
        ),
        migrations.CreateModel(
            name='RPublication',
            fields=[
                ('publication_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.publication')),
            ],
            options={
                'default_related_name': '%(app_label)s_%(model_name)s',
            },
            bases=('core.publication',),
        ),
        migrations.CreateModel(
            name='RRemote',
            fields=[
                ('remote_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.remote')),
            ],
            options={
                'default_related_name': '%(app_label)s_%(model_name)s',
            },
            bases=('core.remote',),
        ),
        migrations.CreateModel(
            name='RRepository',
            fields=[
                ('repository_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.repository')),
            ],
            options={
                'default_related_name': '%(app_label)s_%(model_name)s',
            },
            bases=('core.repository',),
        ),
        migrations.CreateModel(
            name='RPackage',
            fields=[
                ('content_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.content')),
                ('name', models.TextField()),
                ('version', models.TextField()),
                ('summary', models.TextField()),
                ('description', models.TextField()),
                ('license', models.TextField()),
                ('url', models.TextField()),
                ('depends', models.JSONField(default=list)),
                ('imports', models.JSONField(default=list)),
                ('suggests', models.JSONField(default=list)),
                ('requires', models.JSONField(default=list)),
            ],
            options={
                'default_related_name': '%(app_label)s_%(model_name)s',
                'unique_together': {('name', 'version')},
            },
            bases=('core.content',),
        ),
    ]