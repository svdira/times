from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
	path('equipo/<equipo>', views.equipo, name='equipo'),
	path('nomina/<equipo>', views.nomina, name='nomina'),
	path('liga/<liga>', views.liga, name='liga'),
	path('liga-equipo/<liga>/<equipo>', views.ligaEquipo, name='ligaEquipo'),
	path('liga-fase/<liga>/<fase>', views.ligaFase, name='ligaFase'),
	path('add-match/<liga>', views.addMatch, name='addMatch'),
	path('edit-match/<partido>', views.editMatch, name='editMatch'),
	path('partido/<p>', views.partido, name='partido'),
	path('futbol/<p>', views.futbol, name='futbol'),
    path('add-contrato/<equipo>', views.addContrato, name='addContrato'),
	path('reg-gol/', views.regGol, name='regGol'),
	path('add-teams/<liga>', views.addTeams, name='addTeams'),
	path('alineacion/<partido>/<equipo>', views.alineacion, name='alineacion'),
	path('add-nota-partido/<p>', views.addnotapartido, name='addnotapartido'),
	path('add-contrato-rapido/', views.addContratoShort, name='addContratoShort'),
	path('equipos/', views.listTeams, name='equipos'),
	path('contrato/<cid>', views.editContrato, name='editContrato'),
	path('match-report/<p>', views.matchreport, name='matchreport'),
	path('add-profile-picture/<contrato>', views.addProfilePicture, name='addprofilepicture'),

	]
