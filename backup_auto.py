import time
import subprocess
from datetime import datetime

while True:
    agora = datetime.now().strftime("%H:%M")

    if agora in ["13:00", "21:00"]:
        subprocess.run(r"C:\backup_manager\backup_totvs.bat")
        time.sleep(60)

    time.sleep(20)
