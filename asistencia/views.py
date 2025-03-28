from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import Estudiante, RegistroAsistencia
from django.http import JsonResponse
from .utils import enviar_sms_asistencia

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import RegistroAsistencia
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import Estudiante, RegistroAsistencia
from django.http import JsonResponse
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .utils import enviar_sms_asistencia


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirige al dashboard en lugar de scanner
    return render(request, 'asistencia/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def scanner_view(request):
    return render(request, 'asistencia/scanner.html')

@login_required
def registrar_asistencia(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        try:
            estudiante = Estudiante.objects.get(codigo_barras=codigo)
            registro = RegistroAsistencia.objects.create(
                estudiante=estudiante,
                usuario=request.user
            )
            
            # Enviar SMS
            if enviar_sms_asistencia(estudiante):
                registro.notificacion_enviada = True
                registro.save()
            
            return JsonResponse({
                'status': 'success', 
                'nombre': f"{estudiante.nombre} {estudiante.apellidos}"
            })
        except Estudiante.DoesNotExist:
            return JsonResponse({
                'status': 'error', 
                'message': 'Estudiante no encontrado'
            })
    return JsonResponse({'status': 'error'})


@login_required
def agregar_estudiante(request):
    if request.method == 'POST':
        try:
            # Validar datos requeridos
            codigo_barras = request.POST.get('codigo_barras')
            nombre = request.POST.get('nombre')

            if not codigo_barras or not nombre:
                raise ValueError("Código de barras y nombre son campos requeridos")
            
            # Verificar si el código de barras ya existe
            if Estudiante.objects.filter(codigo_barras=codigo_barras).exists():
                raise ValueError("El código de barras ya está registrado")
            
            # Capturar los nuevos campos
            nivel = request.POST.get('nivel', 'primaria')
            grado = request.POST.get('grado')
            seccion = request.POST.get('seccion')
            
            # Convertir grado a entero si se proporcionó
            grado = int(grado) if grado and grado.isdigit() else None
            
            # Crear el estudiante
            estudiante = Estudiante.objects.create(
                codigo_barras=codigo_barras,
                dni=request.POST.get('dni'),
                nombre=nombre,
                apellidos=request.POST.get('apellidos'),
                nombre_padre=request.POST.get('nombre_padre'),
                celular_padre=request.POST.get('celular_padre'),
                activo=request.POST.get('activo', 'off') == 'on',
                nivel=nivel,
                grado=grado,
                seccion=seccion
            )
            
            # Determinar si es una solicitud AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'nombre': f"{estudiante.nombre} {estudiante.apellidos or ''}"
                })
            else:
                return redirect('lista_estudiantes')
            
        except Exception as e:
            error_message = str(e)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': error_message
                }, status=400)
            else:
                return render(request, 'asistencia/agregar_estudiante.html', {
                    'error_message': error_message
                })

    return render(request, 'asistencia/agregar_estudiante.html')

@login_required
def dashboard_view(request):
    # Obtener datos para el gráfico de asistencia de los últimos 7 días
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    asistencia_diaria = RegistroAsistencia.objects.filter(
        fecha__range=[start_date, end_date]
    ).values('fecha__date').annotate(
        total=Count('id')
    ).order_by('fecha__date')

    # Preparar datos para el gráfico
    labels = []
    data = []
    for registro in asistencia_diaria:
        labels.append(registro['fecha__date'].strftime('%d/%m'))
        data.append(registro['total'])

    context = {
        'labels': labels,
        'data': data,
        'total_estudiantes': Estudiante.objects.count(),
        'asistencias_hoy': RegistroAsistencia.objects.filter(
            fecha__date=timezone.now().date()
        ).count(),
    }
    return render(request, 'asistencia/dashboard.html', context)