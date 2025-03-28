from twilio.rest import Client
from django.conf import settings

def enviar_notificaciones_asistencia(estudiante):
    # Enviar SMS usando Twilio
    sms_enviado = enviar_sms_asistencia(estudiante)
    return sms_enviado

def enviar_sms_asistencia(estudiante):
    try:
          
        
        client = Client(account_sid, auth_token)

        mensaje = f"Su hijo(a) {estudiante.nombre} {estudiante.apellidos} ha registrado su asistencia a la institución."
        
        # Enviar SMS - Asegúrate que el número destino esté verificado
        message = client.messages.create(
            body=mensaje,
            from_=twilio_phone_number,
            to=f'+51{estudiante.celular_padre}'  # Formato: +51[9 dígitos]
        )
        
        print(f"SMS enviado con SID: {message.sid}")
        return True
        
    except Exception as e:
        print(f"Error al enviar SMS con Twilio: {str(e)}")
        return False
  