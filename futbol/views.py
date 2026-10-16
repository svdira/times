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
from django.shortcuts import render



def addContrato(request,equipo):
	equipo = Equipo.objects.get(pk=int(equipo))

	if request.method == 'POST':
		nombre = request.POST.get("nombre")
		pais = request.POST.get("pais")
		info = request.POST.get("info")

		fec_ini = request.POST.get("fec_ini")
		posicion = request.POST.get("posicion")
		dorsal = request.POST.get("dorsal")

		if posicion == 'arquero':
			n_p = 1
		elif posicion == 'defensa':
			n_p = 2
		elif posicion == 'centrocampista':
			n_p = 3
		elif posicion == 'delantero':
			n_p = 4
		else:
			n_p = 0

		conteo = Jugador.objects.filter(nombre=nombre).count()

		if conteo == 0:
			newJ = Jugador.objects.create(nombre=nombre, pais=pais, info=info)
			newJ.save()

		else:
			newJ = Jugador.objects.filter(nombre=nombre).latest('id')

		newC = Contrato.objects.create(equipo=equipo,jugador=newJ, fec_ini = fec_ini, posicion=posicion,n_posicion=n_p, dorsal=dorsal,last_edited=datetime.today().date())
		newC.save()

		if request.FILES.get("imagen"):
			newIimg = PlayerProfilePic.objects.create(player=newJ, imagen=request.FILES.get("imagen"),caption=newJ.nombre,tipo='cover')
			newIimg.save()



		return redirect(f'/futbol/nomina/{equipo.id}')

	return render(request,'add-contrato.html',{'this_equipo':equipo})

def addProfilePicture(request,contrato):
	this_contrato = Contrato.objects.get(pk=int(contrato))

	if request.FILES.get("imagen"):
		newIimg = PlayerProfilePic.objects.create(player=this_contrato.jugador, imagen=request.FILES.get("imagen"),caption=this_contrato.jugador.nombre,tipo='cover')
		newIimg.save()

	return redirect(f'/futbol/contrato/{contrato}')

def addContratoShort(request):
	equipo = Equipo.objects.get(pk=int(request.POST.get("equipo")))
	partido = Partido.objects.get(pk=int(request.POST.get("partido")))
	nombre = request.POST.get("nombre")

	conteo_x = Jugador.objects.filter(nombre=nombre).count()
	if conteo_x > 0:
		newJ = Jugador.objects.filter(nombre=nombre).latest('id')
	else:
		newJ = Jugador.objects.create(nombre=nombre, pais='TBA', info='TBA')
		newJ.save()

	newC = Contrato.objects.create(equipo=equipo,jugador=newJ, fec_ini = '1999-12-31', posicion='TBA',n_posicion=0, dorsal=0,last_edited=datetime.today().date())
	newC.save()

	return redirect(f"/futbol/alineacion/{partido.id}/{equipo.id}")


def equipo(request,equipo):
	equipo = Equipo.objects.get(pk=int(equipo))
	ligas = Torneo.objects.all().order_by('-id')

	arqueros = Contrato.objects.filter(equipo=equipo, posicion='arquero', fec_fin__isnull=True).order_by('dorsal')
	defensas = Contrato.objects.filter(equipo=equipo, posicion='defensa', fec_fin__isnull=True).order_by('dorsal')
	centros = Contrato.objects.filter(equipo=equipo, posicion='centrocampista', fec_fin__isnull=True).order_by('dorsal')
	delanteros = Contrato.objects.filter(equipo=equipo, posicion='delantero', fec_fin__isnull=True).order_by('dorsal')
	dt = Contrato.objects.filter(equipo=equipo, posicion='dt', fec_fin__isnull=True).order_by('dorsal')

	last_10partidos = Partido.objects.filter(Q(local=equipo) | Q(visita=equipo)).exclude(terminado=False).order_by('-fecha')[0:10]
	partidos = Partido.objects.filter(Q(local=equipo) | Q(visita=equipo)).exclude(terminado=False).order_by('-fecha')[0:50]

	vector_p = ''

	for p in last_10partidos:
		if  p.goles_local == p.goles_visita:
			this_r = '&#129008;'
		elif p.local == equipo and p.goles_local > p.goles_visita:
			this_r = '&#9989;'
		elif p.local == equipo and p.goles_local < p.goles_visita:
			this_r = '&#10060;'
		elif p.visita == equipo and p.goles_local > p.goles_visita:
			this_r = '&#10060;'
		elif p.visita == equipo and p.goles_local < p.goles_visita:
			this_r = '&#9989;'

		vector_p = vector_p + this_r


	ganes=0
	empates = 0
	perdidos = 0
	conteo = len(partidos)
	for p in partidos:
		if  p.goles_local == p.goles_visita:
			empates = empates + 1
		elif p.local == equipo and p.goles_local > p.goles_visita:
			ganes = ganes + 1
		elif p.local == equipo and p.goles_local < p.goles_visita:
			perdidos = perdidos + 1
		elif p.visita == equipo and p.goles_local > p.goles_visita:
			perdidos = perdidos + 1
		elif p.visita == equipo and p.goles_local < p.goles_visita:
			ganes = ganes + 1


	stats = [conteo,ganes,empates,perdidos]

	return render(request,'equipo.html',{'this_equipo':equipo,'arqueros':arqueros,'defensas':defensas, 'centros':centros,'delanteros':delanteros,'vector_p':vector_p,'stats':stats,'dt':dt,'ligas':ligas,'partidos':partidos})




def nomina(request,equipo):
	equipo = Equipo.objects.get(pk=int(equipo))
	ligas = Torneo.objects.all().order_by('-id')

	arqueros = Contrato.objects.filter(equipo=equipo, posicion='arquero', fec_fin__isnull=True).order_by('dorsal')
	defensas = Contrato.objects.filter(equipo=equipo, posicion='defensa', fec_fin__isnull=True).order_by('dorsal')
	centros = Contrato.objects.filter(equipo=equipo, posicion='centrocampista', fec_fin__isnull=True).order_by('dorsal')
	delanteros = Contrato.objects.filter(equipo=equipo, posicion='delantero', fec_fin__isnull=True).order_by('dorsal')
	tba = Contrato.objects.filter(equipo=equipo, posicion='TBA', fec_fin__isnull=True).order_by('dorsal')
	dt = Contrato.objects.filter(equipo=equipo, posicion='dt', fec_fin__isnull=True).order_by('dorsal')

	partidos = Partido.objects.filter(Q(local=equipo) | Q(visita=equipo)).exclude(terminado=False).order_by('-fecha')[0:25]

	vector_p = ''
	for p in partidos:
		if  p.goles_local == p.goles_visita:
			this_r = 'D'
		elif p.local == equipo and p.goles_local > p.goles_visita:
			this_r = 'W'
		elif p.local == equipo and p.goles_local < p.goles_visita:
			this_r = 'L'
		elif p.visita == equipo and p.goles_local > p.goles_visita:
			this_r = 'L'
		elif p.visita == equipo and p.goles_local < p.goles_visita:
			this_r = 'W'

		vector_p = vector_p + this_r


	conteo = len(vector_p)
	ganes = vector_p.count("W")
	empates = vector_p.count("D")
	perdidos = vector_p.count("L")

	stats = [conteo,ganes,empates,perdidos]




	return render(request,'nomina.html',{'this_equipo':equipo,'arqueros':arqueros,'defensas':defensas, 'centros':centros,'delanteros':delanteros,'tba':tba,'vector_p':vector_p,'stats':stats,'dt':dt,'ligas':ligas,'partidos':partidos})



def liga(request,liga):
	ligas = Torneo.objects.all().order_by('-id')
	this_liga = Torneo.objects.get(pk=int(liga))
	pp = Partido.objects.filter(torneo=this_liga, terminado=False).order_by('fecha','id')
	pt = Partido.objects.filter(torneo=this_liga, terminado=True).filter(Q(fase__contains='MD-') | Q(fase__contains='Group')).order_by('-fecha','id')[0:30]
	pe = Partido.objects.filter(torneo=this_liga, terminado=True).exclude(Q(fase__contains='MD-') | Q(fase__contains='Group')).order_by('-fecha','id')
	tabla = None
	if pt:
		tabla = Partido.objects.raw(f"select * from posiciones where id={this_liga.id} order by pts desc, DG desc, GF desc, PJ desc")

	return render(request,'liga.html',{'this_liga':this_liga,'pe':pe,'pp':pp,'pt':pt,'ligas':ligas,'tabla':tabla})


def ligaEquipo(request,liga,equipo):
	ligas = Torneo.objects.all().order_by('-id')
	this_liga = Torneo.objects.get(pk=int(liga))
	this_equipo = Equipo.objects.get(pk=int(equipo))
	pt = Partido.objects.filter(torneo=this_liga, terminado=True).filter(Q(local=this_equipo) | Q(visita=this_equipo)).order_by('-fecha','id')
	tabla = None
	if pt:
		tabla = Partido.objects.raw(f"select * from posiciones where id={this_liga.id} order by pts desc, DG desc, GF desc, PJ desc")

	return render(request,'liga-equipo.html',{'npars':len(pt),'this_liga':this_liga,'this_equipo':this_equipo,'pt':pt,'ligas':ligas})

def ligaFase(request,liga,fase):
	ligas = Torneo.objects.all().order_by('-id')
	this_liga = Torneo.objects.get(pk=int(liga))
	pp = Partido.objects.filter(torneo=this_liga, fase = fase).order_by('fecha','id')
	pt = Partido.objects.filter(torneo=this_liga, fase=fase).order_by('-fecha','id')
	tabla = None
	if pt:
		tabla = Partido.objects.raw(f"select * from posiciones where id={this_liga.id} order by pts desc, DG desc, GF desc, PJ desc")

	return render(request,'liga-fase.html',{'fase':fase,'npars':len(pt),'this_liga':this_liga,'pt':pt,'ligas':ligas,'tabla':tabla})



def addMatch(request,liga):
	this_liga = Torneo.objects.get(pk=int(liga))
	ligas = Torneo.objects.all().order_by('-id')
	equipos = RelTorneoEquipo.objects.filter(torneo=this_liga).order_by('equipo__nombre')
	ult_partido = Partido.objects.latest('id')

	recent_partidos = Partido.objects.filter(torneo=this_liga).order_by('-id')[0:16]

	if request.method == 'POST':
		local = Equipo.objects.get(pk=int(request.POST.get("local")))
		visit = Equipo.objects.get(pk=int(request.POST.get("visit")))
		fase = request.POST.get("fase")
		fecha = request.POST.get("fecha")

		newP = Partido.objects.create(fecha = fecha,torneo = this_liga,  local = local, visita = visit,fase =fase,  goles_local = 0,  goles_visita = 0,  rondap_local = 0,  rondap_visita = 0,    terminado = False)
		newP.save()

		ult_partido = Partido.objects.latest('id')


	return render(request,'add-match.html',{'this_liga':this_liga,'equipos':equipos,'up':ult_partido,'ligas':ligas,'rp':recent_partidos})


def editMatch(request,partido):
	this_partido = Partido.objects.get(pk=int(partido))
	this_liga = Torneo.objects.get(pk=int(this_partido.torneo.id))
	ligas = Torneo.objects.all().order_by('-id')
	equipos = RelTorneoEquipo.objects.filter(torneo=this_liga).order_by('equipo__nombre')
	ult_partido = Partido.objects.latest('id')

	recent_partidos = Partido.objects.filter(torneo=this_liga).order_by('-id')[0:16]

	if request.method == 'POST':
		local = Equipo.objects.get(pk=int(request.POST.get("local")))
		visit = Equipo.objects.get(pk=int(request.POST.get("visit")))
		fase = request.POST.get("fase")
		fecha = request.POST.get("fecha")

		this_partido.fecha = fecha
		this_partido.local = local
		this_partido.visita = visit
		this_partido.fase = fase
		this_partido.save()

		return redirect(f'/futbol/partido/{this_partido.id}')



	return render(request,'edit-match.html',{'this_partido':this_partido,'this_liga':this_liga,'equipos':equipos,'up':ult_partido,'ligas':ligas,'rp':recent_partidos})




def partido(request,p):
	ligas = Torneo.objects.all().order_by('-id')
	this_partido = Partido.objects.get(pk=int(p))
	pl = None
	pv = None
	comms = NotaPartido.objects.filter(partido=this_partido).order_by('minuto')
	contratos_l = None
	contratos_v = None

	goles = Gol.objects.filter(partido=this_partido).order_by('minuto','adicional')

	contratos_l = Contrato.objects.filter(equipo=this_partido.local, fec_fin__isnull=True).order_by('jugador__nombre')

	contratos_v = Contrato.objects.filter(equipo=this_partido.visita, fec_fin__isnull=True).order_by('jugador__nombre')


	next_m = Partido.objects.filter(torneo=this_partido.torneo, fecha__gte=this_partido.fecha,terminado=False).exclude(id=this_partido.id).order_by('fecha','id')

	if request.method == 'POST':
		pl = None
		pv = None
		marcador = request.POST.get("marcador").split("-")
		goles_local = marcador[0].strip()
		goles_visita = marcador[1].strip()

		if len(marcador)==4:
			pl = marcador[2].strip()
			pv = marcador[3].strip()



		this_partido.goles_local = int(goles_local)
		this_partido.goles_visita = int(goles_visita)
		if pl or pv:
			this_partido.rondap_local = int(pl)
			this_partido.rondap_visita = int(pv)
		this_partido.terminado = True
		this_partido.save()

	return render(request,'partido.html',{'comms':comms,'this_partido':this_partido,'next_m':next_m,'ligas':ligas,'contratos_l':contratos_l,'contratos_v':contratos_v,'goles':goles})

def addnotapartido(request,p):
	this_partido = Partido.objects.get(pk=int(p))

	if request.method == 'POST':
		if len(request.POST.get("minuto"))==0:
			minuto = 0
		else:
			minuto = int(request.POST.get("minuto",0))

		comentario = request.POST.get("comment")

		newN = NotaPartido.objects.create(partido = this_partido, minuto = minuto, comentario = comentario)
		newN.save()

		return redirect(f'/futbol/partido/{this_partido.id}')



	return render(request,'add-nota-partido.html',{'this_partido':this_partido})



def futbol(request,p):

	ligas = Torneo.objects.annotate(ultima_fecha=models.Max('partidos__fecha', filter=models.Q(partidos__terminado=True))).order_by('-ultima_fecha')
	conteo_p = Partido.objects.filter(terminado=False).count()

	cm = []
	if p == '0':
		matches = Partido.objects.filter(terminado=False).select_related('torneo').order_by('torneo__nombre', 'fecha')

		if not matches:
			return redirect('/futbol/futbol/1')
		for liga, group in groupby(matches, key=lambda x: x.torneo.nombre):
			group_list = list(group)
			min_fecha = min(p.fecha for p in group_list)
			cm.append({'liga': liga, 'partidos': group_list, 'min_fecha': min_fecha})
		cm.sort(key=lambda x: x['min_fecha'])
	else:
		matches = Partido.objects.filter(terminado=True).select_related('torneo').order_by('torneo__nombre', '-fecha')
		for liga, group in groupby(matches, key=lambda x: x.torneo.nombre):
			group_list = list(group)
			min_fecha = max(p.fecha for p in group_list)
			cm.append({'liga': liga, 'partidos': group_list[0:5], 'min_fecha': min_fecha})
		cm.sort(key=lambda x: x['min_fecha'], reverse=True)


	return render(request,'futbol.html',{'ligas':ligas,'tc':p,'cm':cm[0:8],'recientes':ligas[0:5]})

def regGol(request):
	contrato = request.POST.get("contrato")
	goal_str = request.POST.get("goal_str")
	tipo = request.POST.get("tipo")
	partido = request.POST.get("partido")

	this_partido = Partido.objects.get(pk=int(partido))
	this_contrato = Contrato.objects.get(pk=int(contrato))
	is_local = True if tipo == 'local' else False

	pedazos = goal_str.split(',')

	if len(pedazos) == 1:
		minutos = pedazos[0].split('+')
		if len(minutos) == 1:
			minuto = int(minutos[0])
			adicional = 0
		else:
			minuto = int(minutos[0])
			adicional = int(minutos[1])

		autogol = False
		penalty = False
	elif len(pedazos) == 2:
		minutos = pedazos[0].split('+')
		if len(minutos) == 1:
			minuto = int(minutos[0])
			adicional = 0
		else:
			minuto = int(minutos[0])
			adicional = int(minutos[1])
		attr = pedazos[1]
		if attr.lower() == 'p':
			autogol = False
			penalty = True
		elif attr.lower() == 'a':
			autogol = True
			penalty = False

	if autogol == True:
		this_contrato = Contrato.objects.get(pk=52)


	newG = Gol.objects.create(partido=this_partido,
		contrato=this_contrato,
		minuto=minuto,
		adicional = adicional,
		penalty=penalty,
		autogol=autogol,
		gol_local = is_local
		)
	newG.save()

	return redirect(f"/futbol/partido/{this_partido.id}")

def addTeams(request,liga):
	query = request.GET.get('q', 'all')
	
	this_liga = Torneo.objects.get(pk=int(liga))

	ligas = Torneo.objects.all().order_by('-id')
	listed_teams = RelTorneoEquipo.objects.filter(torneo = this_liga).values_list('equipo__id', flat=True)
	ids_list = list(listed_teams)

	if query == 'all':
		equipos = Equipo.objects.exclude(id__in=ids_list).order_by('nombre')
	else:
		equipos = Equipo.objects.filter(pais=query).exclude(id__in=ids_list).order_by('nombre')

	if request.method == 'POST':
		for e in equipos:
			if e.nombre in request.POST:
				equ = Equipo.objects.get(pk=e.id)
				nL = RelTorneoEquipo.objects.create(torneo=this_liga, equipo = equ)
		return redirect(f'/futbol/liga/{this_liga.id}')

	return render(request,'relacionar.html',{'this_liga':this_liga,'equipos':equipos,'ligas':ligas})

def listTeams(request):


	ligas = Torneo.objects.all().order_by('-id')



	equipos = Equipo.objects.all().order_by('nombre')


	return render(request,'equipos.html',{'equipos':equipos,'ligas':ligas})

def alineacion(request,partido,equipo):
	this_partido = Partido.objects.get(pk=int(partido))
	this_equipo = Equipo.objects.get(pk=int(equipo))
	ligas = Torneo.objects.all().order_by('-id')

	these_alineaciones = Alineacion.objects.filter(partido=this_partido, equipo=this_equipo).order_by('contrato__n_posicion','contrato__dorsal')
	alineaciones = Alineacion.objects.filter(partido=this_partido, equipo=this_equipo).values_list('contrato__id', flat=True)
	ids_list = list(alineaciones)
	contratos = Contrato.objects.filter(equipo=this_equipo).exclude(id__in=ids_list).exclude(posicion='dt').order_by('jugador__nombre')

	if request.method == 'POST':
		for c in contratos:
			if str(c.id) in request.POST:
				tipo = request.POST.get(str(c.id))
				this_contrato = Contrato.objects.get(pk=c.id)

				newA = Alineacion.objects.create(partido=this_partido, equipo=this_equipo, contrato=this_contrato, tipo= tipo)
				newA.save()
		return redirect(f"/futbol/alineacion/{this_partido.id}/{this_equipo.id}")


	return render(request,'alineacion.html',{'this_partido':this_partido,'contratos':contratos,'ligas':ligas,'this_equipo':this_equipo,'alineaciones':these_alineaciones})


def editContrato(request,cid):
	from django.db.models import Count
	from django.db.models.functions import ExtractYear
	this_contrato = Contrato.objects.get(pk=int(cid))
	this_jugador = Jugador.objects.get(pk=this_contrato.jugador.id)

	goles = Gol.objects.filter(contrato = this_contrato).annotate(anio=ExtractYear('partido__fecha')).values('anio').annotate(total=Count('id')).order_by('-anio')
	partidos = Alineacion.objects.filter(contrato=this_contrato).annotate(anio=ExtractYear('partido__fecha')).values('anio').annotate(total=Count('id')).order_by('-anio')

	if request.method == 'POST':
		this_jugador.pais = request.POST.get("pais")
		this_jugador.info = request.POST.get("info")
		this_jugador.save()

		if len(request.POST.get("fec_ini"))==10:
			this_contrato.fec_ini = request.POST.get("fec_ini")
		if len(request.POST.get("fec_fin"))==10:
			this_contrato.fec_fin = request.POST.get("fec_fin")
		this_contrato.posicion = request.POST.get("posicion")
		this_contrato.dorsal = int(request.POST.get("dorsal"))

		this_contrato.save()

		return redirect(f'/futbol/nomina/{this_contrato.equipo.id}')


	return render(request,'edit-contrato.html',{'this_contrato':this_contrato,'this_jugador':this_jugador,'goles':goles,'partidos':partidos})


def matchreport(request,p):
	this_partido = Partido.objects.get(pk=int(p))

	goles = Gol.objects.filter(partido=this_partido).order_by('minuto','adicional')
	alineacion = Alineacion.objects.filter(partido=this_partido,equipo__id=1)
	alineacion2 = Alineacion.objects.filter(partido=this_partido,equipo__id=2)
	comms = NotaPartido.objects.filter(partido=this_partido).order_by('minuto')

	portero = Alineacion.objects.filter(partido=this_partido,equipo__id=1, contrato__posicion='arquero')
	defensas = Alineacion.objects.filter(partido=this_partido,equipo__id=1, contrato__posicion='defensa')
	medios = Alineacion.objects.filter(partido=this_partido,equipo__id=1, contrato__posicion='centrocampista')
	delanteros = Alineacion.objects.filter(partido=this_partido,equipo__id=1, contrato__posicion='delantero')


	portero2 = Alineacion.objects.filter(partido=this_partido,equipo__id=2, contrato__posicion='arquero')
	defensas2 = Alineacion.objects.filter(partido=this_partido,equipo__id=2, contrato__posicion='defensa')
	medios2 = Alineacion.objects.filter(partido=this_partido,equipo__id=2, contrato__posicion='centrocampista')
	delanteros2 = Alineacion.objects.filter(partido=this_partido,equipo__id=2, contrato__posicion='delantero')

	return render(request,'match-report.html',{'comms':comms,'this_partido':this_partido,'goles':goles,'alineacion':alineacion,'alineacion2':alineacion2,'portero':portero,'defensas':defensas,'medios':medios,'delanteros':delanteros,'portero2':portero2,'defensas2':defensas2,'medios2':medios2,'delanteros2':delanteros2})
