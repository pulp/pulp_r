# Generated by Django 4.2.13 on 2024-05-21 12:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0117_task_unblocked_at'),
        ('r', '0002_rpackagerepositoryversion'),
    ]

    operations = [
        migrations.CreateModel(
            name='RPublishedMetadata',
            fields=[
                ('publishedmetadata_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.publishedmetadata')),
                ('content', models.TextField(blank=True)),
            ],
            options={
                'default_related_name': 'r_published_metadata',
            },
            bases=('core.publishedmetadata',),
        ),
        migrations.AddField(
            model_name='rpackage',
            name='md5sum',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='rpackage',
            name='needs_compilation',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='rpackage',
            name='path',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='rpackage',
            name='priority',
            field=models.TextField(default=''),
        ),
    ]
