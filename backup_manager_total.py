import os
import subprocess
import datetime
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# ===== CONFIG =====

origem_base = r"\\192.168.0.250\backup"
destino_base = r"\\192.168.0.150\d$\Backup Totvs"

pastas = [
    "master",
    "msdb",
    "model",
    "sigaoficialtss",
    "sigaoficial"
]

log_file = "backup_log.txt"
tempo_espera = 60

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


# ===== PROCESSAMENTO =====

def processar_pasta(pasta):

    origem = os.path.join(origem_base, pasta)
    destino = os.path.join(destino_base, pasta)

    os.makedirs(destino, exist_ok=True)

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

        with lock:
            for p in pastas:
                progresso[p]["status"] = "Aguardando"
                progresso[p]["pct"] = 0

        time.sleep(tempo_espera)


# ===== START =====

if __name__ == "__main__":
    executar()
