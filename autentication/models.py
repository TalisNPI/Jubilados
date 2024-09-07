from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

class Reservation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    guests = models.PositiveIntegerField()
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)  # Campo para notas adicionales

    def __str__(self):
        return f"{self.name} - {self.date}"
