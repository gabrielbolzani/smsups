import serial
import binascii
import json
import time


# Dicionário de comandos
cmd = {
    'Q': bytearray([0x51, 0xFF, 0xFF, 0xFF, 0xFF, 0xB3, 0x0D]),  # pega_dados "Q"
    'I': bytearray([0x49, 0xFF, 0xFF, 0xFF, 0xFF, 0xBB, 0x0D]),  # retorna nome do no-break
    'D': bytearray([0x44, 0xFF, 0xFF, 0xFF, 0xFF, 0xC0, 0x0D]),  # para teste de bateria
    'F': bytearray([0x46, 0xFF, 0xFF, 0xFF, 0xFF, 0xBE, 0x0D]),  # características
    'G': bytearray([0x47, 0x01, 0xFF, 0xFF, 0xFF, 0xBB, 0x0D]),  # comando G
    'M': bytearray([0x4D, 0xFF, 0xFF, 0xFF, 0xFF, 0xB7, 0x0D]),  # liga/desliga beep
    'T': bytearray([0x54, 0x00, 0x10, 0x00, 0x00, 0x9C, 0x0D]),  # testa bateria por 10 segundos
    'T1': bytearray([0x54, 0x00, 0x64, 0x00, 0x00, 0x48, 0x0D]),  # teste bateria por 100 segundos
    'T2': bytearray([0x54, 0x00, 0xC8, 0x00, 0x00, 0xE4, 0x0D]),  # teste bateria por 200 segundos
    'T3': bytearray([0x54, 0x01, 0x2C, 0x00, 0x00, 0x7F, 0x0D]),  # teste bateria por 300 segundos
    'T9': bytearray([0x54, 0x03, 0x84, 0x00, 0x00, 0x25, 0x0D]),  # teste bateria por 900 segundos
    'C': bytearray([0x43, 0xFF, 0xFF, 0xFF, 0xFF, 0xC1, 0x0D]),  # cancelamento de shutdown
    'L': bytearray([0x4C, 0xFF, 0xFF, 0xFF, 0xFF]),               # teste bateria baixa
    'R': bytearray([0x52, 0x00, 0xC8, 0x27, 0x0F, 0xB0, 0x0D]),   # shutdown e restore
    'zzz': bytearray([0x52, 0x00, 0xC8, 0x0F, 0xEF, 0xE0, 0x0D]), # comando zzz
    'zz1': bytearray([0x52, 0x01, 0x2C, 0x27, 0x0F, 0x4B, 0x0D]), # comando zz1
    'S': bytearray([0x53])                                       # shutdown em n segundos
}

def calcular_checksum(comando):
    return sum(comando) & 0xFF

def enviar_comando(ser, comando):
    print("Comando enviado : ", binascii.hexlify(comando))  # Mostrar comando enviado
    ser.write(comando)  # Enviar o comando
    resposta = ser.read(32)  # Ler a resposta (ajuste o número de bytes conforme necessário)
    #print("Resposta recebida (bruta):", binascii.hexlify(resposta))  # Mostrar resposta bruta
    return resposta

def hex_to_ascii(bytes_input):
    return bytes_input.decode('ascii', errors='ignore')


def decode_nobreak_data(raw_data):
    """
    Decodifica a resposta recebida do nobreak em um dicionário completo de valores.

    :param raw_data: Dados brutos em bytes recebidos do nobreak.
    :return: Dicionário contendo os dados decodificados.
    """
    def toINT16(valor_hex):
        """Converte valor hexadecimal para inteiro de 16 bits."""
        return int(valor_hex, 16)

    def decode_status_bits(status_bits):
        """
        Decodifica o campo status_bits em um dicionário de indicadores.

        :param status_bits: String binária representando os bits de status.
        :return: Dicionário com a interpretação de cada bit.
        """
        return {
            "beep_enabled": bool(int(status_bits[7])),
            "shutdown_active": bool(int(status_bits[6])),
            "test_active": bool(int(status_bits[5])),
            "ups_ok": bool(int(status_bits[4])),
            "boost_active": bool(int(status_bits[3])),
            "bypass_active": bool(int(status_bits[2])),
            "low_battery": bool(int(status_bits[1])),
            "battery_in_use": bool(int(status_bits[0])),
        }

    # Verifica se os dados começam com '3d'
    r_data = raw_data.hex()
    if r_data[:2] != '3d':
        raise ValueError("Dados inválidos: Não começam com '3d'.")

    # Divide os dados brutos em segmentos
    segmentos = [
        r_data[0:2],   # 0 - Identificador
        r_data[2:6],   # 1 - Última tensão de entrada (Vac)
        r_data[6:10],  # 2 - Tensão de entrada (Vac)
        r_data[10:14], # 3 - Tensão de saída (Vac)
        r_data[14:18], # 4 - Potência de saída
        r_data[18:22], # 5 - Frequência de saída (Hz)
        r_data[22:26], # 6 - Nível de bateria
        r_data[26:30], # 7 - Temperatura (°C)
        r_data[30:32], # 8 - Status (bits)
        r_data[32:34], # 9 - Reservado/Extra
        r_data[34:36], # 10 - Checksum
    ]

    # Decodifica os dados para variáveis específicas
    decoded_data = {
        "last_input_Vac": toINT16(segmentos[1]) / 10,
        "input_Vac": toINT16(segmentos[2]) / 10,
        "output_Vac": toINT16(segmentos[3]) / 10,
        "output_power": toINT16(segmentos[4]) / 10,
        "output_Hz": toINT16(segmentos[5]) / 10,
        "battery_level": toINT16(segmentos[6]) / 10,
        "temperature_C": toINT16(segmentos[7]) / 10,
    }

    # Decodifica o campo status
    status_bin = "{:08b}".format(toINT16(segmentos[8]))  # Converte para binário com 8 bits
    decoded_data["status"] = decode_status_bits(status_bin)

    return decoded_data



def comunicacao_nobreak(cmd_to_send):
    porta_serial = 'COM5'  # Ajuste conforme necessário
    baudrate = 2400
    timeout = 1  # Tempo de espera para leitura
    try:

        ser = serial.Serial(porta_serial, baudrate=baudrate, timeout=timeout)
        print(f'Conectado à porta {porta_serial} Baud: {baudrate}')

        comando_escolhido = cmd[cmd_to_send]
        resposta = enviar_comando(ser, comando_escolhido)
        if resposta:
            print(f"Resposta recebida (bruta): {binascii.hexlify(resposta)}")
            if cmd_to_send == 'I':
                print(f"Resposta convertida: {hex_to_ascii(resposta)}")
            if cmd_to_send == 'F':
                print(f"Resposta convertida: {hex_to_ascii(resposta)}")
            if cmd_to_send == 'Q':
                print("Resposta convertida:")
                print(json.dumps(decode_nobreak_data(resposta), indent=4))
        else:
            print(f"Não obteve resposta")



    except Exception as e:
        print(f"Erro na comunicação: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("\n \nConexão fechada.")


if __name__ == "__main__":
    while True:
        comunicacao_nobreak('Q')
        time.sleep(2)
