# Generated by Django 5.0.5 on 2024-05-12 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_order_buyer_alter_order_seller_userprofile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='user',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='surname',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
