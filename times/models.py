from django.db import models
from datetime import datetime
from django.db import models
from django.utils import timezone
import os
from uuid import uuid4
from django.db.models import Q, Avg, Count, Min, Sum
from random import choice
import markdown
from itertools import chain

class Categoria(models.Model):
    nom_categoria = models.CharField(max_length=255)

    def __str__(self):
        return self.nom_categoria

class Item(models.Model):
    titulo = models.CharField(max_length=255)
    tipo = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    preview = models.TextField()
    fecha_creacion = models.DateField(default='1999-12-31')
    fecha_edicion = models.DateTimeField(auto_now=True)

    def get_attributes_list(self):
        dates = self.attrdate_set.all()
        integers = self.attrinteger_set.all()
        decimals = self.attrdecimal_set.all()
        texts = self.attrtext_set.all().exclude(orden=9999)

        all_attrs = sorted(chain(dates, integers, decimals, texts),key=lambda x: x.orden)
        return [{'orden': attr.orden,'name': attr.att_name,'value': attr.att_value,'type': attr.__class__.__name__} for attr in all_attrs ]

    @property
    def pubyear(self):
        pubdates = AttrDate.objects.filter(item=self,att_name__in=['pub date','premiere','pubdate']).count()
        if pubdates == 0:
            py = ''
        else:
            itm = AttrDate.objects.filter(item=self,att_name__in=['pub date','premiere','pubdate']).latest('id')
            py = str(itm.att_value.year)
        return py

    @property
    def finyear(self):
        pubdates = AttrDate.objects.filter(item=self,att_name__in=['end date','finale','enddate']).count()
        if pubdates == 0:
            py = ''
        else:
            itm = AttrDate.objects.filter(item=self,att_name__in=['end date','finale','enddate']).latest('id')
            py = str(itm.att_value.year)
        return py

    @property
    def periodo(self):
        ini = self.pubyear
        fin = self.finyear
        if ini == '' and fin == '':
            return ''
        elif ini != '' and fin == '':
            return f" ({ini})"
        elif ini != '' and fin != '':
            return f" ({ini}-{fin})"
        else:
            return ''



    @property
    def secciones(self):
        conteo = Seccion.objects.filter(item=self).count()

        if conteo > 0:
            return Seccion.objects.filter(item=self).order_by('-orden','id')
        else:
            return None

    @property
    def consumos(self):
        conteo = Consumo.objects.filter(item=self, fec_fin__isnull=False).count()
        return conteo

    @property
    def authors(self):
        nauthors = AttrText.objects.filter(item=self,att_name='author').count()
        if nauthors > 0:
            txt_authors = ''
            authors = AttrText.objects.filter(item=self,att_name='author')
            for a in authors:
                txt_authors = txt_authors + a.att_value + ', '
            return txt_authors[:-2]
        else:
            return None

    @property
    def members(self):
        import ast

        # Fetch the latest attribute entry in a single SQL query
        item_ids = list(AttrInteger.objects.filter(att_name='parent', att_value=self.id)
        .order_by('id')
        .values_list('item__id', flat=True)
        )

        if item_ids:
            try:
                if isinstance(item_ids, (list, tuple, set)):
                    return Item.objects.filter(id__in=item_ids)
            except (ValueError, SyntaxError):
                pass

        return Item.objects.none() # Returning empty QuerySet is cleaner for Django templates

    def __str__(self):
        return self.titulo


class Seccion(models.Model):
    item = models.ForeignKey(Item, on_delete = models.CASCADE)
    titulo = models.CharField(max_length=512)
    contenido = models.TextField()
    orden = models.IntegerField()
    tipo = models.CharField(max_length=120,default='subitem')

    @property
    def mdOutput(self):
        return(markdown.markdown(self.contenido,extensions=['extra']))

    def __str__(self):
        return self.titulo + ' @ '  + self.item.titulo

class Consumo(models.Model):
    item = models.ForeignKey(Item,on_delete=models.CASCADE,related_name='consumo')
    fec_ini = models.DateField()
    fec_fin = models.DateField(null=True, blank=True)


    def __str__(self):
        return self.item.titulo

class AttrDate(models.Model):
    item = models.ForeignKey(Item,on_delete=models.CASCADE)
    orden = models.IntegerField()
    att_name = models.CharField(max_length=255)
    att_value = models.DateField()

    def __str__(self):
        return self.att_name + ' @ ' + self.item.titulo

class AttrInteger(models.Model):
    item = models.ForeignKey(Item,on_delete=models.CASCADE)
    orden = models.IntegerField()
    att_name = models.CharField(max_length=255)
    att_value = models.IntegerField()

    def __str__(self):
        return self.att_name + ' @ ' + self.item.titulo

class AttrDecimal(models.Model):
    item = models.ForeignKey(Item,on_delete=models.CASCADE)
    orden = models.IntegerField()
    att_name = models.CharField(max_length=255)
    att_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


    def __str__(self):
        return self.att_name + ' @ ' + self.item.titulo


class AttrText(models.Model):
    item = models.ForeignKey(Item,on_delete=models.CASCADE)
    orden = models.IntegerField()
    att_name = models.CharField(max_length=255)
    att_value = models.TextField()

    def __str__(self):
        return self.att_name + ' @ ' + self.item.titulo

class ItemTag(models.Model):
    item = models.ForeignKey(Item,on_delete=models.CASCADE)
    tag = models.CharField(max_length=200)

    def __str__(self):
        return self.tag + ' @ ' + self.item.titulo
