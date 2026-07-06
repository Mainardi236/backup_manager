import customtkinter as ctk
import subprocess
import os
import sys
import json
import smtplib
import threading
from email.message import EmailMessage
from tkinter import filedialog, messagebox
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "backup_settings.json")

DEFAULT_SETTINGS = {
    "backup_source_path": "",
    "backup_destination_path": "",
    "backup_folders": [],
    "copy_everything": True,
    "frequency": "Diário",
    "notifications": "off",
    "compression": "off",
    "log_enabled": False,
    "log_retention": "",
    "show_output_window": False,
    "auto_backup_times": "",
    "loop_backup_times": "",
    "email_enabled": False,
    "sender_email": "",
    "recipient_email": "",
    "email_mode": "failed",
    "smtp_host": "",
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

    if not isinstance(settings, dict):
        settings = DEFAULT_SETTINGS.copy()

    for key, value in DEFAULT_SETTINGS.items():
        settings.setdefault(key, value)

    return settings


def is_default_settings(settings_data):
    if not isinstance(settings_data, dict):
        return True
    return settings_data == DEFAULT_SETTINGS


def save_settings_file(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro salvando configurações: {e}")


settings = load_settings()

ctk.set_appearance_mode("dark")


def import_settings_from_file():
    global settings
    path = filedialog.askopenfilename(title="Importar configurações", filetypes=[("Arquivos JSON", "*.json")], defaultextension=".json")
    if not path:
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            imported = json.load(f)
        if not isinstance(imported, dict):
            raise ValueError("Arquivo inválido")
        merged = DEFAULT_SETTINGS.copy()
        merged.update(imported)
        settings = merged
        save_settings_file(settings)
        render_preview()
        return True
    except Exception as e:
        messagebox.showerror("Importar configurações", f"Não foi possível importar as configurações:\n{e}")
        return False


def prompt_initial_setup():
    if not is_default_settings(settings):
        return

    choice = messagebox.askyesnocancel(
        "Configurações",
        "Nenhuma configuração foi encontrada. Deseja configurar agora?\n\nClique em Sim para abrir as configurações.\nClique em Não para importar um arquivo JSON.\nClique em Cancelar para continuar sem configurar."
    )

    if choice is True:
        abrir_settings()
    elif choice is False:
        import_settings_from_file()

app = ctk.CTk()
app.title("Controle de Backup")
app.geometry("520x480")
app.minsize(520, 480)
app.resizable(True, True)
app.iconbitmap(r"C:\backup_manager\leao_preto.ico")

# ===== FUNDO PRETO =====

frame = ctk.CTkFrame(app, fg_color=PALETTE_BG)
frame.pack(fill="both", expand=True)
frame.grid_columnconfigure(0, weight=1)
frame.grid_rowconfigure(1, weight=1)
frame.grid_rowconfigure(2, weight=0)

status_var = ctk.StringVar(value="Status: pronto")
status_frame = ctk.CTkFrame(frame, fg_color="#171a1d")
status_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))
status_frame.grid_columnconfigure(0, weight=1)

status_progress = ctk.CTkProgressBar(status_frame, width=220, height=6)
status_progress.set(0)
status_progress.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 6))

status_label = ctk.CTkLabel(status_frame, textvariable=status_var, text_color=PALETTE_MUTED, font=("Arial", 11))
status_label.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 10))


def set_status(message, running=False):
    status_var.set(f"Status: {message}")
    if running:
        status_progress.start()
    else:
        status_progress.stop()
        status_progress.set(0)

# ===== CABEÇALHO =====

header_frame = ctk.CTkFrame(frame, fg_color="#171a1d")
header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))
header_frame.grid_columnconfigure(0, weight=0)
header_frame.grid_columnconfigure(1, weight=1)
header_frame.grid_rowconfigure(0, weight=1)

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

# ===== CONTEÚDO PRINCIPAL =====

content_frame = ctk.CTkFrame(frame, fg_color="transparent")
content_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
content_frame.grid_columnconfigure(0, weight=1)
content_frame.grid_columnconfigure(1, weight=0)
content_frame.grid_rowconfigure(0, weight=1)

# ===== BOTÕES =====

button_container = ctk.CTkFrame(content_frame, fg_color="#171a1d")
button_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
button_container.grid_columnconfigure(0, weight=1)
button_container.grid_rowconfigure(0, weight=0)
button_container.grid_rowconfigure(1, weight=0)
button_container.grid_rowconfigure(2, weight=0)
button_container.grid_rowconfigure(3, weight=0)
button_container.grid_rowconfigure(4, weight=0)
button_container.grid_rowconfigure(5, weight=1)

button_group = ctk.CTkFrame(button_container, fg_color="transparent", width=320)
button_group.grid(row=0, column=0, sticky="n", padx=16, pady=16)
button_group.grid_propagate(False)
button_group.grid_columnconfigure(0, weight=1)

# ===== PREVIEW LATERAL =====

preview_container = ctk.CTkFrame(content_frame, fg_color="#171a1d")
preview_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
preview_container.grid_columnconfigure(0, weight=1)
preview_container.grid_rowconfigure(0, weight=0)
preview_container.grid_rowconfigure(1, weight=1)
preview_container.grid_rowconfigure(2, weight=1)

preview_title = ctk.CTkLabel(preview_container, text="Preview", text_color=PALETTE_TEXT, font=("Arial", 14, "bold"))
preview_title.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

source_panel = ctk.CTkFrame(preview_container, fg_color="#21262c")
source_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
source_panel.grid_columnconfigure(0, weight=1)
source_panel.grid_rowconfigure(0, weight=0)
source_panel.grid_rowconfigure(1, weight=0)
source_panel.grid_rowconfigure(2, weight=1)
source_panel.configure(width=260, height=185)

source_label = ctk.CTkLabel(source_panel, text="Origem", text_color=PALETTE_ACCENT, font=("Arial", 12, "bold"))
source_label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))

source_path_var = ctk.StringVar(value=settings.get("backup_source_path", ""))
source_path_label = ctk.CTkLabel(source_panel, textvariable=source_path_var, text_color=PALETTE_TEXT, wraplength=200, justify="left")
source_path_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))

source_scroll = ctk.CTkScrollableFrame(source_panel, fg_color="#2b3138")
source_scroll.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
source_scroll.grid_columnconfigure(0, weight=1)

source_items = []


destination_panel = ctk.CTkFrame(preview_container, fg_color="#21262c")
destination_panel.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
destination_panel.grid_columnconfigure(0, weight=1)
destination_panel.grid_rowconfigure(0, weight=0)
destination_panel.grid_rowconfigure(1, weight=0)
destination_panel.grid_rowconfigure(2, weight=1)
destination_panel.configure(width=260, height=185)

destination_label = ctk.CTkLabel(destination_panel, text="Destino", text_color=PALETTE_ACCENT, font=("Arial", 12, "bold"))
destination_label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))

destination_path_var = ctk.StringVar(value=settings.get("backup_destination_path", ""))
destination_path_label = ctk.CTkLabel(destination_panel, textvariable=destination_path_var, text_color=PALETTE_TEXT, wraplength=200, justify="left")
destination_path_label.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))

destination_scroll = ctk.CTkScrollableFrame(destination_panel, fg_color="#2b3138")
destination_scroll.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
destination_scroll.grid_columnconfigure(0, weight=1)

destination_items = []


def render_preview():
    for widget in source_scroll.winfo_children():
        widget.destroy()
    for widget in destination_scroll.winfo_children():
        widget.destroy()

    source_items.clear()
    destination_items.clear()
    source_path = settings.get("backup_source_path", "")
    destination_path = settings.get("backup_destination_path", "")
    source_path_var.set(source_path)
    destination_path_var.set(destination_path)

    def add_item(container, label_text, is_dir=True):
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=2)
        icon = "📁" if is_dir else "📄"
        ctk.CTkLabel(row, text=f"{icon} {label_text}", text_color=PALETTE_TEXT, anchor="w", justify="left", wraplength=180).pack(anchor="w")

    try:
        if os.path.exists(source_path):
            entries = sorted(os.listdir(source_path))[:10]
            for entry in entries:
                full_path = os.path.join(source_path, entry)
                add_item(source_scroll, entry, os.path.isdir(full_path))
        else:
            add_item(source_scroll, "Pasta de origem não encontrada", True)
    except Exception:
        add_item(source_scroll, "Não foi possível listar a origem", True)

    try:
        if os.path.exists(destination_path):
            entries = sorted(os.listdir(destination_path))[:10]
            for entry in entries:
                full_path = os.path.join(destination_path, entry)
                add_item(destination_scroll, entry, os.path.isdir(full_path))
        else:
            add_item(destination_scroll, "Pasta de destino não encontrada", True)
    except Exception:
        add_item(destination_scroll, "Não foi possível listar o destino", True)


def refresh_preview_loop():
    if app.winfo_exists():
        render_preview()
        app.after(3000, refresh_preview_loop)


render_preview()
refresh_preview_loop()

# ===== FUNÇÃO EXECUTAR =====

def rodar(arquivo):

    try:
        target_name = os.path.basename(arquivo).lower()
        if target_name == "backup_auto.py":
            set_status("backup auto ativo", running=True)
        elif target_name == "backup_loop.ps1":
            set_status("backup loop ativo", running=True)
        else:
            set_status("iniciando backup...", running=True)

        kwargs = {}
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs["startupinfo"] = startupinfo
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        if arquivo.endswith(".ps1"):
            process = subprocess.Popen([
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-WindowStyle",
                "Hidden",
                "-File",
                arquivo
            ], **kwargs)
            setattr(app, "active_backup_process", process)

        elif arquivo.endswith(".py"):
            show_output = load_settings().get("show_output_window", True)
            if show_output:
                active_backup_process = getattr(app, "active_backup_process", None)
                if active_backup_process is not None and active_backup_process.poll() is None:
                    active_backup_process.terminate()

                output_window_existing = getattr(app, "output_window", None)
                if output_window_existing is not None and output_window_existing.winfo_exists():
                    output_window_existing.destroy()

                output_window = ctk.CTkToplevel(app)
                setattr(app, "output_window", output_window)
                output_window.title("Saída do Backup")
                output_window.geometry("700x420")
                output_window.minsize(700, 420)
                output_window.configure(fg_color=PALETTE_PANEL)
                output_window.iconbitmap(r"C:\backup_manager\leao_preto.ico")
                output_window.grid_columnconfigure(0, weight=1)
                output_window.grid_rowconfigure(0, weight=1)

                header = ctk.CTkLabel(output_window, text="Saída do Backup", font=("Arial", 16, "bold"), text_color=PALETTE_TEXT)
                header.pack(padx=20, pady=(15, 10), anchor="w")

                output_text = ctk.CTkTextbox(output_window, fg_color="#2b2b2b", text_color="white", wrap="word", height=260)
                output_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))
                output_text.insert("end", "Iniciando backup...\n")
                output_text.configure(state="disabled")

                footer = ctk.CTkFrame(output_window, fg_color="transparent")
                footer.pack(fill="x", padx=20, pady=(0, 15))

                def close_window():
                    active_backup_process = getattr(app, "active_backup_process", None)
                    if active_backup_process is not None and active_backup_process.poll() is None:
                        active_backup_process.terminate()
                    output_window_existing = getattr(app, "output_window", None)
                    if output_window_existing is not None and output_window_existing.winfo_exists():
                        output_window_existing.destroy()
                    setattr(app, "output_window", None)
                    set_status("pronto", running=False)

                close_button = ctk.CTkButton(footer, text="Fechar", command=close_window, fg_color=PALETTE_SECONDARY, hover_color=PALETTE_SECONDARY_HOVER)
                close_button.pack(anchor="e")

                process = subprocess.Popen([
                    sys.executable,
                    arquivo
                ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, **kwargs)
                setattr(app, "active_backup_process", process)

                def stream_output():
                    if process.stdout is None:
                        return
                    for line in process.stdout:
                        output_text.after(0, lambda l=line: output_text.configure(state="normal") or output_text.insert("end", l) or output_text.configure(state="disabled"))
                    if process.poll() is None:
                        process.wait()
                    output_text.after(0, lambda: output_text.configure(state="normal") or output_text.insert("end", "\nBackup finalizado.\n") or output_text.configure(state="disabled"))
                    set_status("pronto", running=False)

                threading.Thread(target=stream_output, daemon=True).start()
                return

            process = subprocess.Popen([
                sys.executable,
                arquivo
            ], **kwargs)
            setattr(app, "active_backup_process", process)
            set_status("pronto", running=False)

        else:
            os.startfile(arquivo)

        messagebox.showinfo("Backup", "O backup foi iniciado em segundo plano.")

    except Exception as e:
        print(e)
        messagebox.showerror("Erro", f"Não foi possível iniciar o backup: {e}")


# ===== BOTÕES =====

botao1 = ctk.CTkButton(
    button_group,
    text="Executar Backup Manual",
    command=lambda: rodar(r"C:\backup_manager\backup_manager_total.py"),
    width=800,
    height=35,
    fg_color=PALETTE_ACCENT,
    hover_color=PALETTE_ACCENT_HOVER,
    text_color=PALETTE_TEXT
)

botao1.grid(row=0, column=0, pady=(0, 8), padx=20)


botao2 = ctk.CTkButton(
    button_group,
    text="Executar Backup Auto",
    command=lambda: rodar(r"C:\backup_manager\backup_auto.py"),
    width=800,
    height=35,
    fg_color=PALETTE_ACCENT,
    hover_color=PALETTE_ACCENT_HOVER,
    text_color=PALETTE_TEXT
)

botao2.grid(row=1, column=0, pady=(0, 8), padx=20)


botao3 = ctk.CTkButton(
    button_group,
    text="Executar Backup Loop",
    command=lambda: rodar(r"C:\backup_manager\backup_loop.ps1"),
    width=800,
    height=35,
    fg_color=PALETTE_ACCENT,
    hover_color=PALETTE_ACCENT_HOVER,
    text_color=PALETTE_TEXT
)

botao3.grid(row=2, column=0, pady=(0, 8), padx=20)

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
    width=800,
    height=35,
    fg_color=PALETTE_SECONDARY,
    hover_color=PALETTE_SECONDARY_HOVER,
    text_color=PALETTE_TEXT
)

botao4.grid(row=3, column=0, pady=(0, 8), padx=20)
update_log_button()


# ===== BOTÕES INFERIORES =====

def cancelar_backup_em_execucao():
    active_backup_process = getattr(app, "active_backup_process", None)
    if active_backup_process is not None and active_backup_process.poll() is None:
        active_backup_process.terminate()
        set_status("backup cancelado", running=False)
        messagebox.showinfo("Backup", "Backup cancelado com sucesso.")
    else:
        messagebox.showwarning("Backup", "Nenhum backup está em execução no momento.")


def reiniciar_programa():
    app.destroy()
    os.startfile(os.path.abspath(__file__))


def fechar_programa():
    app.destroy()


# ===== SETTINGS WINDOW =====

def abrir_settings():
    """Abre a janela de configurações"""
    
    existing_settings_window = getattr(app, "settings_window", None)
    if existing_settings_window is not None and existing_settings_window.winfo_exists():
        existing_settings_window.focus()
        return
    
    settings_window = ctk.CTkToplevel(app)
    setattr(app, "settings_window", settings_window)
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

    backup_path_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
    backup_path_frame.pack(fill="x", padx=20, pady=(0, 15))
    backup_path_frame.grid_columnconfigure(0, weight=1)

    entry_backup_path = ctk.CTkEntry(backup_path_frame, placeholder_text="Selecione a pasta de origem")
    entry_backup_path.insert(0, settings.get("backup_source_path", settings.get("backup_path", "")))
    entry_backup_path.grid(row=0, column=0, sticky="ew", padx=(0, 8))

    def browse_source_folder():
        folder = filedialog.askdirectory(title="Selecionar pasta de origem")
        if folder:
            entry_backup_path.delete(0, "end")
            entry_backup_path.insert(0, folder)

    browse_source_button = ctk.CTkButton(
        backup_path_frame,
        text="Procurar",
        width=90,
        height=30,
        fg_color=PALETTE_ACCENT,
        hover_color=PALETTE_ACCENT_HOVER,
        text_color=PALETTE_TEXT,
        command=browse_source_folder
    )
    browse_source_button.grid(row=0, column=1)

    label_destination_path = ctk.CTkLabel(
        settings_frame,
        text="Destino de Backup:",
        text_color=PALETTE_TEXT,
        font=("Arial", 12, "bold")
    )
    label_destination_path.pack(anchor="w", padx=20, pady=(10, 5))

    destination_path_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
    destination_path_frame.pack(fill="x", padx=20, pady=(0, 15))
    destination_path_frame.grid_columnconfigure(0, weight=1)

    entry_destination_path = ctk.CTkEntry(destination_path_frame, placeholder_text="Selecione a pasta de destino")
    entry_destination_path.insert(0, settings.get("backup_destination_path", ""))
    entry_destination_path.grid(row=0, column=0, sticky="ew", padx=(0, 8))

    def browse_destination_folder():
        folder = filedialog.askdirectory(title="Selecionar pasta de destino")
        if folder:
            entry_destination_path.delete(0, "end")
            entry_destination_path.insert(0, folder)

    browse_destination_button = ctk.CTkButton(
        destination_path_frame,
        text="Procurar",
        width=90,
        height=30,
        fg_color=PALETTE_ACCENT,
        hover_color=PALETTE_ACCENT_HOVER,
        text_color=PALETTE_TEXT,
        command=browse_destination_folder
    )
    browse_destination_button.grid(row=0, column=1)

    label_folder_list = ctk.CTkLabel(
        settings_frame,
        text="Pastas a copiar (vírgula separada):",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_folder_list.pack(anchor="w", padx=20, pady=(10, 5))

    entry_folder_list = ctk.CTkEntry(settings_frame, placeholder_text="Ex.: pasta1, pasta2")
    entry_folder_list.insert(0, ",".join(settings.get("backup_folders", [])))
    entry_folder_list.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    copy_everything_var = ctk.StringVar(value="on" if settings.get("copy_everything", True) else "off")
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

    # ===== HORÁRIOS DO BACKUP AUTO =====
    label_auto_times = ctk.CTkLabel(
        settings_frame,
        text="Horários do Backup Auto (HH:MM, separados por vírgula):",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_auto_times.pack(anchor="w", padx=20, pady=(10, 5))

    entry_auto_times = ctk.CTkEntry(settings_frame, placeholder_text="Ex.: 13:00,21:00")
    entry_auto_times.insert(0, settings.get("auto_backup_times", ""))
    entry_auto_times.pack(fill="x", expand=True, padx=20, pady=(0, 15))

    # ===== HORÁRIOS DO LOOP =====
    label_loop_times = ctk.CTkLabel(
        settings_frame,
        text="Horários do Loop (HH:MM, separados por vírgula):",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_loop_times.pack(anchor="w", padx=20, pady=(10, 5))

    entry_loop_times = ctk.CTkEntry(settings_frame, placeholder_text="Ex.: 13:00,21:00")
    entry_loop_times.insert(0, settings.get("loop_backup_times", ""))
    entry_loop_times.pack(fill="x", expand=True, padx=20, pady=(0, 15))
    
    # ===== LOG ENABLE =====
    log_enabled_var = ctk.StringVar(value="on" if settings.get("log_enabled", False) else "off")
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
    
    entry_log_retention = ctk.CTkEntry(settings_frame, placeholder_text="Ex.: 7")
    entry_log_retention.insert(0, settings.get("log_retention", ""))
    entry_log_retention.pack(fill="x", expand=True, padx=20, pady=(0, 15))
    
    # ===== EXIBIR SAÍDA EM JANELA =====
    label_output_window = ctk.CTkLabel(
        settings_frame,
        text="Exibir saída do backup em janela:",
        text_color="white",
        font=("Arial", 12, "bold")
    )
    label_output_window.pack(anchor="w", padx=20, pady=(10, 5))

    show_output_window_var = ctk.StringVar(value="on" if settings.get("show_output_window", False) else "off")
    switch_show_output_window = ctk.CTkSwitch(
        settings_frame,
        text="Mostrar janela com o output da cópia",
        variable=show_output_window_var,
        onvalue="on",
        offvalue="off"
    )
    switch_show_output_window.pack(anchor="w", padx=20, pady=(0, 15))

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

    entry_smtp_host = ctk.CTkEntry(settings_frame, placeholder_text="smtp.exemplo.com")
    entry_smtp_host.insert(0, settings.get("smtp_host", ""))
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
    button_frame.pack(pady=(20, 10))

    def collect_current_settings():
        return {
            "backup_source_path": entry_backup_path.get().strip() or settings.get("backup_source_path", settings.get("backup_path", "C:\\Backups\\")),
            "backup_destination_path": entry_destination_path.get().strip() or settings.get("backup_destination_path", "\\\\192.168.0.150\\d$\\Backup Totvs"),
            "backup_folders": [item.strip() for item in entry_folder_list.get().split(",") if item.strip()],
            "copy_everything": copy_everything_var.get() == "on",
            "frequency": frequency_var.get(),
            "notifications": notifications_var.get(),
            "compression": compression_var.get(),
            "log_enabled": log_enabled_var.get() == "on",
            "log_retention": entry_log_retention.get().strip() or settings.get("log_retention", "30"),
            "show_output_window": show_output_window_var.get() == "on",
            "auto_backup_times": entry_auto_times.get().strip() or "13:00,21:00",
            "loop_backup_times": entry_loop_times.get().strip() or "13:00,21:00",
            "email_enabled": email_enabled_var.get() == "on",
            "sender_email": entry_sender_email.get().strip(),
            "recipient_email": entry_recipient_email.get().strip(),
            "email_mode": "always" if email_mode_var.get() == "Sempre" else "failed",
            "smtp_provider": provider_var.get(),
            "smtp_host": entry_smtp_host.get().strip() or "localhost",
            "smtp_port": int(entry_smtp_port.get().strip() or 25) if entry_smtp_port.get().strip() else 25,
            "smtp_username": entry_smtp_username.get().strip(),
            "smtp_password": entry_smtp_password.get(),
            "smtp_security": {
                "Nenhum": "none",
                "STARTTLS": "starttls",
                "SSL/TLS": "ssl"
            }.get(smtp_security_var.get(), "none")
        }

    def apply_settings_to_form(data):
        entry_backup_path.delete(0, "end")
        entry_backup_path.insert(0, data.get("backup_source_path", settings.get("backup_source_path", "C:\\Backups\\")))
        entry_destination_path.delete(0, "end")
        entry_destination_path.insert(0, data.get("backup_destination_path", "\\\\192.168.0.150\\d$\\Backup Totvs"))
        entry_folder_list.delete(0, "end")
        entry_folder_list.insert(0, ",".join(data.get("backup_folders", [])))
        copy_everything_var.set("on" if data.get("copy_everything", False) else "off")
        frequency_var.set(data.get("frequency", "Diário"))
        notifications_var.set(data.get("notifications", "on"))
        compression_var.set(data.get("compression", "off"))
        log_enabled_var.set("on" if data.get("log_enabled", True) else "off")
        entry_log_retention.delete(0, "end")
        entry_log_retention.insert(0, str(data.get("log_retention", "30")))
        show_output_window_var.set("on" if data.get("show_output_window", True) else "off")
        entry_auto_times.delete(0, "end")
        entry_auto_times.insert(0, data.get("auto_backup_times", "13:00,21:00"))
        entry_loop_times.delete(0, "end")
        entry_loop_times.insert(0, data.get("loop_backup_times", "13:00,21:00"))
        email_enabled_var.set("on" if data.get("email_enabled", False) else "off")
        entry_sender_email.delete(0, "end")
        entry_sender_email.insert(0, data.get("sender_email", ""))
        entry_recipient_email.delete(0, "end")
        entry_recipient_email.insert(0, data.get("recipient_email", ""))
        email_mode_var.set("Sempre" if data.get("email_mode", "always") == "always" else "Apenas falhas")
        provider_var.set(data.get("smtp_provider", detect_smtp_provider()))
        entry_smtp_host.delete(0, "end")
        entry_smtp_host.insert(0, data.get("smtp_host", "localhost"))
        entry_smtp_port.delete(0, "end")
        entry_smtp_port.insert(0, str(data.get("smtp_port", 25)))
        entry_smtp_username.delete(0, "end")
        entry_smtp_username.insert(0, data.get("smtp_username", ""))
        entry_smtp_password.delete(0, "end")
        entry_smtp_password.insert(0, data.get("smtp_password", ""))
        smtp_security_var.set({
            "ssl": "SSL/TLS",
            "starttls": "STARTTLS",
            "none": "Nenhum"
        }.get(data.get("smtp_security", "none"), "Nenhum"))
        toggle_email_fields()

    def save_settings():
        global settings, log_enabled, email_enabled
        log_enabled = log_enabled_var.get() == "on"
        email_enabled = email_enabled_var.get() == "on"

        settings.update(collect_current_settings())
        save_settings_file(settings)
        update_log_button()
        render_preview()
        settings_window.destroy()

    def restore_default_settings():
        global settings, log_enabled, email_enabled
        if not messagebox.askyesno("Restaurar padrões", "Deseja restaurar todas as configurações para os valores padrão?"):
            return
        settings = DEFAULT_SETTINGS.copy()
        save_settings_file(settings)
        apply_settings_to_form(settings)
        log_enabled = settings.get("log_enabled", True)
        email_enabled = settings.get("email_enabled", False)
        update_log_button()
        render_preview()
        messagebox.showinfo("Configurações", "Configurações padrão aplicadas com sucesso.")

    def import_settings():
        global settings, log_enabled, email_enabled
        path = filedialog.askopenfilename(title="Importar configurações", filetypes=[("Arquivos JSON", "*.json")], defaultextension=".json")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                imported = json.load(f)
            if not isinstance(imported, dict):
                raise ValueError("Arquivo inválido")
            merged = DEFAULT_SETTINGS.copy()
            merged.update(imported)
            settings = merged
            save_settings_file(settings)
            apply_settings_to_form(settings)
            log_enabled = settings.get("log_enabled", True)
            email_enabled = settings.get("email_enabled", False)
            update_log_button()
            render_preview()
            messagebox.showinfo("Configurações", "Configurações importadas com sucesso.")
        except Exception as e:
            messagebox.showerror("Importar configurações", f"Não foi possível importar as configurações:\n{e}")

    def export_settings():
        path = filedialog.asksaveasfilename(title="Exportar configurações", initialfile="backup_settings.json", filetypes=[("Arquivos JSON", "*.json")], defaultextension=".json")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(collect_current_settings(), f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Configurações", "Configurações exportadas com sucesso.")
        except Exception as e:
            messagebox.showerror("Exportar configurações", f"Não foi possível exportar as configurações:\n{e}")

    botao_restaurar = ctk.CTkButton(
        button_frame,
        text="Padrões",
        width=110,
        height=36,
        fg_color=PALETTE_SECONDARY,
        hover_color=PALETTE_SECONDARY_HOVER,
        text_color=PALETTE_TEXT,
        command=restore_default_settings
    )
    botao_restaurar.pack(side="left", padx=6)

    botao_importar = ctk.CTkButton(
        button_frame,
        text="Importar",
        width=110,
        height=36,
        fg_color=PALETTE_SECONDARY,
        hover_color=PALETTE_SECONDARY_HOVER,
        text_color=PALETTE_TEXT,
        command=import_settings
    )
    botao_importar.pack(side="left", padx=6)

    botao_exportar = ctk.CTkButton(
        button_frame,
        text="Exportar",
        width=110,
        height=36,
        fg_color=PALETTE_SECONDARY,
        hover_color=PALETTE_SECONDARY_HOVER,
        text_color=PALETTE_TEXT,
        command=export_settings
    )
    botao_exportar.pack(side="left", padx=6)

    action_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
    action_frame.pack(pady=(8, 20))

    botao_salvar = ctk.CTkButton(
        action_frame,
        text="Salvar",
        width=110,
        height=36,
        fg_color=PALETTE_ACCENT,
        hover_color=PALETTE_ACCENT_HOVER,
        text_color=PALETTE_TEXT,
        command=save_settings
    )
    botao_salvar.pack(side="left", padx=8)
    
    botao_cancelar = ctk.CTkButton(
        action_frame,
        text="Cancelar",
        width=110,
        height=36,
        fg_color=PALETTE_SECONDARY,
        hover_color=PALETTE_SECONDARY_HOVER,
        text_color=PALETTE_TEXT,
        command=settings_window.destroy
    )
    botao_cancelar.pack(side="left", padx=8)


botao_settings = ctk.CTkButton(
    button_container,
    text="Configurações",
    command=abrir_settings,
    width=280,
    height=42,
    fg_color=PALETTE_ACCENT,
    hover_color=PALETTE_ACCENT_HOVER,
    text_color=PALETTE_TEXT
)

botao_settings.grid(row=4, column=0, pady=(0, 8), padx=20)

footer_buttons_frame = ctk.CTkFrame(button_container, fg_color="transparent")
footer_buttons_frame.grid(row=5, column=0, sticky="sw", padx=20, pady=(8, 16))
footer_buttons_frame.grid_columnconfigure(0, weight=0)
footer_buttons_frame.grid_columnconfigure(1, weight=0)
footer_buttons_frame.grid_columnconfigure(2, weight=0)

botao_cancelar_backup = ctk.CTkButton(
    footer_buttons_frame,
    text="Cancelar Backup",
    width=120,
    height=36,
    fg_color=PALETTE_SECONDARY,
    hover_color=PALETTE_SECONDARY_HOVER,
    text_color=PALETTE_TEXT,
    command=cancelar_backup_em_execucao
)
botao_cancelar_backup.pack(side="left", padx=(0, 8))

botao_reiniciar = ctk.CTkButton(
    footer_buttons_frame,
    text="Reiniciar",
    width=110,
    height=36,
    fg_color=PALETTE_SECONDARY,
    hover_color=PALETTE_SECONDARY_HOVER,
    text_color=PALETTE_TEXT,
    command=reiniciar_programa
)
botao_reiniciar.pack(side="left", padx=(0, 8))

botao_fechar = ctk.CTkButton(
    footer_buttons_frame,
    text="Fechar",
    width=100,
    height=36,
    fg_color=PALETTE_SECONDARY,
    hover_color=PALETTE_SECONDARY_HOVER,
    text_color=PALETTE_TEXT,
    command=fechar_programa
)
botao_fechar.pack(side="left")


# ===== RODAR =====

app.after(200, prompt_initial_setup)
app.mainloop()
