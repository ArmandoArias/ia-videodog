# modules/bedrock_generator.py

import boto3
import json
import logging
from botocore.exceptions import ClientError, BotoCoreError

# Inicializar el cliente de runtime de Bedrock
bedrock_runtime_client = boto3.client('bedrock-runtime', region_name='us-east-1')

def generar_sugerencias_claude_optimizado(transcripcion, titulo_actual):
    user_message =  f"""
Tu tarea es crear tres títulos para un video de YouTube en español, dirigidos a un público latinoamericano (México, Colombia, Perú, etc.), basados en la transcripción y el título actual que te proporciono. Los títulos deben cumplir con las políticas de YouTube y ser atractivos para captar la atención del espectador.

1. **Título 1 (Estructura de éxito)**: El primer título debe seguir la **estructura** de los títulos exitosos proporcionados, manteniendo la idea central del video, pero con un formato similar a los siguientes ejemplos:
- "LE FUE INFIEL A SU ESPOSO CIEGO CON UNA MUJER"
- "SE DEJÓ LLEVAR POR EL DESEO DE ESTE HOMBRE"
- "Nunca te metas con el hijo de un pandillero  #short"
- "LE HICIERON ESTO A LA VECINA BONITA, PERO LA VIDA LES DIO UNA LECCIÓN"
- "MI HERMANA ME TRAICIONO CON MI ESPOSA, EN MI PROPIA CARA"
- "MI HERMANA SE ENAMORO DE MI ESPOSA EN MI PROPIA CASA"
- "ME ENAMORE DE UN VAGABUNDO Y PASO A ESTO"
- "ENCUENTRO A MI ESPOSA EN UN MOTEL CON MI MEJOR AMIGO"
- "Encontre a mi esposo con mi mamá en mi cuarto"
- "MONJAS ENGAÑARON A ESTOS POLICIAS DE ESTA MANERA"
- "NUNCA TE METAS CON EL HIJO DE UN PANDILLERO"
- "EMBARAZO A LA ESPOSA DE SU HIJO A ESCONDIDAS"
- "MUJER DESEABA A OTRO HOMBRE MIENTRAS EL TRABAJABA"
- "SE VOLVIO MILLONARIO DESPUES DE QUE SU ESPOSA LO DEJO Y TRAICIONO POR SER POBRE"
- "ESTE HOMBRE NOS QUERIA ALMORZAR"
- "ENCONTRO A SU ESPOSA CON UN JOVENCITO EN SU CAMA"
- "Niña le cambio la vida a sus papás y a su abuela "
- "MI CUÑADO ME DESEABA Y SE ENAMORO DE MI"
- "SE ALMORZO AL CHOFER DE SU ESPOSO"
- "MI TIO SE ENAMORO DE MI DE ESTA MANERA"
- "SE APROVECHABA DE SU ESPOSO ENFERMO PARA ENTRAR AL VECINO"
- "LE FUI INFIEL A MI ESPOSA ENFERMA POR UNA MÁS JOVÉN"
- "MI NOVIO DESEA A MI MAMÁ EN MI PROPIA CASA"
- "LE FUE INFIEL A SU ESPOSO HUMILDE EN SU GRADO"
- "Chicas jovenes despreciaban a una abuela humilde vendedora de flores  #short"
- "Le regalo un carro y lo descubrio con otra mujer  #short"
- "Madre huye con su hija de su esposo por está razón  #short"
- "ESTA MUJER SE ALMORZO AL SOBRINO DE SU ESPOSO"
- "LO HUMILLABAN POR LIMPIAR VIDRIOS HASTA QUE SALVO LA VIDA DE UNA MUJER Y ESO CAMBIO SU VIDA"
- "MI JEFE SE ENAMORO DE MI Y ME ESPIABA A ESCONDIDAS"
- "MI VECINO ME VISITO A ESCONDIDAS"
- "SE METIO CON LA SUEGRA 20 AÑOS MAYOR QUE EL"
- "LE FUI INFIEL A MI ESPOSA CON LA EMPLEADA DE SERVICIOS"
- "MI CUÑADA ENTRO A MI HABITACIÓN Y PASÓ ESTO"
- "SE VISTIÓ DE LA VIRGEN PARA VER A SU ESPOSO ERA INFIEL CON UNA MUJER MÁS JOVEN"
- "PROFESOR SE ENAMORO DE UNA JOVEN UNIVERSITARIA"
- "CAMBIO A SU ESPOSO HUMILDE POR UN GRINGO"
- "MI ESPOSA SE ENAMORO DE MI PADRE"
- "ME METI CON LA VECINA A ESCONDIDAS"
- "ME ACOSTE CON LA ESPOSA DE MI HIJO"
- "ENCONTRO A SU ESPOSA CON SU AMANTE EN SU PROPIA CASA"
- "ESTA MUJER QUERIA DESHACERSE DE SU ESPOSO ENFERMO"
- "LA VECINA ME QUITO MI MARIDO EN MI PROPIA CARA"
- "MI SUEGRO SE HACIA EL ENFERMO PARA ENAMORARSE DE MI"
- "VAGABUNDO FUE JUZGADO POR SU APARIENCIA EN UN LUJOSO RESTAURANTE"
- "SU NOVIA LO DESPRECIO POR SER POBRE PERO LA VIDA LE DARIA UNA GRAN LECCIÓN"
- "TENGO UNA FANTASIA CON LA VECINA"
- "MI HERMANA ME QUERIA QUITAR A MI ESPOSO"
- "ESTE HOMBRE SE ENAMORABA DE SUS EMPLEADAS DE ESTA MANERA"
- "LE FUI INFIEL A MI ESPOSA CON SU MEJOR AMIGA"
- "ABANDONO A SU ESPOSO Y A SU HIJA RECIEN NACIDA POR SER MECANICO Y LA VIDA LE DIO UNA LECCION"
- "ABANDONO A SU ESPOSO DEL CAMPO POR IRSE CON SU AMANTE"
- "Se enamoró de mi la persona que menos pensaba. #short "
- "ENCONTRO A UNA MUJER EN SU CASA SIN NADA"
- "ENCONTRE A MI PRIMA EN LA CAMA CON MI ESPOSO"
- "LE FUE INFIEL A SU ESPOSO CON EL DUEÑO DE LA CASA"
- "SU JEFE LE DIO TODO EL AMOR A ESCONDIDAS"
- "CAMBIO A SU ESPOSO HUMILDE POR EL JEFE DE EL"
- "HOMBRE LE FUE INFIEL A SU ESPOSA CON UNA MUJER MÁS JOVÉN"
- "LE DEJO SU HERENCIA A SU HIJA ADOPTIVA PERO SUS HERMANOS NO LO PERMITIRIAN"
- "DESCUBRIO A SU HIJO CON LA EMPLEADA DOMESTICA Y LOS ECHO DE LA CASA"
- "EMBARAZO A SU AMANTE Y LE MINTIO A SU ESPOSA"
- "PERDIO A SU ESPOSA POR ESTA TERRIBLE ENFERMEDAD"
- "LE FUI INFIEL A MI ESPOSO CON EL PLOMERO"

2. **Título 2 (Intriga)**: El segundo título debe crear **intriga**, usando emociones como traición, deseo, engaño o sorpresas familiares, pero sin revelar demasiado de la trama.

3. **Título 3 (Creativo y optimizado)**: El tercer título debe ser el más **creativo** y **optimizado** para YouTube, cumpliendo con las políticas, sin ser clickbait, pero muy atractivo. Debes usar mayúsculas en palabras clave importantes para captar la atención del espectador, pero no en todo el título. Este título debe ser breve y directo, pero lo suficientemente intrigante para generar curiosidad.

4. **Resumen**: También proporciona un resumen **detallado** y **atractivo** para el video, que intrigue al espectador sin revelar demasiado de la trama, pero que lo invite a ver el contenido completo. Este resumen debe generar suspense y estar alineado con las políticas de las plataformas. Evita el uso de clickbait o contenido engañoso.

**Título Actual del Video:** {titulo_actual}
**Transcripción del Video:** {transcripcion}

Proporciona lo siguiente en formato JSON:
- "Título Opción 1": Un título alineado con la estructura de los ejemplos proporcionados, pero manteniendo la idea central del título actual.
- "Título Opción 2": Un título intrigante que no revele demasiado pero que evoque emociones fuertes.
- "Título Opción 3": Un título muy creativo, optimizado para YouTube, cumpliendo con las políticas, breve, y usando mayúsculas en palabras clave importantes.
- "Resumen": Un resumen intrigante, detallado, y atractivo que invite a los espectadores a ver el video completo.
"""
    # Crear el payload para la solicitud
    
    conversation = [
        {
            "role": "user",
            "content": [{"text": user_message}]
        }
    ]

    response = bedrock_runtime_client.converse(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        messages=conversation,
        inferenceConfig={
            "maxTokens": 4096,
            "temperature": 0.7
        }
    )

    response_text = response["output"]["message"]["content"][0]["text"]

    # Validar si la respuesta es JSON
    try:
        sugerencias = json.loads(response_text)
        formatted_sugerencias = json.dumps(sugerencias, indent=4, ensure_ascii=False)
        return formatted_sugerencias
    except json.JSONDecodeError:
        return response_text