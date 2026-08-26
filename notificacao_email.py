import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from database.db_manager import JobDatabase

logger = logging.getLogger(__name__)

def enviar_relatorio_email():
    email_remetente = os.getenv("EMAIL_REMETENTE")
    senha_app = os.getenv("EMAIL_SENHA_APP")
    email_destinatario = os.getenv("EMAIL_DESTINATARIO", email_remetente)

    if not email_remetente or not senha_app:
        logger.warning("⚠️ Variáveis EMAIL_REMETENTE ou EMAIL_SENHA_APP não configuradas no .env. Pulando envio de e-mail.")
        return

    logger.info("Preparando relatório de vagas para envio por e-mail...")
    db = JobDatabase()
    vagas_processadas = db.obter_todas_vagas() 
    
    # Filtra vagas com score >= 70 (Boas oportunidades)
    vagas_boas = [v for v in vagas_processadas if v.get('Score', 0) >= 70]
    # Ordena por score decrescente
    vagas_boas.sort(key=lambda x: x.get('Score', 0), reverse=True)

    if not vagas_boas:
        logger.info("Nenhuma vaga com score >= 70 encontrada para enviar no relatório.")
        return

    assunto = f"Relatório Job Hunter - {len(vagas_boas)} Excelentes Oportunidades Encontradas!"
    
    corpo_html = f"""
    <html>
    <head></head>
    <body style="font-family: Arial, sans-serif;">
        <h2>Olá Lucas,</h2>
        <p>O seu robô caçador de vagas encontrou <b>{len(vagas_boas)}</b> oportunidades altamente aderentes ao seu perfil!</p>
        <hr>
    """

    for vaga in vagas_boas[:15]:
        corpo_html += f"""
        <div style="margin-bottom: 20px;">
            <h3 style="color: #2e6c80;"><a href="{vaga.get('ID_Vaga')}">{vaga.get('Titulo')}</a></h3>
            <p><b>Empresa:</b> {vaga.get('Empresa')} | <b>Score IA:</b> <span style="color: green; font-weight: bold;">{vaga.get('Score')}</span></p>
            <p><b>Justificativa da IA:</b> {vaga.get('Justificativa')}</p>
        </div>
        """
    
    corpo_html += """
        <hr>
        <p>Acesse o banco de dados local (banco_vagas.db) para ver todas as vagas coletadas.</p>
        <p>Atenciosamente,<br><b>Job Hunter AI (Automação Lucas)</b></p>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = email_remetente
    msg['To'] = email_destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo_html, 'html'))

    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(email_remetente, senha_app)
        servidor.send_message(msg)
        servidor.quit()
        logger.info("✅ Relatório enviado com sucesso para %s!", email_destinatario)
    except Exception as e:
        logger.error("❌ Falha ao enviar e-mail: %s", e)

if __name__ == "__main__":
    enviar_relatorio_email()
