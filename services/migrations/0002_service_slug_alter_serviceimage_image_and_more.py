# Generated by Django 5.0.4 on 2025-03-03 05:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='slug',
            field=models.SlugField(blank=True, max_length=100, unique=True, verbose_name='Slug'),
        ),
        migrations.AlterField(
            model_name='serviceimage',
            name='image',
            field=models.ImageField(upload_to='services/static/services/imagenes/', verbose_name='Image'),
        ),
        migrations.AlterField(
            model_name='servicevideo',
            name='video',
            field=models.FileField(upload_to='services/static/services/videos/', verbose_name='Video'),
        ),
    ]
