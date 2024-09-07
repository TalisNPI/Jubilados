from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, ReservationForm
from .models import Reservation
from purchases.models import Purchase
from purchases.forms import PurchaseForm
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from itertools import groupby
from operator import attrgetter
import requests
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.timezone import localdate
from django.http import HttpResponseRedirect


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form}) 


def home_view(request):
    # Formularios
    reservation_form = ReservationForm()
    purchase_form = PurchaseForm()

    # Obtener la fecha más reciente que tiene reservas
    latest_date = Reservation.objects.latest('date').date

    # Obtener las últimas 3 reservas de la fecha más reciente
    reservations = Reservation.objects.filter(date=latest_date).order_by('-date', '-id')[:3]

    # Agrupar las reservas por la fecha más reciente (aunque solo habrá una fecha)
    grouped_reservations = {latest_date: reservations}

    # Ordenar las compras por orden alfabético y mostrar solo 3
    purchases = Purchase.objects.all().order_by('item_name')[:3]

    # Calcular el total de comensales y contar el número de reservas (mesas reservadas) para la fecha más reciente
    total_comensales = Reservation.objects.filter(date=latest_date).aggregate(Sum('guests'))['guests__sum'] or 0
    mesas_reservadas = Reservation.objects.filter(date=latest_date).count()  # Contar el número de reservas

    # Calcular el porcentaje de ocupación
    capacidad_total = 55
    porcentaje_ocupacion = (total_comensales / capacidad_total) * 100
    
    # Obtener los datos meteorológicos de Turis (aprox. latitud y longitud)
    weather_info = get_weather_data(latitude=39.3667, longitude=-0.6833)

    
    return render(request, 'home.html', {
        'grouped_reservations': grouped_reservations,
        'purchases': purchases,
        'reservation_form': reservation_form,
        'purchase_form': purchase_form,
        'total_comensales': total_comensales,  # Agregar total_comensales al contexto
        'mesas_reservadas': mesas_reservadas,  # Agregar mesas_reservadas al contexto
        'capacidad_total': capacidad_total,
        'porcentaje_ocupacion': porcentaje_ocupacion,  # Pasar porcentaje de ocupación al contexto
        'weather_info': weather_info  # Pasar la información del clima
    })
    
    
def add_reservation(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.save()
            messages.success(request, 'Reserva añadida con éxito.')
            # Redirige al usuario a la página desde la cual se realizó la solicitud
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.error(request, 'Hubo un error al añadir la reserva. Por favor, revisa el formulario.')
            # En caso de error, redirige también a la misma página
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    else:
        form = ReservationForm()

    return render(request, 'add_reservation.html', {'form': form})


def get_next_saturday():
    today = localdate()
    days_ahead = 5 - today.weekday()  # 5 es sábado (0 es lunes)
    if days_ahead < 0:  # Si ya pasó el sábado, vamos al siguiente
        days_ahead += 7
    next_saturday = today + timedelta(days=days_ahead)
    return next_saturday

def all_reservations_view(request):
    query = request.GET.get('q', None)
    today = localdate()
    latest_date = Reservation.objects.latest('date').date

    if query:
        reservations = Reservation.objects.filter(
            Q(name__icontains=query) & Q(date__gte=today)
        ).order_by('-date')
    else:
        reservations = Reservation.objects.all().order_by('-date')

    # Agrupar las reservas por fecha
    grouped_reservations = {latest_date: reservations}
    grouped_notes = {}

    for date, group in groupby(reservations, key=attrgetter('date')):
        reservations_list = list(group)
        grouped_reservations[date] = reservations_list

        # Recoger las notas de las reservas de este grupo con el nombre del cliente
        notes_list = [{'name': reservation.name, 'note': reservation.notes} 
                      for reservation in reservations_list if reservation.notes]
        if notes_list:
            grouped_notes[date] = notes_list

    # Calcular el total de comensales y contar el número de reservas (mesas reservadas) para la fecha más reciente
    total_comensales = Reservation.objects.filter(date=latest_date).aggregate(Sum('guests'))['guests__sum'] or 0
    mesas_reservadas = Reservation.objects.filter(date=latest_date).count()  # Contar el número de reservas

    # Calcular el porcentaje de ocupación
    capacidad_total = 55
    porcentaje_ocupacion = (total_comensales / capacidad_total) * 100

    reservation_form = ReservationForm()

    return render(request, 'all_reservations.html', {
        'grouped_reservations': grouped_reservations,
        'grouped_notes': grouped_notes,
        'query': query,
        'found_reservations': reservations.exists(),
        'reservation_form': reservation_form,
        'total_comensales': total_comensales,
        'mesas_reservadas': mesas_reservadas,
        'capacidad_total': capacidad_total,
        'porcentaje_ocupacion': porcentaje_ocupacion,
    })


# Vista para editar la reserva
def edit_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    form = ReservationForm(instance=reservation)  # Define 'form' aquí por defecto
    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            return redirect('all_reservations')
    return render(request, 'edit_reservation.html', {'form': form, 'reservation': reservation})


# Vista para eliminar reserva
def delete_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        reservation.delete()
        return redirect('all_reservations')
    return render(request, 'delete_reservation.html', {'reservation': reservation})    



# Vista de la API del tiempo
def get_weather_data(latitude, longitude):
    base_url = 'https://api.open-meteo.com/v1/forecast'
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'daily': 'temperature_2m_max,temperature_2m_min,weathercode',
        'timezone': 'Europe/Madrid'
    }
    
    response = requests.get(base_url, params=params)
    weather_data = response.json()
    
    if response.status_code == 200:
        # Extraer los datos meteorológicos diarios
        daily_data = weather_data.get('daily', {})
        week_data = []
        
        # Iterar sobre los datos diarios para extraer toda la semana
        for i in range(len(daily_data['time'])):
            date_str = daily_data['time'][i]
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Mapeo de código del clima a iconos y descripción
            weather_code = daily_data['weathercode'][i]
            if weather_code in [1, 2]:
                weather_desc = 'Soleado'
                weather_icon = '☀️'
            elif weather_code in [3]:
                weather_desc = 'Parcialmente Nublado'
                weather_icon = '⛅'
            elif weather_code in [45, 48, 51, 53, 55]:
                weather_desc = 'Niebla'
                weather_icon = '🌫️'
            elif weather_code in [61, 63, 65, 80, 81, 82]:
                weather_desc = 'Lluvioso'
                weather_icon = '🌧️'
            else:
                weather_desc = 'Variable'
                weather_icon = '🌤️'
            
            week_data.append({
                'day_name': date_obj.strftime('%A'),  # Nombre del día de la semana en español
                'temperature_max': daily_data['temperature_2m_max'][i],
                'temperature_min': daily_data['temperature_2m_min'][i],
                'weather_desc': weather_desc,
                'weather_icon': weather_icon,
            })
        
        return week_data
    else:
        return None


@require_GET
def get_reservations(request):
    # Filtrar y agrupar las reservas por fecha, sumando el número de comensales
    saturday_reservations = Reservation.objects.filter(date__week_day=7).values('date').annotate(total_guests=Sum('guests'))

    events = []
    for reservation in saturday_reservations:
        events.append({
            'title': f'{reservation["total_guests"]}',
            'start': reservation['date'].isoformat(),
            'end': reservation['date'].isoformat(),
        })

    return JsonResponse(events, safe=False)

def get_reservations_for_date(request):
    date_str = request.GET.get('date')
    if date_str:
        try:
            # Intenta parsear la fecha, esto ayudará a capturar errores de formato.
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            reservations = Reservation.objects.filter(date=date)

            reservation_list = []
            for reservation in reservations:
                reservation_list.append({
                    'id': reservation.id,  # Asegúrate de devolver el ID para las acciones de editar/eliminar
                    'name': reservation.name,
                    'phone': reservation.phone,
                    'guests': reservation.guests,
                })

            return JsonResponse(reservation_list, safe=False)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
    else:
        return JsonResponse({'error': 'Date parameter is missing'}, status=400)