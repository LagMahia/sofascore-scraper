import asyncio
import csv
import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from playwright.async_api import async_playwright

# Función para enviar el correo con el archivo adjunto
def enviar_correo(nombre_archivo):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_receiver = os.getenv("EMAIL_RECEIVER")

    mensaje = MIMEMultipart()
    mensaje["From"] = smtp_username
    mensaje["To"] = email_receiver
    mensaje["Subject"] = "📊 Reporte de Partidos Sofascore"

    body = "Adjunto encontrarás el archivo CSV con los partidos recopilados automáticamente por tu scraper de Sofascore."
    mensaje.attach(MIMEText(body, "plain"))

    # Adjuntar archivo
    with open(nombre_archivo, "rb") as f:
        part = MIMEApplication(f.read(), Name=nombre_archivo)
        part['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        mensaje.attach(part)

    # Enviar correo
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(mensaje)
            print(f"✅ Correo enviado exitosamente a {email_receiver}.")
    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")

# Función principal del scraper
async def main():
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"partidos_{fecha_actual}.csv"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.sofascore.com/es/", wait_until="networkidle")

        # Intentar aceptar cookies si aparecen
        try:
            consent_button = await page.wait_for_selector('button:has-text("Consentir")', timeout=5000)
            await consent_button.click()
            print("✅ Consentimiento de cookies aceptado.")
        except:
            print("ℹ️ No apareció el banner de cookies.")

        # Esperar que se carguen los partidos
        try:
            await page.wait_for_selector('[data-testid="events-content"]', timeout=60000)
        except:
            print("⚠️ No se encontraron partidos.")
            await browser.close()
            return

        event_elements = await page.query_selector_all('[data-testid="events-content"] [data-testid="event-item"]')
        print(f"🔍 Partidos encontrados: {len(event_elements)}")

        partidos = []

        for event in event_elements:
            try:
                team_names = await event.query_selector_all('[data-testid="event-participant-name"]')
                teams = [await team.inner_text() for team in team_names]

                time_element = await event.query_selector('[data-testid="event-date"]')
                event_time = await time_element.inner_text() if time_element else "Hora no disponible"

                partidos.append({
                    "Equipo Local": teams[0],
                    "Equipo Visitante": teams[1],
                    "Hora": event_time
                })

            except Exception as e:
                print(f"⚠️ Error procesando un evento: {e}")
                continue

        await browser.close()

        # Guardar el archivo CSV
        if partidos:
            with open(nombre_archivo, mode="w", newline="", encoding="utf-8") as archivo_csv:
                campos = ["Equipo Local", "Equipo Visitante", "Hora"]
                writer = csv.DictWriter(archivo_csv, fieldnames=campos)

                writer.writeheader()
                for partido in partidos:
                    writer.writerow(partido)

            print(f"✅ Partidos guardados en '{nombre_archivo}'.")
            enviar_correo(nombre_archivo)
        else:
            print("⚠️ No se encontraron partidos para guardar.")

if __name__ == "__main__":
    asyncio.run(main())
