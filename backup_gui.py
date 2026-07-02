import customtkinter as ctk
import subprocess
import os
from PIL import Image

ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.title("Controle de Backup")
app.geometry("520x420")
app.iconbitmap(r"C:\backup_manager\leao_preto.ico")

# ===== FUNDO PRETO =====

frame = ctk.CTkFrame(app, fg_color="black")
frame.pack(fill="both", expand=True)

# ===== LOGO =====

logo_img = ctk.CTkImage(
    light_image=Image.open(r"C:\backup_manager\logo1.png"),
    size=(80,80)
)

logo = ctk.CTkLabel(frame, image=logo_img, text="")
logo.place(x=30,y=20)

# ===== TITULO =====

titulo = ctk.CTkLabel(
    frame,
    text="CONTROLE DE BACKUP",
    text_color="#2596be",
    font=("Arial",24,"bold")
)

titulo.place(x=130,y=40)

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
    frame,
    text="Executar Backup Manual",
    command=lambda: rodar(r"C:\backup_manager\backup_manager_total.py"),
    width=300
)

botao1.place(x=110,y=140)


botao2 = ctk.CTkButton(
    frame,
    text="Executar Backup Auto",
    command=lambda: rodar(r"C:\backup_manager\backup_auto.py"),
    width=300
)

botao2.place(x=110,y=190)


botao3 = ctk.CTkButton(
    frame,
    text="Executar Backup Loop",
    command=lambda: rodar(r"C:\backup_manager\backup_loop.ps1"),
    width=300
)

botao3.place(x=110,y=240)


botao4 = ctk.CTkButton(
    frame,
    text="Ver Log",
    command=lambda: rodar(r"C:\backup_manager\backup_log.txt"),
    width=300
)

botao4.place(x=110,y=290)


# ===== RODAR =====

app.mainloop()
