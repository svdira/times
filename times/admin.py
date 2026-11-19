from django.contrib import admin
from .models import *

admin.site.register(Categoria)
admin.site.register(Item)
admin.site.register(Seccion)
admin.site.register(Consumo)
admin.site.register(AttrDate)
admin.site.register(AttrInteger)
admin.site.register(AttrDecimal)
admin.site.register(AttrText)
admin.site.register(ItemTag)
admin.site.register(AttrImage)
admin.site.register(LineaCredito)
admin.site.register(Depositos)
admin.site.register(CategoriaGastos)
admin.site.register(CuentaGasto)
admin.site.register(TrxGasto)
admin.site.register(TrxIngreso)


