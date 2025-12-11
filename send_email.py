import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def send_email(to, subject, body):
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 465))

    msg = EmailMessage()
    msg["From"] = email_address
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        print("Email envoyé avec succès !")
    except Exception as e:
        print("Erreur lors de l'envoi :", e)
