from django.contrib import admin
from .models import Camarero

@admin.register(Camarero)
class CamareroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'usuario')
    search_fields = ('nombre',)
