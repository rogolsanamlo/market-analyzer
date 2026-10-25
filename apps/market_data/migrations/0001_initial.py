import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Asset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("symbol", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=100)),
                ("category", models.CharField(max_length=20)),
                ("unit", models.CharField(max_length=20)),
                ("source", models.CharField(max_length=20)),
                ("source_id", models.CharField(max_length=100)),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="PriceRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("price", models.FloatField()),
                ("recorded_at", models.DateTimeField()),
                ("source", models.CharField(max_length=20)),
                (
                    "asset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prices",
                        to="market_data.asset",
                    ),
                ),
            ],
            options={
                "ordering": ["recorded_at"],
            },
        ),
        migrations.AddIndex(
            model_name="pricerecord",
            index=models.Index(fields=["asset", "recorded_at"], name="price_asset_time_idx"),
        ),
        migrations.AddConstraint(
            model_name="pricerecord",
            constraint=models.UniqueConstraint(fields=("asset", "recorded_at"), name="unique_price_per_time"),
        ),
    ]
