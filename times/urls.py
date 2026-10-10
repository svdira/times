from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
	path('', views.homepage, name='homepage'),
	path('add-item/', views.addItem, name='addItem'),
	path('add-item-atts/<item>', views.addAttrs, name='addAttrs'),	
	path('item/<item>', views.item, name='item'),	
	path('add-seccion/<item>', views.addSeccion, name='addSeccion'),
	path('edit-seccion/<seccion>', views.editSeccion, name='editSeccion'),	
	path('consumir/<item>', views.startConsumo, name='startConsumo'),	
	path('categoria/<c>', views.categoria, name='categoria'),	
	path('finish-consumo/', views.finishConsumo, name='finishConsumo'),	
	path('in-progress/', views.itemInProgress, name='itemInProgress'),
	path('book-history/', views.bookHistory, name='bookHistory'),
	path('book-queue/', views.bookQueue, name='bookQueue'),
	path('edit-item/<item>', views.editItem, name='editItem'),
	path('item/<int:item_id>/add-attribute/', views.add_attribute, name='addAttribute'),
	path('tag/<tag>', views.tag, name='tag'),
	]