"""
V1 - 
Fecha: 21/10/2026
Autor: Valeria Rodríguez Morales 
Solicitud:  Crear un programa interactivo en Python que permita al usuario escribir manualmente cualquier código de serie económica de Banxico para
consultar su valor en tiempo real a través de su API oficial. Con estos datos dinámicos, el sistema solicita los valores comerciales correspondientes
para realizar el cálculo del impuesto ISC y, finalmente, pide un correo electrónico destinatario para automatizar el envío del informe final en formato 
de texto plano.
""" 
import os
import time
import random
import requests
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Cargar y asegurar variables de entorno desde el archivo .env
load_dotenv()
TOKEN_BANXICO = os.getenv("TOKEN_BANXICO")
CORREO_REMITENTE = os.getenv("CORREO_REMITENTE")
PASSWORD_APLICACION = os.getenv("PASSWORD_APLICACION")
PUERTO_SMTP = int(os.getenv("PUERTO_SMTP", 587))

def consultar_banxico_universal(serie):
    """
    Consulta una serie económica en tiempo real desde la API oficial de Banxico.
    Args: serie debe ser una cadena de texto alfanumérica que represente el identificador oficial del indicador económico.
    Returns: un diccionario con el valor flotante limpio, su título y su fecha si la consulta es exitosa; o None si ocurre un fallo de red o credenciales.
    """
    serie = serie.strip().upper()
    url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/oportuno"
    headers = {"Bmx-Token": TOKEN_BANXICO, "Accept": "application/json"}

    try:
        print(f"\nConectando con Banxico para la serie: {serie}...")
        respuesta = requests.get(url, headers=headers, timeout=10)

        if respuesta.status_code == 200:
            datos = respuesta.json()
            nodo_serie = datos['bmx']['series'][0]
            info_valores = nodo_serie['datos'][0]
            
            # Limpiador preventivo de comas por si el servidor las incluye
            valor_limpio = info_valores['dato'].replace(",", "").strip()
            
            print("¡Conexión y extracción de datos exitosa!")
            return { "valor": float(valor_limpio), "titulo": nodo_serie['titulo'], "fecha": info_valores['fecha']}
        
        print(f"Error de API: El servidor devolvió el código de estado {respuesta.status_code}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Error de red o conexión con el servidor de Banxico: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        print(f"Error al interpretar la estructura del JSON devuelto: {e}")
        return None

def enviar_email(correo_destino, contenido_reporte, asunto):
    """
    Envía el informe financiero generado en formato de texto plano mediante un servidor SMTP.
    Args: correo_destino como la dirección del destinatario, contenido_reporte con el cuerpo del mensaje y asunto para el encabezado del correo.
    Returns: no devuelve ningún valor tras finalizar el intento de conexión y envío.
    """
    mensaje = MIMEText(contenido_reporte, 'plain', 'utf-8')
    mensaje['Subject'] = asunto
    mensaje['From'] = CORREO_REMITENTE
    mensaje['To'] = correo_destino

    try:
        print(f"Conectando con el servidor de correo seguro de Gmail (Puerto {PUERTO_SMTP})...")
        
        # Conexión adaptada al puerto de tus variables de entorno
        if PUERTO_SMTP == 587:
            servidor = smtplib.SMTP('gmail.com', PUERTO_SMTP, timeout=15)
            servidor.starttls()
        else:
            servidor = smtplib.SMTP_SSL('gmail.com', PUERTO_SMTP, timeout=15)
            
        servidor.login(CORREO_REMITENTE, PASSWORD_APLICACION)
        servidor.sendmail(CORREO_REMITENTE, correo_destino, mensaje.as_string())
        servidor.quit()
        print(f"¡Correo enviado con éxito a {correo_destino}!")
        return

    except Exception as e:
        if "11001" in str(e) or "getaddrinfo" in str(e):
            print("\n[!] Se detectó un micro-corte en el DNS de tu módem.")
            print(f"Activando atajo seguro: Conectando directo a la IP de Google (142.250.138.108) por el puerto {PUERTO_SMTP}...")
            try:
                if PUERTO_SMTP == 587:
                    servidor_ip = smtplib.SMTP('142.250.138.108', PUERTO_SMTP, timeout=15)
                    servidor_ip.starttls()
                else:
                    servidor_ip = smtplib.SMTP_SSL('142.250.138.108', PUERTO_SMTP, timeout=15)
                    
                servidor_ip.login(CORREO_REMITENTE, PASSWORD_APLICACION)
                servidor_ip.sendmail(CORREO_REMITENTE, correo_destino, mensaje.as_string())
                servidor_ip.quit()
                print(f"¡Correo enviado con éxito usando la IP directa a {correo_destino}!")
                return
            except Exception as error_interno:
                print(f"[!] No se pudo conectar usando la IP de respaldo: {error_interno}")
        else:
            print(f"\n[!] Error en el protocolo SMTP o rechazo del servidor: {e}")


def resolver_isc():
    """
    Gestiona todo el flujo interactivo por consola para calcular el Interés sobre Capital utilizando los datos de Banxico.
    Args: no recibe parámetros de entrada.
    Returns: no retorna ningún valor, ya que imprime los resultados directamente en terminal.
    """
    print("\n--- [ 2. CONSULTA TASA CETES Y CÁLCULO ISC ] ---")
    
    # Serie oficial para tasa de CETES 28d
    serie_cetes = "SF60633"  
    
    datos_indicador = consultar_banxico_universal(serie_cetes)
    if not datos_indicador:
        print("No se pudo realizar el cálculo porque falló la consulta a Banxico.")
        return

    try:
        tasa_actual_banxico = datos_indicador["valor"]
        print(f"Trabajando con la tasa oficial: {datos_indicador['titulo']}")
        print(f"Tasa de interés actual del mercado: {tasa_actual_banxico}%")
        
        capital_inicial = float(input("\nIngrese el Capital Inicial (Monto base): $"))
        # FÓRMULA DE INTERÉS SOBRE CAPITAL 
        monto_isc_final = capital_inicial * (tasa_actual_banxico / 100)
        destino = input("¿A qué correo vas a enviar el reporte?: ").strip()

        reporte = (
            f"REPORTE DE CÁLCULO: INTERÉS SOBRE CAPITAL (ISC)\n\n"
            f"REMITENTE: {CORREO_REMITENTE}\n"
            f"DESTINATARIO: {destino}\n\n"
            f"Objetivo Inicial: Calcular el Interés sobre Capital utilizando la tasa vigente de Banxico.\n\n"
            f"Datos del Mercado Financiero:\n"
            f"- Identificador de Serie Banxico: {serie_cetes}\n"
            f"- Concepto Oficial: {datos_indicador['titulo']}\n"
            f"- Tasa de Interés Actual: {tasa_actual_banxico:.2f}% (Fecha: {datos_indicador['fecha']})\n\n"
            f"Resultado de la Evaluación Financiera:\n"
            f"- Capital Inicial Evaluado: ${capital_inicial:.2f} MXN\n"
            f"- Rendimiento / Interés generado (Anual): ${monto_isc_final:.2f} MXN\n\n"
            f"Atentamente,\n"
            f"Sistema de Reportes Python\n"
            f"Fecha de ejecución: {time.strftime('%d/%m/%Y a las %H:%M:%S')}" )
        print("\n" + reporte)
        print("\nEnviando reporte por favor espere...")
        
        asunto_correo = f"Reporte ISC Automatizado - Tasa {tasa_actual_banxico}%"
        enviar_email(destino, reporte, asunto_correo)

    except ValueError:
        print("Error de Validación: Ingrese exclusivamente un valor numérico para el Capital Inicial.")


def menu_principal():
    """
    Despliega el menú iterativo principal del sistema para guiar al usuario por las distintas funciones disponibles.
    Args: no acepta argumentos.
    """
    series_aleatorias = ["SF60633", "SF43718", "SF61745"]

    while True:
        print("\n=== MENÚ DEL PROGRAMA INTERACTIVO ===")
        print("1. Consulta una serie de Banxico aleatoria")
        print("2. Consulta Banxico en la serie relacionada a los CETES para calcular")
        print("3. Salir")
        
        opcion = input("Selecciona una opción (1-3): ").strip()

        if opcion == "1":
            serie_elegida = random.choice(series_aleatorias)
            print(f"\n[Aleatorio] Se ha seleccionado la serie: {serie_elegida}")
            res = consultar_banxico_universal(serie_elegida)
            if res:
                print(f"Resultado -> Título: {res['titulo']} | Valor: {res['valor']}")
        elif opcion == "2":
            resolver_isc()
        elif opcion == "3":
            print("Saliendo del sistema...")
            break
        else:
            print("Opción inválida. Intente de nuevo.")

if __name__ == "__main__":
    menu_principal()
