from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import Estudiante, RegistroAsistencia
from django.http import JsonResponse
from .utils import enviar_sms_asistencia
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from django.http import JsonResponse, HttpResponse

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from django.contrib.staticfiles import finders



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
        # Ahora se espera que se envíe el dni en lugar del código de barras
        dni = request.POST.get('dni')
        try:
            # Se busca al estudiante usando el campo dni
            estudiante = Estudiante.objects.get(dni=dni)
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
            dni = request.POST.get('dni')  # Ahora se recibe el dni
            nombre = request.POST.get('nombre')

            if not dni or not nombre:
                raise ValueError("DNI y nombre son campos requeridos")
            
            # Verificar si el dni ya existe
            if Estudiante.objects.filter(dni=dni).exists():
                raise ValueError("El DNI ya está registrado")
            
            # Capturar los nuevos campos
            nivel = request.POST.get('nivel', 'primaria')
            grado = request.POST.get('grado')
            seccion = request.POST.get('seccion')
            
            # Convertir grado a entero si se proporcionó
            grado = int(grado) if grado and grado.isdigit() else None
            
            # Crear el estudiante (ya no se asigna codigo_barras)
            estudiante = Estudiante.objects.create(
                dni=dni,
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
        dni = request.POST.get('dni')
        try:
            estudiante = Estudiante.objects.get(dni=dni)
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
            return JsonResponse({'status': 'error', 'message': 'Estudiante no encontrado'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=400)

@login_required
def exportar_pdf_asistencia(request):
    # Creamos un buffer en memoria para el PDF
    buffer = BytesIO()

    # Definimos la plantilla del documento en orientación horizontal
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), 
                          title="Reporte de Asistencia",
                          topMargin=40,
                          bottomMargin=40)

    # Obtenemos estilos para texto
    styles = getSampleStyleSheet()
    story = []

    # Logo y encabezado
    logo_path = finders.find("images/logo2.jpg")   # Ajusta la ruta según tu estructura
    logo = Image(logo_path, width=120, height=80)
    logo.hAlign = 'CENTER'
    story.append(logo)
    story.append(Spacer(1, 10))

    # Título del colegio
    colegio_style = ParagraphStyle(
        'colegio',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,  # Centrado
        spaceAfter=6,
        textColor=colors.HexColor("#003366")
    )
    colegio = Paragraph("COLEGIO ADVENTISTA JOSÉ PARDO", colegio_style)
    story.append(colegio)

    # Título del reporte
    title_style = ParagraphStyle(
        'title',
        parent=styles['Heading2'],
        fontSize=14,
        alignment=1,
        spaceAfter=12
    )
    title = Paragraph("REPORTE DETALLADO DE ASISTENCIA", title_style)
    story.append(title)

    # Información del reporte
    fecha_style = ParagraphStyle(
        'fecha',
        parent=styles['Normal'],
        fontSize=10,
        alignment=1,
        spaceAfter=24
    )
    fecha_reporte = Paragraph(f"Generado el: {timezone.now().strftime('%d/%m/%Y %H:%M')} | Usuario: {request.user.username}", fecha_style)
    story.append(fecha_reporte)

    # Consultamos los registros de asistencia
    registros = RegistroAsistencia.objects.select_related('estudiante', 'usuario').order_by('-fecha')

    # Definimos la cabecera de la tabla con más columnas
    data = [
        ["N°", "Estudiante", "DNI", "Fecha", "Hora", "Notificación", "Registrado por"]
    ]

    # Agregamos cada registro a la tabla
    for i, reg in enumerate(registros, 1):
        estudiante_nombre = f"{reg.estudiante.nombre} {reg.estudiante.apellidos}"
        fecha = reg.fecha.strftime("%d/%m/%Y")
        hora = reg.fecha.strftime("%H:%M")
        notificacion = "Sí" if reg.notificacion_enviada else "No"
        usuario = reg.usuario.get_full_name() or reg.usuario.username
        data.append([
            str(i),
            estudiante_nombre,
            reg.estudiante.dni,
            fecha,
            hora,
            notificacion,
            usuario
        ])

    # Creamos la tabla con estilo profesional
    table = Table(data, colWidths=[30, 180, 80, 70, 60, 70, 100])
    table.setStyle(TableStyle([
        # Estilo cabecera
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Bordes y relleno
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        
        # Alternar colores de fila
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f9ff")])
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))

    # Pie de página
    footer_style = ParagraphStyle(
        'footer',
        parent=styles['Italic'],
        fontSize=8,
        alignment=2,  # Derecha
        textColor=colors.grey
    )
    footer = Paragraph("Sistema de Gestión de Asistencia - Colegio Adventista José Pardo", footer_style)
    story.append(footer)

    # Construimos el documento
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    # Retornamos el PDF para descarga
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_asistencia_detallado.pdf"'
    response.write(pdf)
    return response