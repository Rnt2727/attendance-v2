from twilio.rest import Client
from django.conf import settings

def enviar_notificaciones_asistencia(estudiante):
    sms_enviado = enviar_sms_asistencia(estudiante)
    return sms_enviado

def enviar_sms_asistencia(estudiante):
    try:
        account_sid = ''
        auth_token = ''
        twilio_phone_number = ''   
        
        client = Client(account_sid, auth_token)

        mensaje = f"Su hijo(a) {estudiante.nombre} {estudiante.apellidos} ha registrado su asistencia a la institución."
        
        message = client.messages.create(
            body=mensaje,
            from_=twilio_phone_number,
            to=f'+51{estudiante.celular_padre}' 
        )
        
        print(f"SMS enviado con SID: {message.sid}")
        return True
        
    except Exception as e:
        print(f"Error al enviar SMS con Twilio: {str(e)}")
        return False
  