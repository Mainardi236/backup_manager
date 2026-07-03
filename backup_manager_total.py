import os
import subprocess
import datetime
import time
import threading
import json
import smtplib
from email.message import EmailMessage
from concurrent.futures import ThreadPoolExecutor

# ===== CONFIG =====

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "backup_settings.json")

DEFAULT_SETTINGS = {
    "backup_source_path": r"\\192.168.0.250\\backup",
    "backup_destination_path": r"\\192.168.0.150\\d$\\Backup Totvs",
    "backup_folders": ["master", "msdb", "model", "sigaoficialtss", "sigaoficial"],
    "copy_everything": False,
    "email_enabled": False,
    "sender_email": "",
    "recipient_email": "",
    "email_mode": "always",
    "smtp_host": "localhost",
    "smtp_port": 25,
    "smtp_username": "",
    "smtp_password": "",
    "smtp_security": "none"
}

def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except Exception:
        settings = DEFAULT_SETTINGS.copy()

    for key, value in DEFAULT_SETTINGS.items():
        settings.setdefault(key, value)

    return settings


settings = load_settings()
origem_base = settings.get("backup_source_path", DEFAULT_SETTINGS["backup_source_path"])
destino_base = settings.get("backup_destination_path", DEFAULT_SETTINGS["backup_destination_path"])
copy_everything = settings.get("copy_everything", False)
backup_folders = settings.get("backup_folders", DEFAULT_SETTINGS["backup_folders"])
pastas = ["Tudo"] if copy_everything else backup_folders

log_file = "backup_log.txt"
tempo_espera = 60

email_enabled = settings.get("email_enabled", False)
sender_email = settings.get("sender_email", "")
recipient_email = settings.get("recipient_email", "")
email_mode = settings.get("email_mode", "always")

smtp_host = settings.get("smtp_host", DEFAULT_SETTINGS["smtp_host"])
try:
    smtp_port = int(settings.get("smtp_port", DEFAULT_SETTINGS["smtp_port"]))
except (TypeError, ValueError):
    smtp_port = DEFAULT_SETTINGS["smtp_port"]
smtp_username = settings.get("smtp_username", "")
smtp_password = settings.get("smtp_password", "")
smtp_security = settings.get("smtp_security", "none")

# ===== ANSI COLORS =====

class C:
    RESET = "\033[0m"
    VERDE = "\033[92m"
    VERMELHO = "\033[91m"
    AMARELO = "\033[93m"
    AZUL = "\033[94m"
    CYAN = "\033[96m"
    CINZA = "\033[90m"
    BOLD = "\033[1m"

# ===== CONTROLE =====

progresso = {p: {"pct": 0, "status": "Aguardando"} for p in pastas}
lock = threading.Lock()


# ===== UTIL =====

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')


def limpar_log_se_grande(max_mb=5):
    if os.path.exists(log_file):
        tamanho = os.path.getsize(log_file) / (1024 * 1024)
        if tamanho > max_mb:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("Log reiniciado\n")


def enviar_email_assunto_corpo(assunto, corpo):
    if not email_enabled or not sender_email or not recipient_email:
        return

    try:
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = assunto
        msg.set_content(corpo)

        if smtp_security == "ssl":
            smtp = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
        else:
            smtp = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            if smtp_security == "starttls":
                smtp.starttls()

        with smtp:
            if smtp_username and smtp_password:
                smtp.login(smtp_username, smtp_password)
            smtp.send_message(msg)
    except Exception as e:
        log(f"Falha ao enviar e-mail: {e}")


def enviar_email_resumo(status_geral):
    if not email_enabled:
        return

    if email_mode == "failed" and status_geral == "OK":
        return

    assunto = "Backup concluído" if status_geral == "OK" else "Backup com falha"
    corpo = f"Status geral do backup: {status_geral}\n\nLogs recentes:\n"

    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            corpo += f.read()[-2000:]

    enviar_email_assunto_corpo(assunto, corpo)


# ===== LOG =====

def log(msg):
    agora = datetime.datetime.now()
    linha = f"{agora:%Y-%m-%d %H:%M:%S} - {msg}"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


# ===== COR POR STATUS =====

def cor_status(status):
    if "OK" in status:
        return C.VERDE
    elif "Erro" in status:
        return C.VERMELHO
    elif "Copiando" in status:
        return C.AMARELO
    elif "Iniciando" in status:
        return C.AZUL
    else:
        return C.CINZA


# ===== PAINEL =====

def desenhar_painel():

    while True:
        limpar_tela()

        agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(C.BOLD + C.CYAN + "=== BACKUP MONITOR (NOC) ===" + C.RESET)
        print(C.CINZA + f"Atualizado: {agora}" + C.RESET)
        print()

        with lock:
            for pasta in pastas:
                pct = progresso[pasta]["pct"]
                status = progresso[pasta]["status"]

                barra_total = 30
                preenchido = int((pct / 100) * barra_total)

                barra = "█" * preenchido + "░" * (barra_total - preenchido)

                cor = cor_status(status)

                print(
                    f"{C.BOLD}{pasta:<20}{C.RESET} "
                    f"[{cor}{barra}{C.RESET}] "
                    f"{pct:6.1f}% | {cor}{status}{C.RESET}"
                )

        time.sleep(0.5)


# ===== LIMPEZA =====

def limpar_antigos(base_path, dias=5):

    agora = time.time()
    limite = dias * 86400

    if copy_everything:
        for raiz, _, arquivos in os.walk(base_path):
            for arquivo in arquivos:
                if not arquivo.lower().endswith(".bak"):
                    continue

                caminho_arquivo = os.path.join(raiz, arquivo)

                if agora - os.path.getmtime(caminho_arquivo) >= limite:
                    try:
                        os.remove(caminho_arquivo)
                        log(f"[Todos] removido antigo {arquivo}")
                    except:
                        pass
    else:
        for pasta in pastas:

            caminho = os.path.join(base_path, pasta)

            if not os.path.exists(caminho):
                continue

            for arquivo in os.listdir(caminho):

                if not arquivo.lower().endswith(".bak"):
                    continue

                caminho_arquivo = os.path.join(caminho, arquivo)

                if agora - os.path.getmtime(caminho_arquivo) >= limite:
                    try:
                        os.remove(caminho_arquivo)
                        log(f"[{pasta}] removido antigo {arquivo}")
                    except:
                        pass


# ===== ROBOCOPY =====

def copiar_arquivo(origem, destino, arquivo, pasta):

    comando = [
        "robocopy",
        origem,
        destino,
        arquivo,
        "/R:3",
        "/W:5",
        "/Z",
        "/ETA"
    ]

    processo = subprocess.Popen(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for linha in processo.stdout:

        if "%" in linha:
            try:
                pct = float(linha.split("%")[0].split()[-1])

                with lock:
                    progresso[pasta]["pct"] = pct
                    progresso[pasta]["status"] = f"Copiando {arquivo}"

            except:
                pass

    processo.wait()
    return processo.returncode


def copiar_pasta_completa(origem, destino, pasta):
    comando = [
        "robocopy",
        origem,
        destino,
        "/E",
        "/R:3",
        "/W:5",
        "/Z",
        "/ETA"
    ]

    processo = subprocess.Popen(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for linha in processo.stdout:
        with lock:
            progresso[pasta]["status"] = f"Copiando {pasta}"

    processo.wait()
    return processo.returncode


# ===== PROCESSAMENTO =====

def processar_pasta(pasta):

    if copy_everything and pasta == "Tudo":
        origem = origem_base
        destino = destino_base
    else:
        origem = os.path.join(origem_base, pasta)
        destino = os.path.join(destino_base, pasta)

    os.makedirs(destino, exist_ok=True)

    if copy_everything:
        with lock:
            progresso[pasta]["pct"] = 0
            progresso[pasta]["status"] = f"Iniciando {pasta}"

        codigo = copiar_pasta_completa(origem, destino, pasta)

        if codigo <= 3:
            with lock:
                progresso[pasta]["status"] = "OK"
                progresso[pasta]["pct"] = 100
        else:
            with lock:
                progresso[pasta]["status"] = "Erro cópia"

        return

    try:
        arquivos = os.listdir(origem)
    except:
        with lock:
            progresso[pasta]["status"] = "Erro acesso"
        return

    for arquivo in arquivos:

        if not arquivo.lower().endswith(".bak"):
            continue

        origem_arq = os.path.join(origem, arquivo)
        destino_arq = os.path.join(destino, arquivo)

        if os.path.exists(destino_arq):
            try:
                os.remove(origem_arq)
            except:
                pass
            continue

        with lock:
            progresso[pasta]["pct"] = 0
            progresso[pasta]["status"] = f"Iniciando {arquivo}"

        codigo = copiar_arquivo(origem, destino, arquivo, pasta)

        if codigo <= 3:
            try:
                os.remove(origem_arq)
            except:
                pass

            with lock:
                progresso[pasta]["status"] = "OK"
                progresso[pasta]["pct"] = 100
        else:
            with lock:
                progresso[pasta]["status"] = "Erro cópia"


# ===== LOOP =====

def executar():

    threading.Thread(target=desenhar_painel, daemon=True).start()

    while True:

        limpar_log_se_grande()

        limpar_antigos(origem_base)
        limpar_antigos(destino_base)

        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.map(processar_pasta, pastas)

        status_geral = "OK"
        with lock:
            for p in pastas:
                if "Erro" in progresso[p]["status"]:
                    status_geral = "Falha"
                progresso[p]["status"] = "Aguardando"
                progresso[p]["pct"] = 0

        enviar_email_resumo(status_geral)
        time.sleep(tempo_espera)


# ===== START =====

if __name__ == "__main__":
    executar()
