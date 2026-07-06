import os
import subprocess
import datetime
import time
import threading
import json
import smtplib
import sys
import argparse
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

def emit(msg):
    print(msg, flush=True)

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')


def limpar_log_se_grande(max_mb=5):
    if os.path.exists(log_file):
        tamanho = os.path.getsize(log_file) / (1024 * 1024)
        if tamanho > max_mb:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("Log reiniciado\n")


def enviar_email_assunto_corpo(assunto, corpo):
    # reload settings so long-running process picks up GUI changes
    s = load_settings()
    enabled = s.get("email_enabled", False)
    sender = s.get("sender_email", "")
    recipient = s.get("recipient_email", "")
    if not enabled or not sender or not recipient:
        return

    smtp_h = s.get("smtp_host", DEFAULT_SETTINGS.get("smtp_host", "localhost"))
    try:
        smtp_p = int(s.get("smtp_port", DEFAULT_SETTINGS.get("smtp_port", 25)))
    except (TypeError, ValueError):
        smtp_p = DEFAULT_SETTINGS.get("smtp_port", 25)
    smtp_user = s.get("smtp_username", "")
    smtp_pass = s.get("smtp_password", "")
    smtp_sec = s.get("smtp_security", "none")
    smtp_provider = s.get("smtp_provider", "Personalizado")
    try:
        log(f"Tentando enviar e-mail SMTP: host={smtp_h} port={smtp_p} security={smtp_sec} provider={smtp_provider} user_set={bool(smtp_user)}")
        msg = EmailMessage()
        effective_sender = sender
        if smtp_provider == "Locaweb" and smtp_username and sender.lower() != smtp_username.lower():
            log(f"Locaweb provider: usando remetente SMTP autenticado em vez de {sender}")
            effective_sender = smtp_username
        msg["From"] = effective_sender
        msg["To"] = recipient
        msg["Subject"] = assunto
        msg.set_content(corpo)

        if smtp_sec == "ssl":
            smtp = smtplib.SMTP_SSL(smtp_h, smtp_p, timeout=30)
        else:
            smtp = smtplib.SMTP(smtp_h, smtp_p, timeout=30)
            try:
                smtp.ehlo()
            except Exception:
                pass
            if smtp_sec == "starttls":
                smtp.starttls()
                try:
                    smtp.ehlo()
                except Exception:
                    pass

        with smtp:
            if smtp_user and smtp_pass:
                smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)
        log("E-mail enviado com sucesso.")
    except Exception as e:
        log(f"Falha ao enviar e-mail: {e}")
        raise


def enviar_email_resumo(status_geral):
    s = load_settings()
    enabled = s.get("email_enabled", False)
    if not enabled:
        log("E-mail desativado nas configurações; não enviando resumo.")
        return

    email_mode_local = s.get("email_mode", "always")
    if email_mode_local == "failed" and status_geral == "OK":
        log("E-mail configurado para enviar apenas em falhas; sem envio de resumo OK.")
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

    emit(linha)


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

def listar_arquivos_para_copiar(base_path):
    arquivos = []
    for raiz, _, nomes_arquivos in os.walk(base_path):
        for nome_arquivo in nomes_arquivos:
            arquivos.append(os.path.join(raiz, nome_arquivo))
    return arquivos


def limpar_antigos(base_path, dias=5):

    agora = time.time()
    limite = dias * 86400

    if copy_everything:
        for raiz, _, arquivos in os.walk(base_path):
            for arquivo in arquivos:
                caminho_arquivo = os.path.join(raiz, arquivo)

                if agora - os.path.getmtime(caminho_arquivo) >= limite:
                    try:
                        os.remove(caminho_arquivo)
                        log(f"[Todos] removido antigo {arquivo}")
                    except Exception as exc:
                        log(f"[Todos] falha ao remover {arquivo}: {exc}")
    else:
        for pasta in pastas:

            caminho = os.path.join(base_path, pasta)

            if not os.path.exists(caminho):
                continue

            for arquivo in os.listdir(caminho):
                caminho_arquivo = os.path.join(caminho, arquivo)

                if not os.path.isfile(caminho_arquivo):
                    continue

                if agora - os.path.getmtime(caminho_arquivo) >= limite:
                    try:
                        os.remove(caminho_arquivo)
                        log(f"[{pasta}] removido antigo {arquivo}")
                    except Exception as exc:
                        log(f"[{pasta}] falha ao remover {arquivo}: {exc}")


# ===== ROBOCOPY =====

def build_robocopy_command(origem, destino, arquivo=None, move_files=False, recursive=False):
    comando = ["robocopy", origem, destino]

    if arquivo:
        comando.append(arquivo)

    if recursive:
        comando.append("/E")

    if move_files:
        comando.append("/MOV")

    comando.extend(["/R:3", "/W:5", "/Z", "/ETA"])
    return comando


def copiar_arquivo(origem, destino, arquivo, pasta):

    comando = build_robocopy_command(origem, destino, arquivo=arquivo)

    processo = subprocess.Popen(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    if processo.stdout:
        for linha in processo.stdout:
            if "%" in linha:
                try:
                    pct = float(linha.split("%")[0].split()[-1])

                    with lock:
                        progresso[pasta]["pct"] = pct
                        progresso[pasta]["status"] = f"Copiando {arquivo}"
                    emit(f"[{pasta}] Copiando {arquivo} ({pct:.1f}%)")
                except Exception:
                    pass

    processo.wait()
    return processo.returncode


def copiar_pasta_completa(origem, destino, pasta):
    comando = build_robocopy_command(origem, destino, move_files=True, recursive=True)

    processo = subprocess.Popen(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    if processo.stdout:
        for linha in processo.stdout:
            with lock:
                progresso[pasta]["status"] = f"Copiando {pasta}"
                progresso[pasta]["pct"] = 50
            emit(f"[{pasta}] Copiando {pasta}")

    processo.wait()
    return processo.returncode


def remover_arquivos_copiados(origem, destino):
    if not os.path.exists(origem):
        return

    for raiz, _, arquivos in os.walk(origem, topdown=False):
        for arquivo in arquivos:
            origem_arq = os.path.join(raiz, arquivo)
            rel_path = os.path.relpath(origem_arq, origem)
            destino_arq = os.path.join(destino, rel_path)

            if os.path.exists(destino_arq):
                try:
                    os.remove(origem_arq)
                    log(f"Origem limpa após cópia: {origem_arq}")
                except Exception as exc:
                    log(f"Não foi possível remover {origem_arq}: {exc}")

    for raiz, dirs, _ in os.walk(origem, topdown=False):
        for nome_dir in dirs:
            caminho_dir = os.path.join(raiz, nome_dir)
            try:
                if os.path.isdir(caminho_dir) and not os.listdir(caminho_dir):
                    os.rmdir(caminho_dir)
            except Exception:
                pass


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
        emit(f"[{pasta}] Iniciando {pasta}")

        codigo = copiar_pasta_completa(origem, destino, pasta)

        if codigo <= 3:
            remover_arquivos_copiados(origem, destino)
            with lock:
                progresso[pasta]["status"] = "OK"
                progresso[pasta]["pct"] = 100
            emit(f"[{pasta}] OK")
        else:
            with lock:
                progresso[pasta]["status"] = "Erro cópia"
            emit(f"[{pasta}] Erro cópia")

        return

    try:
        arquivos = listar_arquivos_para_copiar(origem)
    except Exception:
        with lock:
            progresso[pasta]["status"] = "Erro acesso"
        return

    if not arquivos:
        with lock:
            progresso[pasta]["status"] = "OK"
            progresso[pasta]["pct"] = 100
        return

    for caminho_arq in arquivos:
        rel_path = os.path.relpath(caminho_arq, origem)
        destino_arq = os.path.join(destino, rel_path)

        if os.path.exists(destino_arq):
            try:
                os.remove(caminho_arq)
            except Exception:
                pass
            continue

        os.makedirs(os.path.dirname(destino_arq), exist_ok=True)

        with lock:
            progresso[pasta]["pct"] = 0
            progresso[pasta]["status"] = f"Iniciando {rel_path}"
        emit(f"[{pasta}] Iniciando {rel_path}")

        codigo = copiar_arquivo(origem, destino, rel_path, pasta)

        if codigo <= 3:
            try:
                os.remove(caminho_arq)
            except Exception:
                pass

            with lock:
                progresso[pasta]["status"] = "OK"
                progresso[pasta]["pct"] = 100
        else:
            with lock:
                progresso[pasta]["status"] = "Erro cópia"


# ===== LOOP =====

def executar(loop=False, sleep_seconds=None):

    if loop:
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

        emit(f"Status geral do backup: {status_geral}")
        enviar_email_resumo(status_geral)

        if not loop:
            return status_geral

        time.sleep(sleep_seconds or tempo_espera)


# ===== START =====

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup Manager")
    parser.add_argument("--loop", action="store_true", help="Executa continuamente")
    parser.add_argument("--wait-seconds", type=int, default=60, help="Intervalo entre execuções em modo loop")
    args = parser.parse_args()
    executar(loop=args.loop, sleep_seconds=args.wait_seconds)
