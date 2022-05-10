# Generated by Django 4.0.4 on 2022-05-10 12:12

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import web.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name_plural': 'Users',
                'ordering': ['username'],
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('token', models.CharField(default=web.models.Agent.token, max_length=50, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=100)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('port', models.IntegerField(blank=True, default=8080, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(65535)])),
                ('status', models.CharField(blank=True, choices=[('OK', 'OK'), ('WR', 'WARNING'), ('BA', 'BAD'), ('UN', 'UNREACHEABLE')], default='OK', max_length=20)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Hosts',
                'ordering': ['ip'],
            },
        ),
        migrations.CreateModel(
            name='Metric',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('status', models.JSONField()),
                ('metrics', models.JSONField()),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metrics', to='web.agent')),
            ],
            options={
                'verbose_name_plural': 'Metrics',
                'ordering': ['created'],
            },
        ),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('cpu_percent', models.FloatField(default=None, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('ram_percent', models.FloatField(default=None, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('processes', models.JSONField(default=None, null=True)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='web.agent')),
            ],
            options={
                'verbose_name_plural': 'Alerts',
                'ordering': ['created'],
            },
        ),
        migrations.CreateModel(
            name='AgentConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logging_filename', models.CharField(default='monitor.log', max_length=100)),
                ('logging_level', models.CharField(choices=[('debug', 'Debug'), ('info', 'Informative'), ('warning', 'Warning'), ('error', 'Error'), ('critical', 'Critical Error')], default='info', max_length=9)),
                ('metrics_enable_logfile', models.BooleanField(default=False)),
                ('metrics_get_endpoint', models.BooleanField(default=False)),
                ('metrics_log_filename', models.CharField(default='metrics.json', max_length=100)),
                ('metrics_post_interval', models.PositiveIntegerField(default=60, validators=[django.core.validators.MinValueValidator(1)])),
                ('threshold_cpu_percent', models.PositiveIntegerField(default=50, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('threshold_ram_percent', models.PositiveIntegerField(default=30, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('uvicorn_backlog', models.PositiveIntegerField(default=2048)),
                ('uvicorn_debug', models.BooleanField(default=False)),
                ('uvicorn_host', models.GenericIPAddressField(default='0.0.0.0')),
                ('uvicorn_log_level', models.CharField(choices=[('trace', 'Trace'), ('debug', 'Debug'), ('info', 'Informative'), ('warning', 'Warning'), ('error', 'Error'), ('critical', 'Critical Error')], default='trace', max_length=9)),
                ('uvicorn_port', models.PositiveIntegerField(default=8080, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(65535)])),
                ('uvicorn_reload', models.BooleanField(default=True)),
                ('uvicorn_timeout_keep_alive', models.PositiveIntegerField(default=5)),
                ('uvicorn_workers', models.PositiveIntegerField(default=4)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='web.agent')),
            ],
            options={
                'verbose_name_plural': 'Hosts config',
                'ordering': ['agent'],
            },
        ),
    ]
