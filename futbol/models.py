from django.db import models
from datetime import datetime
from django.db import models
from django.utils import timezone
import os
from uuid import uuid4
from django.db.models import Q, Avg, Count, Min, Sum
from random import choice
import markdown
from PIL import Image

class Equipo(models.Model):
    nombre = models.CharField(max_length=250)
    nombre_corto = models.CharField(max_length=15)
    pais = models.CharField(max_length=200)

    def __str__(self):
        return self.nombre

class Jugador(models.Model):
    nombre = models.CharField(max_length=250)
    info = models.TextField()
    pais = models.CharField(max_length=200)

    @property
    def mainPic(self):
        npics = PlayerProfilePic.objects.filter(player=self,tipo='cover').count()
        if npics == 0:
            return None
        else:
            pks = PlayerProfilePic.objects.filter(player=self,tipo='cover').values_list('pk', flat=True)
            random_pk = choice(pks)
            ppic = PlayerProfilePic.objects.get(pk=random_pk)
            return ppic

    def __str__(self):
        return self.nombre

class Contrato(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE)
    fec_ini = models.DateField(null=True, blank=True)
    fec_fin = models.DateField(null=True, blank=True)
    posicion = models.CharField(max_length=200)
    n_posicion = models.IntegerField(default=0)
    dorsal = models.IntegerField()
    last_edited = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.jugador.nombre + ' @ ' + self.equipo.nombre

class Torneo(models.Model):
    nombre = models.CharField(max_length=256)
    region = models.CharField(max_length=200)

    @property
    def npartidos(self):
        con = Partido.objects.filter(torneo=self).count()
        return con

    def __str__(self):
        return self.nombre

class Partido(models.Model):
    fecha = models.DateField()
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE, related_name='partidos')
    local = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='local')
    visita = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='visita')
    fase = models.CharField(max_length=200,default='MD')
    goles_local = models.IntegerField()
    goles_visita = models.IntegerField()
    rondap_local = models.IntegerField()
    rondap_visita = models.IntegerField()
    terminado = models.BooleanField()


    def __str__(self):
        return self.local.nombre + ' v ' + self.visita.nombre + ' @ ' + self.torneo.nombre


    @property
    def gl(self):
        return Gol.objects.filter(partido=self, gol_local=True).count()

    @property
    def gv(self):
        return Gol.objects.filter(partido=self, gol_local=False).count()

    @property
    def headline(self):
        if self.terminado == False:
            return self.local.nombre + ' v ' + self.visita.nombre
        else:
            if (self.rondap_local +  self.rondap_visita) > 0:
                m = f"{self.goles_local}({self.rondap_local}) - ({self.goles_visita}){self.goles_visita}"
            else:
                m = f"{self.goles_local} - {self.goles_visita}"

            return self.local.nombre + f' {m} ' + self.visita.nombre

    @property
    def marcador(self):
        if self.terminado == False:
            m = " vs "
        elif (self.rondap_local +  self.rondap_visita) > 0:
            m = f"{self.goles_local}({self.rondap_local}) - ({self.goles_visita}){self.goles_visita}"
        else:
            m = f"{self.goles_local} - {self.goles_visita}"

        return m

class Gol(models.Model):
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE)
    contrato = models.ForeignKey(Contrato,on_delete=models.CASCADE)
    minuto = models.IntegerField()
    adicional = models.IntegerField()
    penalty = models.BooleanField()
    autogol = models.BooleanField()
    gol_local = models.BooleanField(default=False)

    def __str__(self):
        return self.contrato.jugador.nombre + 'on partido: ' + str(self.partido.id) + ' @ ' + str(self.minuto)


class Alineacion(models.Model):
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    contrato = models.ForeignKey(Contrato,on_delete=models.CASCADE)
    tipo = models.CharField(max_length=75)

    def __str__(self):
        return self.contrato.jugador.nombre + 'on partido: ' + str(self.partido.id)
    
    @property
    def icono(self):
        if self.tipo == 'titularSale':
            # &#128308; (Red circle) or &#9660; (Down arrow) or &#8595; (Simple down arrow)
            i = "<span style='color: #ef4444;'>&#9660;</span>"  # ▼
        elif self.tipo == 'bancaEntra':
            # &#128896; (Green circle) or &#9650; (Up arrow) or &#8593; (Simple up arrow)
            i = "<span style='color: #22c55e;'>&#9650;</span>"  # ▲
        else:
            i = ""
        
        return i

class RelTorneoEquipo(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE)
    def __str__(self):
        return self.equipo.nombre + ' @ ' + self.torneo.nombre

class PlayerProfilePic(models.Model):
    player = models.ForeignKey(Jugador,on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='attr_images/', max_length=255, null=True, blank=True)
    caption = models.TextField()
    tipo = models.CharField(max_length=30)
    vista = models.BooleanField(default=False)


    def save(self, *args, **kwargs):
        # Solo procesa y renombra si es un archivo nuevo/subido (_committed es False)
        if self.imagen and hasattr(self.imagen, 'file') and not getattr(self.imagen, '_committed', False):
            try:
                img = Image.open(self.imagen)

                # Mantener transparencia para PNG o convertir a JPEG
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    formato = 'PNG'
                    ext = '.png'
                else:
                    formato = 'JPEG'
                    ext = '.jpg'
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                # Redimensionar manteniendo proporción (máx 400x400)
                img.thumbnail((400, 400), Image.Resampling.LANCZOS)

                buffer = BytesIO()
                img.save(buffer, format=formato, quality=85, optimize=True)
                buffer.seek(0)

                # Código hexadecimal de 32 caracteres (ej: 4f1a8e2b9c3d4e5f6a7b8c9d0e1f2a3b.jpg)
                hex_name = f"{uuid4().hex}{ext}"

                # Si prefieres una longitud fija más corta (ej: 16 caracteres hex), puedes usar:
                # hex_name = f"{uuid4().hex[:16]}{ext}"

                self.imagen.save(hex_name, ContentFile(buffer.read()), save=False)
            except Exception:
                pass

        super().save(*args, **kwargs)


    def __str__(self):
        return self.player.nombre

class NotaPartido(models.Model):
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE)
    minuto = models.IntegerField()
    comentario = models.TextField()


    def __str__(self):
        return str(self.minuto)+ ' @ '+ self.partido.headline