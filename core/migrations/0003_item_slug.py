# Generated by Django 2.2.8 on 2020-03-09 22:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20200309_2213'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='slug',
            field=models.SlugField(null=True, unique=True),
        ),
    ]