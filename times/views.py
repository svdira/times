from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django import template
from .models import *
from django.db.models import Avg, Count, Min, Sum
from django.db.models import Q, Max
from django.db.models import FloatField
from django.db.models import F
from django.db.models.functions import Round
from django.db.models.functions import Cast
from datetime import datetime
from datetime import date
import math
import random
import re
import locale
from itertools import groupby
from operator import itemgetter
import os

def homepage(request):
	page = request.GET.get('page', 1)
	articles = Item.objects.all().order_by('-fecha_creacion','-fecha_edicion')
	paginator = Paginator(articles, 12)
	resultados = paginator.get_page(page)
	return render(request,'homepage.html',{'articles':resultados})

def categoria(request,c):
	page = request.GET.get('page', 1)
	articles = Item.objects.filter(tipo__id=int(c)).order_by('-fecha_creacion')
	paginator = Paginator(articles, 12)
	resultados = paginator.get_page(page)
	return render(request,'categoria.html',{'articles':resultados})

def tag(request,tag):
	page = request.GET.get('page', 1)
	articles = ItemTag.objects.filter(tag=tag).order_by('-item__fecha_creacion')
	paginator = Paginator(articles, 12)
	resultados = paginator.get_page(page)
	return render(request,'tag.html',{'articles':resultados})

def addItem(request):
	if request.method == 'POST':
		titulo = request.POST.get("titulo")
		preview = request.POST.get("contenido")
		cat_id = int(request.POST.get("categoria"))
		pub_date = request.POST.get("pub_date")
		categoria = Categoria.objects.get(pk=int(cat_id))
		if categoria.nom_categoria == 'journal' and pub_date:
			date_obj = datetime.strptime(pub_date, "%Y-%m-%d")
			titulo = date_obj.strftime("%A, %B %d, %Y")

		newI = Item.objects.create(titulo = titulo, fecha_creacion = pub_date, tipo =categoria, preview=preview)
		newI.save()
		if request.POST.get("tags"):
			for t in request.POST.get("tags").split(","):
				newt = ItemTag.objects.create(item=newI,tag=t)
				newt.save()

		if newI.tipo.nom_categoria == 'book':
			return redirect('addAttrs',item=newI.id)
		else:
			return redirect('item',item=newI.id)


	return render(request,'add-item.html',{})

def addAttrs(request,item):
	this_item = Item.objects.get(pk=int(item))
	if request.method == 'POST':
		if this_item.tipo.nom_categoria == 'book':
			authors = request.POST.get("authors")
			pub_date = request.POST.get("pub_date")
			orig_lan = request.POST.get("orig_lan")
			genres = request.POST.get("genres")
			newF = AttrDate.objects.create(item=this_item,orden = 2,att_name='pub date',att_value=pub_date)
			newF.save()
			for a in authors.split(","):
				newT = AttrText.objects.create(item=this_item,orden=1,att_name='author',att_value=a.strip())
				newT.save()
			newT = AttrText.objects.create(item=this_item,orden=3,att_name='original language',att_value=orig_lan)
			newT.save()
			if len(genres) > 0:
				for g in genres.split(","):
					newT = AttrText.objects.create(item=this_item,orden=4,att_name='genre',att_value=g.strip())
					newT.save()
		return redirect('item',item=this_item.id)


	return render(request,'add-item-atts.html',{'this_item':this_item})


def item(request,item):
	this_item = Item.objects.get(pk=int(item))
	inprogress = Consumo.objects.filter(item=this_item,fec_ini__isnull=False,fec_fin__isnull=True)
	aplica_consumo = 1 if this_item.tipo.nom_categoria in ['book','bunko','manga volume','comic book','magazine issue','anime season','show season','TV miniseries'] else 0
	tags = ItemTag.objects.filter(item=this_item)
	nsecciones = len(this_item.secciones) if this_item.secciones else 0
	return render(request,'item.html',{'this_item':this_item,'tags':tags,'aplica_consumo':aplica_consumo,'inprogress':inprogress,'nsecciones':nsecciones})

def addSeccion(request,item):
	this_item = Item.objects.get(pk=int(item))
	if request.method == 'POST':
		if not(len(request.POST.get("contenido"))>0 and len(request.POST.get("titulo"))>0):
			return redirect('item',item=this_item.id)
		else:
			newS = Seccion.objects.create(item = this_item, titulo = request.POST.get("titulo"), contenido = request.POST.get("contenido"),orden=int(request.POST.get("orden")),tipo=request.POST.get("tipo"))
			newS.save()


		return redirect(f"/item/{this_item.id}")

	return render(request,'add-seccion.html',{'this_item':this_item})

def editSeccion(request,seccion):
	mode = request.GET.get("mode","edit")
	this_seccion = Seccion.objects.get(pk=int(seccion))
	if request.method == 'POST':
		this_seccion.titulo = request.POST.get("titulo")
		this_seccion.contenido = request.POST.get("contenido")
		this_seccion.orden = request.POST.get("orden")
		this_seccion.save()
		return redirect('item',item=this_seccion.item.id)
	return render(request,'edit-seccion.html',{'this_seccion':this_seccion,'mode':mode})

def editItem(request,item):
	this_item = Item.objects.get(pk=int(item))
	this_children = None
	children = ''

	if AttrText.objects.filter(item=this_item,att_name='children_items'):
		this_children = AttrText.objects.filter(item=this_item,att_name='children_items').latest('id')
		children = this_children.att_value

	if request.method == 'POST':
		this_item.titulo = request.POST.get("titulo")
		this_item.preview = request.POST.get("contenido")
		this_item.save()
		if this_children:
			this_children.att_value = request.POST.get("children")
			this_children.save()

		if this_children == None and len(request.POST.get("children"))>1:
			newT = AttrText.objects.create(item=this_item,att_name='children_items',orden=9999,att_value=request.POST.get("children"))
			newT.save()

		if request.POST.get("tags"):
			for t in request.POST.get("tags").split(","):
				newt = ItemTag.objects.create(item=this_item,tag=t)
				newt.save()

		return redirect('item',item=this_item.id)
	return render(request,'edit-item.html',{'this_item':this_item,'children':children})

def startConsumo(request,item):
	this_item = Item.objects.get(pk=int(item))
	if request.method == 'POST':
		fec_ini = request.POST.get("fec_ini")
		fec_fin = request.POST.get("fec_fin")

		if fec_fin:
			newC = Consumo.objects.create(item=this_item,fec_ini=fec_ini,fec_fin=fec_fin)
			this_item.fecha_creacion = fec_fin
			this_item.save()
		else:
			newC = Consumo.objects.create(item=this_item,fec_ini=fec_ini)

		return redirect('item',item=this_item.id)

	return render(request,'consumir.html',{'this_item':this_item})

def finishConsumo(request):
	this_consumo = Consumo.objects.get(pk=int(request.POST.get("con_id")))
	this_consumo.fec_fin = request.POST.get("fec_fin")
	this_consumo.save()
	this_item = Item.objects.get(pk=this_consumo.item.id)
	this_item.fecha_creacion = request.POST.get("fec_fin")
	this_item.save()
	return redirect('item',item=this_consumo.item.id)

def itemInProgress(request):
	item_queue = Item.objects.filter(consumo__fec_ini__isnull=False,consumo__fec_fin__isnull=True)
	return render(request,'item-queue.html',{'item_queue':item_queue})

def bookHistory(request):
	item_queue = Consumo.objects.filter(item__tipo__id=1,fec_fin__isnull=False).order_by('-fec_fin')
	return render(request,'book-history.html',{'item_queue':item_queue,'nbooks':len(item_queue)})

def bookQueue(request):
	item_queue = Item.objects.filter(tipo__id=1,consumo__fec_ini__isnull=True).order_by('titulo')
	return render(request,'book-queue.html',{'item_queue':item_queue})


from django.shortcuts import redirect, get_object_or_404

from .forms import AddAttributeForm

def add_attribute(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if request.method == 'POST':
        form = AddAttributeForm(request.POST)
        if form.is_valid():
            form.save(item=item)
    return redirect('item', item=item.id)
