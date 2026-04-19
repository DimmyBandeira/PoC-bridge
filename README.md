# PoC Bridge API

Middleware entre o WebGuardião e a plataforma iConvNet (PoC) para envio de alertas de texto e foto para rádios comunicadores.

## Requisitos

- Python 3.10+
- Ubuntu Server (com NTP sincronizado)
- PM2 (opcional, para gerenciamento do processo)

## Instalação

1. Clone o repositório no servidor Ubuntu:
   ```bash
   git clone <seu-repo> poc-bridge
   cd poc-bridge