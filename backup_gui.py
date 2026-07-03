import customtkinter as ctk
import subprocess
import os
import json
import smtplib
from email.message import EmailMessage
from tkinter import messagebox
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "backup_settings.json")

DEFAULT_SETTINGS = {
    "backup_source_path": "C:\\Backups\\",
    "backup_destination_path": "\\\\192.168.0.150\\d$\\Backup Totvs",
    "backup_folders": ["master", "msdb", "model", "sigaoficialtss", "sigaoficial"],
    "copy_everything": False,
    "frequency": "Diário",
    "notifications": "on",
    "compression": "off",
    "log_enabled": True,
    "log_retention": "30",
    "dark_mode": "Escuro",
    "email_enabled": False,
    "sender_email": "",
    "recipient_email": "",
    "email_mode": "always",
    "smtp_host": "localhost",
    "smtp_port": 25,
    "smtp_username": "",
    "smtp_password": "",
    "smtp_security": "none",
    "smtp_provider": "Personalizado"
}

# ===== PALETA ESCURA =====
PALETTE_BG = "#1b1d1f"
PALETTE_PANEL = "#1b1d1f"
PALETTE_TEXT = "#e6e9ff"
PALETTE_MUTED = "#99a8d9"
PALETTE_ACCENT = "#3f5cc8"
PALETTE_ACCENT_HOVER = "#334fa3"
PALETTE_SECONDARY = "#141617"
PALETTE_SECONDARY_HOVER = "#37476a"


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except Exception:
        settings = DEFAULT_SETTINGS.copy()

    for key, value in DEFAULT_SETTINGS.items():
        settings.setdefault(key, value)

    return settings


def save_settings_file(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro salvando configurações: {e}")


settings = load_settings()

ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.title("Controle de Backup")
app.geometry("520x480")
app.minsize(520, 480)
app.resizable(True, True)
app.iconbitmap(r"C:\backup_manager\leao_preto.ico")

# ===== FUNDO PRETO =====

frame = ctk.CTkFrame(app, fg_color=PALETTE_BG)
frame.pack(fill="both", expand=True)

# ===== CABEÇALHO =====

header_frame = ctk.CTkFrame(frame, fg_color="transparent")
header_frame.pack(fill="x", padx=20, pady=(20, 10))

logo_img = ctk.CTkImage(
    light_image=Image.open(r"C:\backup_manager\logo1.png"),
    size=(80,80)
)

logo = ctk.CTkLabel(header_frame, image=logo_img, text="")
logo.grid(row=0, column=0, sticky="w", padx=(0, 10))

titulo = ctk.CTkLabel(
    header_frame,
    text="CONTROLE DE BACKUP",
    text_color=PALETTE_ACCENT,
    font=("Arial",24,"bold")
)

titulo.grid(row=0, column=1, sticky="w")
header_frame.grid_columnconfigure(1, weight=1)

# ===== BOTÕES =====

button_container = ctk.CTkFrame(frame, fg_color="transparent")
button_container.pack(fill="x", padx=20, pady=(0, 20))
button_container.grid_columnconfigure(0, weight=1)

button_group = ctk.CTkFrame(button_container, fg_color="transparent", width=420)
button_group.pack(fill="x", anchor="n", padx=20, pady=0)
button_group.pack_propagate(False)
button_group.grid_columnconfigure(0, weight=1)

# ===== FUNÇÃO EXECUTAR =====

def rodar(arquivo):

    try:

        if arquivo.endswith(".ps1"):

            subprocess.Popen([
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                arquivo
            ])

        elif arquivo.endswith(".py"):

            subprocess.Popen([
                "python",
                arquivo
            ])

        else:

            os.startfile(arquivo)

    except Exception as e:

        print(e)


# ===== BOTÕES =====

botao1 = ctk.CTkButton(
    button_group,
    text="Executar Backup Manual",
    command=lambda: rodar(r"C:\backup_manager\backup_manager_total.py"),
    width=420,
    fg_color=PALETTE_ACCENT,
    hover_color=PALETTE_ACCENT_HOVER,
    text_color=PALETTE_TEXT
)

botao1.pack(fill="x", pady=8)


botao2 = ctk.CTkButton(
    button_group,
    text="Executar Backup Auto",
    command=lambda: rodar(r"C:\backup_manager\backup_auto.py"),
    width=420,
    fg_color=PALETTE_ACCENT,
    hover_color=PALETTE_ACCENT_HOVER,
    text_color=PALETTE_TEXT
)

botao2.pack(fill="x", pady=8)


botao3 = ctk.CTkButton(
    button_group,
    text="Executar Backup Loop",
    command=lambda: rodar(r"C:\backup_manager\backup_loop.ps1"),
    width=420,
    fg_color=PALETTE_ACCENT,
    hover_color=PALETTE_ACCENT_HOVER,
    text_color=PALETTE_TEXT
)

botao3.pack(fill="x", pady=8)

log_enabled = settings.get("log_enabled", True)
email_enabled = settings.get("email_enabled", False)


def update_log_button():
    if log_enabled:
        botao4.configure(state="normal", text="Ver Log")
    else:
        botao4.configure(state="disabled", text="Log Desativado")


botao4 = ctk.CTkButton(
    button_group,
    text="Ver Log",
    command=lambda: rodar(r"C:\backup_manager\backup_log.txt") if log_enabled else None,
    width=420,
    fg_color=PALETTE_SECONDARY,
    hover_color=PALETTE_SECONDARY_HOVER,
    text_color=PALETTE_TEXT
)

botao4.pack(fill="x", pady=8)
update_log_button()


# ===== SETTINGS WINDOW =====

def abrir_settings():
    """Abre a janela de configurações"""
    
    if hasattr(app, "settings_window") and app.settings_window.winfo_exists():
        app.settings_window.focus()
        return
    
    settings_window = ctk.CTkToplevel(app)
    app.settings_window = settings_window
    settings_window.title("Configurações")
    settings_window.geometry("500x600")
    settings_window.minsize(500, 600)
    settings_window.iconbitmap(r"C:\backup_manager\leao_preto.ico")
    
    settings_frame = ctk.CTkScrollableFrame(settings_window, fg_color=PALETTE_PANEL)
    settings_frame.pack(fill="both", expand=True, padx=10, pady=10)
    settings_frame.grid_columnconfigure(0, weight=1)
    
    # Título
    titulo_settings = ctk.CTkLabel(
        settings_frame,
        text="CONFIGURAÇÕES",
        text_color=PALETTE_ACCENT,
        font=("Arial", 20, "bold")
    )
    titulo_settings.pack(pady=15)
    
    # ===== LOCAL DE BACKUP =====
    label_backup_path = ctk.CTkLabel(
        settings_frame,
        text="Local de Backup:",
        text_color=PALETTE_TEXT,
        font=("Arial", 12, "bold")
    )
    label_backup_path.pack(anchor="w", padx=20, pady=(10, 5))
    
    entry_backup_path = ctk.CTkEntry(settings_frame)
    entry_backup_path.insert(0, settings.get("backup_source_path", settings.get("backup_path", "C:\\Backups\\")))
    entry_backup_path.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    label_destination_path = ctk.CTkLabel(
        settings_frame,
        text="Destino de Backup:",
        text_color=PALETTE_TEXT,
        font=("Arial", 12, "bold")
    )
    label_destination_path.pack(anchor="w", padx=20, pady=(10, 5))

    entry_destination_path = ctk.CTkEntry(settings_frame)
    entry_destination_path.insert(0, settings.get("backup_destination_path", "\\\\192.168.0.150\\d$\\Backup Totvs"))
    entry_destination_path.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    label_folder_list = ctk.CTkLabel(
        settings_frame,
        text="Pastas a copiar (vírgula separada):",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_folder_list.pack(anchor="w", padx=20, pady=(10, 5))

    entry_folder_list = ctk.CTkEntry(settings_frame)
    entry_folder_list.insert(0, ",".join(settings.get("backup_folders", [])))
    entry_folder_list.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    copy_everything_var = ctk.StringVar(value="on" if settings.get("copy_everything", False) else "off")
    switch_copy_everything = ctk.CTkSwitch(
        settings_frame,
        text="Copiar todos os arquivos/pastas no caminho",
        variable=copy_everything_var,
        onvalue="on",
        offvalue="off"
    )
    switch_copy_everything.pack(anchor="w", padx=20, pady=(0, 20))
    
    # ===== FREQUÊNCIA DE BACKUP =====
    label_frequency = ctk.CTkLabel(
        settings_frame,
        text="Frequência de Backup:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_frequency.pack(anchor="w", padx=20, pady=(10, 5))
    
    frequency_var = ctk.StringVar(value=settings.get("frequency", "Diário"))
    frequency_menu = ctk.CTkComboBox(
        settings_frame,
        values=["Horário", "Diário", "Semanal", "Mensal"],
        variable=frequency_var,
        state="readonly"
    )
    frequency_menu.pack(fill="x", expand=True, padx=20, pady=(0, 15))
    
    # ===== NOTIFICAÇÕES =====
    label_notifications = ctk.CTkLabel(
        settings_frame,
        text="Notificações:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_notifications.pack(anchor="w", padx=20, pady=(10, 5))
    
    notifications_var = ctk.StringVar(value=settings.get("notifications", "on"))
    switch_notifications = ctk.CTkSwitch(
        settings_frame,
        text="Ativar Notificações",
        variable=notifications_var,
        onvalue="on",
        offvalue="off"
    )
    switch_notifications.pack(anchor="w", padx=20, pady=(0, 15))
    
    # ===== COMPRESSÃO =====
    label_compression = ctk.CTkLabel(
        settings_frame,
        text="Compressão:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_compression.pack(anchor="w", padx=20, pady=(10, 5))
    
    compression_var = ctk.StringVar(value=settings.get("compression", "off"))
    switch_compression = ctk.CTkSwitch(
        settings_frame,
        text="Ativar Compressão",
        variable=compression_var,
        onvalue="on",
        offvalue="off"
    )
    switch_compression.pack(anchor="w", padx=20, pady=(0, 15))
    
    # ===== LOG ENABLE =====
    log_enabled_var = ctk.StringVar(value="on" if settings.get("log_enabled", True) else "off")
    label_log_enabled = ctk.CTkLabel(
        settings_frame,
        text="Registro de Log:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_log_enabled.pack(anchor="w", padx=20, pady=(10, 5))
    
    switch_log_enabled = ctk.CTkSwitch(
        settings_frame,
        text="Ativar Log",
        variable=log_enabled_var,
        onvalue="on",
        offvalue="off"
    )
    switch_log_enabled.pack(anchor="w", padx=20, pady=(0, 15))
    
    # ===== RETENÇÃO DE LOGS =====
    label_log_retention = ctk.CTkLabel(
        settings_frame,
        text="Retenção de Logs (dias):",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_log_retention.pack(anchor="w", padx=20, pady=(10, 5))
    
    entry_log_retention = ctk.CTkEntry(settings_frame)
    entry_log_retention.insert(0, settings.get("log_retention", "30"))
    entry_log_retention.pack(fill="x", expand=True, padx=20, pady=(0, 15))
    
    # ===== MODO ESCURO =====
    label_dark_mode = ctk.CTkLabel(
        settings_frame,
        text="Aparência:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_dark_mode.pack(anchor="w", padx=20, pady=(10, 5))
    
    dark_mode_var = ctk.StringVar(value=settings.get("dark_mode", "Escuro"))
    dark_mode_menu = ctk.CTkComboBox(
        settings_frame,
        values=["Claro", "Escuro"],
        variable=dark_mode_var,
        state="readonly"
    )
    dark_mode_menu.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    # ===== EMAIL NOTIFICAÇÕES =====
    label_email_notifications = ctk.CTkLabel(
        settings_frame,
        text="Notificações por E-mail:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_email_notifications.pack(anchor="w", padx=20, pady=(10, 5))

    email_enabled_var = ctk.StringVar(value="on" if settings.get("email_enabled", False) else "off")
    switch_email_enabled = ctk.CTkSwitch(
        settings_frame,
        text="Ativar E-mail",
        variable=email_enabled_var,
        onvalue="on",
        offvalue="off"
    )
    switch_email_enabled.pack(anchor="w", padx=20, pady=(0, 10))

    label_sender_email = ctk.CTkLabel(
        settings_frame,
        text="E-mail de Origem:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_sender_email.pack(anchor="w", padx=20, pady=(10, 5))

    entry_sender_email = ctk.CTkEntry(
        settings_frame,
        placeholder_text="seu-email@dominio.com"
    )
    entry_sender_email.insert(0, settings.get("sender_email", ""))
    entry_sender_email.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    label_recipient_email = ctk.CTkLabel(
        settings_frame,
        text="E-mail Destinatário:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_recipient_email.pack(anchor="w", padx=20, pady=(10, 5))

    entry_recipient_email = ctk.CTkEntry(
        settings_frame,
        placeholder_text="destinatario@dominio.com"
    )
    entry_recipient_email.insert(0, settings.get("recipient_email", ""))
    entry_recipient_email.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    label_email_mode = ctk.CTkLabel(
        settings_frame,
        text="Enviar E-mail:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_email_mode.pack(anchor="w", padx=20, pady=(10, 5))

    email_mode_var = ctk.StringVar(value="Sempre" if settings.get("email_mode", "always") == "always" else "Apenas falhas")
    email_mode_menu = ctk.CTkComboBox(
        settings_frame,
        values=["Sempre", "Apenas falhas"],
        variable=email_mode_var,
        state="readonly"
    )
    email_mode_menu.pack(fill="x", expand=True, padx=20, pady=(0, 20))

    label_smtp_provider = ctk.CTkLabel(
        settings_frame,
        text="Provedor de E-mail:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_smtp_provider.pack(anchor="w", padx=20, pady=(10, 5))

    def detect_smtp_provider():
        host = settings.get("smtp_host", "localhost").lower()
        if "office365" in host or "outlook" in host:
            return "Outlook/Office365"
        if "gmail" in host or "google" in host:
            return "Gmail"
        if host in ("localhost", "127.0.0.1"):
            return "Localhost"
        return "Personalizado"

    provider_var = ctk.StringVar(value=settings.get("smtp_provider", detect_smtp_provider()))
    provider_menu = ctk.CTkComboBox(
        settings_frame,
        values=["Personalizado", "Locaweb", "Outlook/Office365", "Gmail", "Localhost"],
        variable=provider_var,
        state="readonly"
    )
    provider_menu.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    def apply_smtp_provider(*args):
        provider = provider_var.get()
        if provider == "Outlook/Office365":
            entry_smtp_host.delete(0, "end")
            entry_smtp_host.insert(0, "smtp.office365.com")
            entry_smtp_port.delete(0, "end")
            entry_smtp_port.insert(0, "587")
            smtp_security_var.set("STARTTLS")
        elif provider == "Gmail":
            entry_smtp_host.delete(0, "end")
            entry_smtp_host.insert(0, "smtp.gmail.com")
            entry_smtp_port.delete(0, "end")
            entry_smtp_port.insert(0, "587")
            smtp_security_var.set("STARTTLS")
        elif provider == "Locaweb":
            entry_smtp_host.delete(0, "end")
            entry_smtp_host.insert(0, "email-ssl.com.br")
            entry_smtp_port.delete(0, "end")
            entry_smtp_port.insert(0, "465")
            smtp_security_var.set("SSL/TLS")
        elif provider == "Localhost":
            entry_smtp_host.delete(0, "end")
            entry_smtp_host.insert(0, "localhost")
            entry_smtp_port.delete(0, "end")
            entry_smtp_port.insert(0, "25")
            smtp_security_var.set("Nenhum")
        # Personalizado não altera campos

    provider_var.trace_add("write", apply_smtp_provider)

    label_smtp_info = ctk.CTkLabel(
        settings_frame,
        text="Escolha um provedor para preencher as configurações básicas automaticamente."
             " Para Locaweb use 'Locaweb', depois informe usuário e senha."
             "",
        text_color=PALETTE_MUTED,
        font=("Arial", 10),
        wraplength=440,
        justify="left"
    )
    label_smtp_info.pack(fill="x", padx=20, pady=(0, 10))

    label_smtp_host = ctk.CTkLabel(
        settings_frame,
        text="Servidor SMTP:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_smtp_host.pack(anchor="w", padx=20, pady=(10, 5))

    entry_smtp_host = ctk.CTkEntry(settings_frame)
    entry_smtp_host.insert(0, settings.get("smtp_host", "localhost"))
    entry_smtp_host.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    label_smtp_port = ctk.CTkLabel(
        settings_frame,
        text="Porta SMTP:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_smtp_port.pack(anchor="w", padx=20, pady=(10, 5))

    entry_smtp_port = ctk.CTkEntry(settings_frame)
    entry_smtp_port.insert(0, str(settings.get("smtp_port", 25)))
    entry_smtp_port.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    label_smtp_username = ctk.CTkLabel(
        settings_frame,
        text="Usuário SMTP (opcional):",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_smtp_username.pack(anchor="w", padx=20, pady=(10, 5))

    entry_smtp_username = ctk.CTkEntry(settings_frame)
    entry_smtp_username.insert(0, settings.get("smtp_username", ""))
    entry_smtp_username.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    label_smtp_password = ctk.CTkLabel(
        settings_frame,
        text="Senha SMTP (opcional):",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_smtp_password.pack(anchor="w", padx=20, pady=(10, 5))

    entry_smtp_password = ctk.CTkEntry(
        settings_frame,
        show="*"
    )
    entry_smtp_password.insert(0, settings.get("smtp_password", ""))
    entry_smtp_password.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    label_smtp_security = ctk.CTkLabel(
        settings_frame,
        text="Segurança SMTP:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_smtp_security.pack(anchor="w", padx=20, pady=(10, 5))

    smtp_security_var = ctk.StringVar(
        value={
            "ssl": "SSL/TLS",
            "starttls": "STARTTLS",
            "none": "Nenhum"
        }.get(settings.get("smtp_security", "none"), "Nenhum")
    )
    smtp_security_menu = ctk.CTkComboBox(
        settings_frame,
        values=["Nenhum", "STARTTLS", "SSL/TLS"],
        variable=smtp_security_var,
        state="readonly"
    )
    smtp_security_menu.pack(fill="x", expand=True, padx=20, pady=(0, 20))

    def send_test_email():
        sender = entry_sender_email.get().strip()
        recipient = entry_recipient_email.get().strip()
        host = entry_smtp_host.get().strip()
        port_text = entry_smtp_port.get().strip()
        username = entry_smtp_username.get().strip()
        password = entry_smtp_password.get()
        security = smtp_security_var.get()
        provider = provider_var.get()

        if not sender or not recipient:
            messagebox.showerror("Teste de E-mail", "Informe os campos de e-mail de origem e destinatário.")
            return

        if not host:
            messagebox.showerror("Teste de E-mail", "Informe o servidor SMTP.")
            return

        try:
            port = int(port_text) if port_text else 25
        except ValueError:
            messagebox.showerror("Teste de E-mail", "Informe uma porta SMTP válida.")
            return

        msg = EmailMessage()
        effective_sender = sender
        if provider == "Locaweb" and username and sender.lower() != username.lower():
            if messagebox.askyesno(
                "Aviso Locaweb",
                "Para o provedor Locaweb, o remetente normalmente deve ser o mesmo usuário SMTP.\n"
                "Deseja usar o usuário SMTP como remetente para este teste?"
            ):
                effective_sender = username
            else:
                messagebox.showwarning(
                    "Teste de E-mail",
                    "O envio pode falhar se o remetente for diferente do usuário SMTP."
                )

        msg["From"] = effective_sender
        msg["To"] = recipient
        msg["Subject"] = "Teste de e-mail de backup"
        msg.set_content("Este é um e-mail de teste para verificar a configuração SMTP do Backup Manager.")

        try:
            if security == "SSL/TLS":
                smtp = smtplib.SMTP_SSL(host, port, timeout=30)
            else:
                smtp = smtplib.SMTP(host, port, timeout=30)
                try:
                    smtp.ehlo()
                except Exception:
                    pass
                if security == "STARTTLS":
                    smtp.starttls()
                    try:
                        smtp.ehlo()
                    except Exception:
                        pass

            with smtp:
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(msg)

            messagebox.showinfo("Teste de E-mail", "E-mail de teste enviado com sucesso.")
        except Exception as e:
            error_text = str(e)
            if "authentication failed" in error_text.lower() or "auth" in error_text.lower():
                message = (
                    "Autenticação SMTP falhou.\n"
                    "Verifique usuário, senha e tipo de segurança (STARTTLS/SSL/TLS).\n"
                    f"\nDetalhe: {error_text}"
                )
            elif "connection refused" in error_text.lower() or "could not connect" in error_text.lower():
                message = (
                    "Não foi possível conectar ao servidor SMTP.\n"
                    "Verifique servidor, porta e se o servidor está acessível.\n"
                    f"\nDetalhe: {error_text}"
                )
            elif "getaddrinfo failed" in error_text.lower() or "unknown host" in error_text.lower():
                message = (
                    "Servidor SMTP inválido.\n"
                    "Verifique o nome do host.\n"
                    f"\nDetalhe: {error_text}"
                )
            else:
                message = f"Falha ao enviar e-mail de teste:\n{error_text}"
            messagebox.showerror("Teste de E-mail", message)

    def toggle_email_fields(*args):
        enabled = email_enabled_var.get() == "on"
        state = "normal" if enabled else "disabled"
        for widget in [
            entry_sender_email,
            entry_recipient_email,
            email_mode_menu,
            provider_menu,
            entry_smtp_host,
            entry_smtp_port,
            entry_smtp_username,
            entry_smtp_password,
            smtp_security_menu,
            test_email_button
        ]:
            widget.configure(state=state)

    test_email_button = ctk.CTkButton(
        settings_frame,
        text="Enviar E-mail de Teste",
        command=send_test_email,
        fg_color=PALETTE_ACCENT,
        hover_color=PALETTE_ACCENT_HOVER,
        text_color=PALETTE_TEXT
    )
    test_email_button.pack(fill="x", padx=20, pady=(0, 20))

    switch_email_enabled.configure(command=toggle_email_fields)
    toggle_email_fields()

    # ===== BOTÕES DE AÇÃO =====
    button_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
    button_frame.pack(pady=20)
    
    def save_settings():
        nonlocal log_enabled_var

        global log_enabled, email_enabled
        log_enabled = log_enabled_var.get() == "on"
        email_enabled = email_enabled_var.get() == "on"

        settings["backup_source_path"] = entry_backup_path.get() or settings.get("backup_source_path", settings.get("backup_path", "C:\\Backups\\"))
        settings["backup_destination_path"] = entry_destination_path.get() or settings.get("backup_destination_path", "\\\\192.168.0.150\\d$\\Backup Totvs")
        settings["backup_folders"] = [item.strip() for item in entry_folder_list.get().split(",") if item.strip()]
        settings["copy_everything"] = copy_everything_var.get() == "on"
        settings["frequency"] = frequency_var.get()
        settings["notifications"] = notifications_var.get()
        settings["compression"] = compression_var.get()
        settings["log_enabled"] = log_enabled
        settings["log_retention"] = entry_log_retention.get() or settings["log_retention"]
        settings["dark_mode"] = dark_mode_var.get()
        settings["email_enabled"] = email_enabled
        settings["sender_email"] = entry_sender_email.get().strip()
        settings["recipient_email"] = entry_recipient_email.get().strip()
        settings["email_mode"] = "always" if email_mode_var.get() == "Sempre" else "failed"
        settings["smtp_provider"] = provider_var.get()
        settings["smtp_host"] = entry_smtp_host.get().strip() or "localhost"
        try:
            settings["smtp_port"] = int(entry_smtp_port.get().strip() or 25)
        except ValueError:
            settings["smtp_port"] = 25
        settings["smtp_username"] = entry_smtp_username.get().strip()
        settings["smtp_password"] = entry_smtp_password.get()
        settings["smtp_security"] = {
            "Nenhum": "none",
            "STARTTLS": "starttls",
            "SSL/TLS": "ssl"
        }.get(smtp_security_var.get(), "none")

        save_settings_file(settings)
        update_log_button()
        settings_window.destroy()

    botao_salvar = ctk.CTkButton(
        button_frame,
        text="Salvar",
        width=120,
        fg_color=PALETTE_ACCENT,
        hover_color=PALETTE_ACCENT_HOVER,
        text_color=PALETTE_TEXT,
        command=save_settings
    )
    botao_salvar.pack(side="left", padx=10)
    
    botao_cancelar = ctk.CTkButton(
        button_frame,
        text="Cancelar",
        width=120,
        fg_color=PALETTE_SECONDARY,
        hover_color=PALETTE_SECONDARY_HOVER,
        text_color=PALETTE_TEXT,
        command=settings_window.destroy
    )
    botao_cancelar.pack(side="left", padx=10)


botao_settings = ctk.CTkButton(
    button_container,
    text="Configurações",
    command=abrir_settings,
    fg_color=PALETTE_ACCENT,
    hover_color=PALETTE_ACCENT_HOVER,
    text_color=PALETTE_TEXT
)

botao_settings.pack(fill="x", pady=8)


# ===== RODAR =====

app.mainloop()
