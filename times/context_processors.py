from django.db.models import Count, Case, When, Value, IntegerField
from .models import Categoria

def categories_processor(request):
    tipo_priority = ['book','movie','tv series', 'TV miniseries', 'bunko series', 'manga series']

    custom_tipo_order = Case(
        *[When(nom_categoria=t, then=Value(i)) for i, t in enumerate(tipo_priority)],
        default=Value(len(tipo_priority)),
        output_field=IntegerField()
    )

    return {
        'cats': (
            Categoria.objects.annotate(total_items=Count('item'))
            .filter(total_items__gt=0)
            .order_by(custom_tipo_order, '-total_items')
        ),
        'all_cats': (
            Categoria.objects.annotate(total_items=Count('item'))
            .order_by(custom_tipo_order, '-total_items')
        )
    }
