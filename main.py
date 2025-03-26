import pymem
import time
import keyboard
import threading
import ctypes
from ctypes import wintypes

# Nome do processo do jogo - você precisará substituir pelo nome correto
PROCESS_NAME = "DriveBeyondHorizons-Win64-Shipping.exe"

# Endereços de memória encontrados com o Cheat Engine (formato hexadecimal)
ADDRESSES = [
    0x1EA309C39C0,  # Primeiro endereço
    0x1E99CBFE0A0   # Segundo endereço
]

# Valor que você quer definir
NEW_VALUE = 999.0

# Constantes do Windows para VirtualProtectEx
PAGE_EXECUTE_READWRITE = 0x40
PROCESS_ALL_ACCESS = 0x1F0FFF

# Funções da API Windows
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

VirtualProtectEx = kernel32.VirtualProtectEx
VirtualProtectEx.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
VirtualProtectEx.restype = wintypes.BOOL

def continuous_writer(pm, addresses, value, stop_event):
    """Thread que escreve continuamente nos endereços de memória"""
    old_protect = wintypes.DWORD(0)

    # Tenta mudar a proteção de memória para permitir escrita
    for address in addresses:
        VirtualProtectEx(pm.process_handle, address, 8, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))

    counter = 0
    while not stop_event.is_set():
        for address in addresses:
            try:
                # Escreve o valor diretamente
                pm.write_double(address, value)

                # A cada 1000 iterações, verifica se o valor está correto
                if counter % 1000 == 0:
                    current = pm.read_double(address)
                    if abs(current - value) > 0.01:
                        print(f"[AVISO] Valor em 0x{address:X} está {current} (esperado {value})")
            except:
                pass  # Ignora erros para manter o script rodando

        counter += 1
        # Micro-pausa para não sobrecarregar a CPU
        time.sleep(0.001)

def main():
    print(f"Tentando conectar ao processo: {PROCESS_NAME}")

    try:
        # Conecta ao processo do jogo
        pm = pymem.Pymem(PROCESS_NAME)
        print(f"Conectado ao processo com ID: {pm.process_id}")

        # Guarda os valores originais
        original_values = []
        for address in ADDRESSES:
            try:
                value = pm.read_double(address)
                original_values.append(value)
                print(f"Endereço: 0x{address:X} - Valor original: {value}")
            except:
                print(f"Não foi possível ler o endereço: 0x{address:X}")
                original_values.append(0.0)

        print("\nControles:")
        print("  F1: Iniciar modificação contínua (modo agressivo)")
        print("  F2: Restaurar valores originais")
        print("  ESC: Sair")

        # Evento para controlar o thread
        stop_thread = threading.Event()
        writer_thread = None

        while True:
            # Inicia modo agressivo
            if keyboard.is_pressed('F1') and writer_thread is None:
                print("\n[ATIVADO] Modo de escrita agressiva")
                stop_thread.clear()
                writer_thread = threading.Thread(
                    target=continuous_writer,
                    args=(pm, ADDRESSES, NEW_VALUE, stop_thread)
                )
                writer_thread.daemon = True
                writer_thread.start()
                time.sleep(0.3)

            # Restaura valores originais
            if keyboard.is_pressed('F2'):
                if writer_thread is not None:
                    stop_thread.set()
                    writer_thread.join()
                    writer_thread = None
                    print("\n[PARADO] Modo de escrita agressiva")

                print("\n[RESTAURANDO] Valores originais")
                for i, address in enumerate(ADDRESSES):
                    try:
                        pm.write_double(address, original_values[i])
                    except:
                        print(f"Não foi possível restaurar o endereço: 0x{address:X}")
                time.sleep(0.3)

            # Sai do script
            if keyboard.is_pressed('esc'):
                if writer_thread is not None:
                    stop_thread.set()
                    writer_thread.join()
                print("\nSaindo...")
                break

            time.sleep(0.01)

    except pymem.exception.ProcessNotFound:
        print(f"Erro: Processo '{PROCESS_NAME}' não encontrado.")
        print("Certifique-se de que o jogo está em execução e o nome do processo está correto.")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    print("=== Game Memory Trainer Avançado ===")
    main()
