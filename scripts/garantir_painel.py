import socket
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PAINEL_PY = BASE_DIR / "painel.py"
PORT = 8050


def is_port_in_use(port: int = PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex(("127.0.0.1", port)) == 0


def iniciar_painel():
    if is_port_in_use():
        print(f"Painel Web já está ativo e respondendo na porta {PORT} (http://localhost:{PORT}).")
        return True

    print(f"Iniciando Painel Web na porta {PORT} em segundo plano...")
    # Launch detached process in Windows
    DETACHED_PROCESS = 0x00000008
    CREATE_NO_WINDOW = 0x08000000
    flags = DETACHED_PROCESS | CREATE_NO_WINDOW

    subprocess.Popen(
        [sys.executable, str(PAINEL_PY)],
        cwd=str(BASE_DIR),
        creationflags=flags,
        close_fds=True,
    )

    # Wait up to 5 seconds for it to start
    for _ in range(10):
        time.sleep(0.5)
        if is_port_in_use():
            print(f"Painel Web iniciado com sucesso em http://localhost:{PORT}!")
            return True

    print(f"Aviso: O painel foi disparado, mas ainda não respondeu na porta {PORT}.")
    return False


if __name__ == "__main__":
    iniciar_painel()
