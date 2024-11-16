# Comunicação Serial com Nobreak

Projeto para comunicação com nobreaks sms, enviando comandos e decodificando respostas.

## Funcionalidades

- Envia comandos como consulta de status e teste de bateria.
- Decodifica respostas para exibir informações como:
  - Tensão de entrada e saída.
  - Nível de bateria.
  - Potência e temperatura.
  - Status geral.

## Como Usar

1. **Pré-requisitos**:  
   - Python 3.6+  
   - Instale a biblioteca `pyserial`:  
     ```bash
     pip install pyserial
     ```

2. **Configuração**:  
   Ajuste a porta serial no código (`COM5` ou `/dev/ttyUSB0`) e o baud rate (padrão: 2400).


