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
import requests
import json
from decimal import Decimal
from django.db import transaction


from django.db.models import Q

def search_items(request):
    query = request.GET.get('q', '').strip()
    articles = []

    if query:
        items_by_title = Item.objects.filter(titulo__icontains=query)


        items_by_preview = Item.objects.filter(preview__icontains=query)


        sections = Seccion.objects.filter(
            Q(titulo__icontains=query) | Q(contenido__icontains=query)
        )
        items_by_section = Item.objects.filter(seccion__in=sections)


        articles = list(items_by_title | items_by_preview | items_by_section)

    page = request.GET.get('page', 1)
    paginator = Paginator(articles, 12)
    resultados = paginator.get_page(page)

    return render(request, 'search.html', {'articles': resultados, 'query': query})

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
	return render(request,'tag.html',{'articles':resultados,'this_tag':tag})

def addItem(request):
    parent = int(request.GET.get('parent', 0))
    if request.method == 'POST':
        titulo = request.POST.get("titulo")
        preview = request.POST.get("contenido")
        cat_id = int(request.POST.get("categoria"))
        categoria = Categoria.objects.get(pk=int(cat_id))
        if categoria.nom_categoria in ['book','tv series','TV miniseries','bunko','manga volume','comic book','anime series','show season']:
            pub_date = '1999-12-31'
        else:
            pub_date = request.POST.get("pub_date")

        if categoria.nom_categoria == 'journal' and pub_date:
            date_obj = datetime.strptime(pub_date, "%Y-%m-%d")
            titulo = date_obj.strftime("%A, %B %d, %Y")

        newI = Item.objects.create(titulo=titulo, fecha_creacion=pub_date, tipo=categoria, preview=preview)
        newI.save()

        if parent > 0:
            newT = AttrInteger.objects.create(item=newI, att_name='parent', orden=9999, att_value=parent)
        # Procesar imagen
        if 'imagen' in request.FILES:
            AttrImage.objects.create(
                item=newI,
                imagen=request.FILES['imagen'],
                att_name='cover',
                orden=1
            )

        if request.POST.get("tags"):
            for t in request.POST.get("tags").split(","):
                newt = ItemTag.objects.create(item=newI, tag=t.strip())
                newt.save()

        if newI.tipo.nom_categoria == 'book':
            return redirect('addAttrs', item=newI.id)
        else:
            return redirect('item', item=newI.id)

    this_parent = None
    if parent > 0:
        this_parent = Item.objects.get(pk=parent)

    return render(request, 'add-item.html', {'this_parent':this_parent})

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
	aplica_consumo = 1 if this_item.tipo.nom_categoria in ['book','bunko','movie','manga volume','comic book','magazine issue','anime season','show season','TV miniseries'] else 0
	tags = ItemTag.objects.filter(item=this_item)
	nsecciones = len(this_item.secciones) if this_item.secciones else 0
	this_parent = None
	if AttrInteger.objects.filter(item=this_item, att_name='parent').count() > 0:
	    obj_parent = AttrInteger.objects.filter(item=this_item, att_name='parent').latest('id')
	    this_parent = Item.objects.get(pk=obj_parent.att_value)
	return render(request,'item.html',{'this_item':this_item,'tags':tags,'aplica_consumo':aplica_consumo,'inprogress':inprogress,'nsecciones':nsecciones,'this_parent':this_parent})

def addSeccion(request,item):
	this_item = Item.objects.get(pk=int(item))
	if request.method == 'POST':
		if not(len(request.POST.get("contenido"))>0 and len(request.POST.get("titulo"))>0):
			return redirect('item',item=this_item.id)
		else:
			newS = Seccion.objects.create(item = this_item, titulo = request.POST.get("titulo"), contenido = request.POST.get("contenido"),orden=int(request.POST.get("orden")),tipo=request.POST.get("tipo"))
			newS.save()
			if 'imagen' in request.FILES:
			    AttrImageSeccion.objects.create(seccion=this_seccion,imagen=request.FILES['imagen'],att_name='cover', orden=1)


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
		if 'imagen' in request.FILES:
		    AttrImageSeccion.objects.create(seccion=this_seccion,imagen=request.FILES['imagen'],att_name='cover', orden=1)
		return redirect('item',item=this_seccion.item.id)
	return render(request,'edit-seccion.html',{'this_seccion':this_seccion,'mode':mode})

def editItem(request, item):
    this_item = Item.objects.get(pk=int(item))
    parent = None
    parent_id = 0

    if AttrInteger.objects.filter(item=this_item, att_name='parent'):
        parent = AttrInteger.objects.filter(item=this_item, att_name='parent').latest('id')
        parent_id = parent.att_value

    if request.method == 'POST':
        this_item.titulo = request.POST.get("titulo")
        this_item.preview = request.POST.get("contenido")
        this_item.save()

        if parent_id > 0:
            parent.att_value = int(request.POST.get("parent"))
            parent.save()

        if parent is None and len(request.POST.get("parent", "")) > 1:
            newT = AttrInteger.objects.create(item=this_item, att_name='parent', orden=9999, att_value=int(request.POST.get("parent")))
            newT.save()

        if request.POST.get("tags"):
            for t in request.POST.get("tags").split(","):
                newt = ItemTag.objects.create(item=this_item, tag=t.strip())
                newt.save()

        # Actualizar o crear imagen
        if 'imagen' in request.FILES:
            AttrImage.objects.create(
                item=this_item,
                imagen=request.FILES['imagen'],
                att_name='cover',
                orden=1)

        return redirect('item', item=this_item.id)


    return render(request, 'edit-item.html', {
        'this_item': this_item,
        'parent': parent_id
    })

def startConsumo(request,item):
	this_item = Item.objects.get(pk=int(item))
	if request.method == 'POST':
		fec_ini = request.POST.get("fec_ini")
		fec_fin = request.POST.get("fec_fin")

		if fec_fin:
			newC = Consumo.objects.create(item=this_item,fec_ini=fec_ini,fec_fin=fec_fin)
			this_item.fecha_creacion = fec_fin
			this_item.save()
		elif this_item.tipo.nom_categoria == 'movie':
			newC = Consumo.objects.create(item=this_item,fec_ini=fec_ini,fec_fin=fec_ini)
			this_item.fecha_creacion = fec_ini
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

from django.db.models import Count
from django.db.models.functions import ExtractYear

def bookHistory(request):
    con_cats = Categoria.objects.filter(id__in=[1, 2, 4, 5, 9, 10])
    this_cat = request.GET.get('cat', 1)
    now_cat = Categoria.objects.get(pk=int(this_cat))

    # Base queryset for the category
    item_queue = Consumo.objects.filter(
        item__tipo__id=this_cat,
        fec_fin__isnull=False
    )

    # Optional year filtering
    this_year = request.GET.get('year')
    if this_year:
        item_queue = item_queue.filter(fec_fin__year=this_year)

    item_queue = item_queue.order_by('-fec_fin')

    # Counts (respecting the year filter if applied)
    total_count = item_queue.count()
    distinct_count = item_queue.values('item__id').distinct().count()

    # Get available years annotated with their total count of consumos
    available_years = (
        Consumo.objects.filter(item__tipo__id=this_cat, fec_fin__isnull=False)
        .annotate(year=ExtractYear('fec_fin'))
        .values('year')
        .annotate(count=Count('id'))
        .order_by('-year')
    )

    return render(request, 'book-history.html', {
        'item_queue': item_queue,
        'total_count': total_count,
        'distinct_count': distinct_count,
        'con_cats': con_cats,
        'now_cat': now_cat,
        'available_years': available_years,
        'selected_year': this_year,
    })

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

def addMovie(request):
	if request.method == 'POST':
		movie_id = request.POST.get("code")
		url = "https://api.themoviedb.org/3/movie/{}?language=en-US".format(movie_id)
		headers = {
			"accept": "application/json",
			"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NmM4MjVlMDFiY2RiMWQ1NWQ4YjRmYzNiNDQ0ODFhZiIsInN1YiI6IjYwMWM1NmFkNzMxNGExMDAzZGZjMzhiOSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.vnpzsejhhlKDqssAg1dHiMH64Ja4_bP2UPcJFgHrW3k"
		}

		response = requests.get(url, headers=headers)
		movie_dict = json.loads(response.text)
		str_titulo = movie_dict['original_title']
		str_overview = movie_dict['overview']
		str_premiere = movie_dict['release_date']
		str_runtime= movie_dict['runtime']
		categoria = Categoria.objects.get(pk=2)
		newI = newI = Item.objects.create(titulo = str_titulo, fecha_creacion =  str_premiere, tipo =categoria, preview=str_overview)
		newI.save()
		newT = AttrDate.objects.create(item=newI,orden=1,att_name='premiere',att_value=str_premiere)
		newT.save()



		url = "https://api.themoviedb.org/3/movie/{}/credits?language=en-US".format(movie_id)


		response = requests.get(url, headers=headers)
		movie_dict_2 = json.loads(response.text)
		for c in movie_dict_2['crew']:
			if c['job']=='Director':
				newT = AttrText.objects.create(item=newI,orden=2,att_name='director',att_value=c['original_name'])
				newT.save()

		for c in movie_dict_2['cast'][0:25]:
			newt = ItemTag.objects.create(item=newI,tag=c['original_name'])
			newt.save()

		return redirect("item",item=newI.id)



	return render(request,'add-movie.html',{})


from decimal import Decimal

def addGasto(request):
    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        cuenta_id = int(request.POST.get('cuenta'))
        tipo_origen = int(request.POST.get('tipo_origen'))
        origen = int(request.POST.get('origen'))
        monto = Decimal(request.POST.get('monto'))
        descripcion = request.POST.get('descripcion', '').strip()

        cuenta = CuentaGasto.objects.get(pk=cuenta_id)

        TrxGasto.objects.create(
            fecha=fecha,
            cuenta=cuenta,
            origen=origen,
            tipo_origen=tipo_origen,
            monto=monto,
            descripcion=descripcion
        )

        # Optional: Automatically update saldo when registering an expense
        if tipo_origen == 1:  # Deposito (reduces available funds)
            dep = Depositos.objects.get(pk=origen)
            dep.saldo -= monto
            dep.save()
        elif tipo_origen == 2:  # LineaCredito (increases debt balance)
            lc = LineaCredito.objects.get(pk=origen)
            lc.saldo += monto
            lc.save()

        return redirect('addGasto')

    categorias = CategoriaGastos.objects.prefetch_related('cat_gasto').all().order_by('categoria')
    depositos = Depositos.objects.all().order_by('nombre')
    lineas_credito = LineaCredito.objects.all().order_by('nombre')
    ultimos_gastos = TrxGasto.objects.select_related('cuenta', 'cuenta__categoria').order_by('-fecha', '-id')[:10]

    return render(request, 'add-gasto.html', {
        'categorias': categorias,
        'depositos': depositos,
        'lineas_credito': lineas_credito,
        'ultimos_gastos': ultimos_gastos,
        'today': date.today().strftime('%Y-%m-%d'),
    })

from decimal import Decimal

def addIngreso(request):
    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        tipo_destino = int(request.POST.get('tipo_destino'))
        destino = int(request.POST.get('destino'))
        monto = Decimal(request.POST.get('monto'))

        TrxIngreso.objects.create(
            fecha=fecha,
            destino=destino,
            tipo_destino=tipo_destino,
            monto=monto,
        )
        if tipo_destino == 1:
            dep = Depositos.objects.get(pk=destino)
            dep.saldo += monto
            dep.save()
        elif tipo_destino == 2:  # LineaCredito (reduces debt balance)
            lc = LineaCredito.objects.get(pk=destino)
            lc.saldo -= monto
            lc.save()

        return redirect('addIngreso')

    depositos = Depositos.objects.all().order_by('nombre')
    lineas_credito = LineaCredito.objects.all().order_by('nombre')
    ultimos_ingresos = TrxIngreso.objects.all().order_by('-fecha', '-id')[:10]

    # Map IDs to names for displaying recent entries cleanly in the sidebar
    dep_map = {d.id: f"{d.nombre} ({d.entidad})" for d in depositos}
    lc_map = {lc.id: f"{lc.nombre} ({lc.entidad})" for lc in lineas_credito}

    ingresos_display = []
    for ing in ultimos_ingresos:
        if ing.tipo_destino == 1:
            nombre_destino = dep_map.get(ing.destino, f"Depósito #{ing.destino}")
            tipo_label = "Depósito"
        else:
            nombre_destino = lc_map.get(ing.destino, f"Línea de Crédito #{ing.destino}")
            tipo_label = "Línea de Crédito"

        ingresos_display.append({
            'id': ing.id,
            'fecha': ing.fecha,
            'monto': ing.monto,
            'destino_nombre': nombre_destino,
            'tipo_label': tipo_label,
        })

    return render(request, 'add-ingreso.html', {
        'depositos': depositos,
        'lineas_credito': lineas_credito,
        'ultimos_ingresos': ingresos_display,
        'today': date.today().strftime('%Y-%m-%d'),
    })


def _resolve_account_label(tipo, acc_id, dep_map, lc_map):
    if tipo == 1:
        return dep_map.get(acc_id, f"Depósito #{acc_id}"), "Depósito"
    return lc_map.get(acc_id, f"Línea de Crédito #{acc_id}"), "Línea de Crédito"


def addTransfer(request):
    depositos = Depositos.objects.all().order_by('nombre')
    lineas_credito = LineaCredito.objects.all().order_by('nombre')
    dep_map = {d.id: f"{d.nombre} ({d.entidad})" for d in depositos}
    lc_map = {lc.id: f"{lc.nombre} ({lc.entidad})" for lc in lineas_credito}

    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        tipo_origen = int(request.POST.get('tipo_origen'))
        origen = int(request.POST.get('origen'))
        tipo_destino = int(request.POST.get('tipo_destino'))
        destino = int(request.POST.get('destino'))
        monto = Decimal(request.POST.get('monto'))

        with transaction.atomic():
            # Adjust source account balance
            if tipo_origen == 1:
                dep_src = Depositos.objects.select_for_update().get(pk=origen)
                dep_src.saldo -= monto
                dep_src.save()
            elif tipo_origen == 2:
                lc_src = LineaCredito.objects.select_for_update().get(pk=origen)
                lc_src.saldo += monto
                lc_src.save()

            # Adjust destination account balance
            if tipo_destino == 1:
                dep_dst = Depositos.objects.select_for_update().get(pk=destino)
                dep_dst.saldo += monto
                dep_dst.save()
            elif tipo_destino == 2:
                lc_dst = LineaCredito.objects.select_for_update().get(pk=destino)
                lc_dst.saldo -= monto
                lc_dst.save()

            # Record inflow/payment on destination
            TrxIngreso.objects.create(
                fecha=fecha,
                destino=destino,
                tipo_destino=tipo_destino,
                monto=monto,
            )

        return redirect('addTransfer')

    recent_ingresos = TrxIngreso.objects.all().order_by('-fecha', '-id')[:10]
    ingresos_display = []
    for ing in recent_ingresos:
        nombre, tipo_label = _resolve_account_label(ing.tipo_destino, ing.destino, dep_map, lc_map)
        ingresos_display.append({
            'id': ing.id,
            'fecha': ing.fecha,
            'monto': ing.monto,
            'destino_nombre': nombre,
            'tipo_label': tipo_label,
        })

    return render(request, 'add-transfer.html', {
        'depositos': depositos,
        'lineas_credito': lineas_credito,
        'ultimos_movimientos': ingresos_display,
        'today': date.today().strftime('%Y-%m-%d'),
    })


def financeDashboard(request):
    depositos = Depositos.objects.all().order_by('nombre')
    lineas_credito = LineaCredito.objects.all().order_by('nombre')

    total_depositos = sum((d.saldo for d in depositos), Decimal('0.00'))
    total_deuda = sum((lc.saldo for lc in lineas_credito), Decimal('0.00'))
    posicion_neta = total_depositos - total_deuda

    dep_map = {d.id: f"{d.nombre} ({d.entidad})" for d in depositos}
    lc_map = {lc.id: f"{lc.nombre} ({lc.entidad})" for lc in lineas_credito}

    gastos = TrxGasto.objects.select_related('cuenta', 'cuenta__categoria').order_by('-fecha', '-id')[:10]
    total_gastos = TrxGasto.objects.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    ingresos_raw = TrxIngreso.objects.all().order_by('-fecha', '-id')[:10]
    total_ingresos = TrxIngreso.objects.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    ingresos = []
    for ing in ingresos_raw:
        nombre, tipo_label = _resolve_account_label(ing.tipo_destino, ing.destino, dep_map, lc_map)
        ingresos.append({
            'id': ing.id,
            'fecha': ing.fecha,
            'monto': ing.monto,
            'destino_nombre': nombre,
            'tipo_label': tipo_label,
        })

    return render(request, 'finance-dashboard.html', {
        'depositos': depositos,
        'lineas_credito': lineas_credito,
        'total_depositos': total_depositos,
        'total_deuda': total_deuda,
        'posicion_neta': posicion_neta,
        'gastos': gastos,
        'ingresos': ingresos,
        'total_gastos': total_gastos,
        'total_ingresos': total_ingresos,
    })