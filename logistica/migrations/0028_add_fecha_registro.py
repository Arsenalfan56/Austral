import django.utils.timezone
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('logistica', '0027_remove_diagnosticopredictivo_tiempo_total_horas_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrocalibracion',
            name='fecha_registro',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Fecha de Registro'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ordenvibracion',
            name='fecha_registro',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Fecha de Registro'),
            preserve_default=False,
        ),
    ]
