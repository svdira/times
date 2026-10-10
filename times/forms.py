from django import forms
from .models import AttrText, AttrDate, AttrInteger, AttrDecimal

TYPE_CHOICES = [
    ('text', 'Text'),
    ('date', 'Date'),
    ('integer', 'Integer'),
    ('decimal', 'Decimal'),
]

class AddAttributeForm(forms.Form):
    tipo = forms.ChoiceField(choices=TYPE_CHOICES, label="Tipo de Atributo")
    orden = forms.IntegerField(initial=1, label="Orden")
    att_name = forms.CharField(max_length=255, label="Nombre del Atributo")
    att_value = forms.CharField(label="Valor del Atributo", widget=forms.TextInput())

    def save(self, item):
        tipo = self.cleaned_data['tipo']
        orden = self.cleaned_data['orden']
        name = self.cleaned_data['att_name']
        val = self.cleaned_data['att_value']

        if tipo == 'text':
            return AttrText.objects.create(item=item, orden=orden, att_name=name, att_value=val)
        elif tipo == 'date':
            return AttrDate.objects.create(item=item, orden=orden, att_name=name, att_value=val)
        elif tipo == 'integer':
            return AttrInteger.objects.create(item=item, orden=orden, att_name=name, att_value=int(val))
        elif tipo == 'decimal':
            return AttrDecimal.objects.create(item=item, orden=orden, att_name=name, att_value=float(val))