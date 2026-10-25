from django.contrib import admin

from .models import Asset, PriceRecord


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "category", "unit", "source")
    list_filter = ("category", "source")
    search_fields = ("symbol", "name")


@admin.register(PriceRecord)
class PriceRecordAdmin(admin.ModelAdmin):
    list_display = ("asset", "price", "recorded_at", "source")
    list_filter = ("asset", "source")
    date_hierarchy = "recorded_at"
