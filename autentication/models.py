from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

class Camarero(models.Model):
    nombre = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)  # Para que cada camarero tenga un avatar
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Relación con el usuario principal

    def __str__(self):
        return self.nombre

class Reservation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    camarero = models.ForeignKey(Camarero, on_delete=models.SET_NULL, null=True, blank=True)  # Relación con camarero
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    guests = models.PositiveIntegerField()
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)  # Campo para notas adicionales

    def __str__(self):
        return f"{self.name} - {self.date}"
