# Blue&Me USB Bluetooth Bridge 🚗🎵

**Ouvir áudio Bluetooth através da entrada USB original de rádios Blue&Me que só reconhecem pens USB.** Um projeto comunitário, independente e de código aberto, baseado num **Raspberry Pi Zero W**.

[![Testes](https://github.com/technabo33/blueandme-usb-bridge/actions/workflows/test.yml/badge.svg)](https://github.com/technabo33/blueandme-usb-bridge/actions/workflows/test.yml)
![Versão](https://img.shields.io/badge/vers%C3%A3o-0.5.6%20community-blue)
![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

🚀 **[Começar do zero (guia simples)](QUICKSTART.pt-PT.md)** · 📖 **[Guia completo](INSTALL.pt-PT.md)** · 🌍 **[English README](README.en.md)** · 🧰 **[Resolução de problemas](TROUBLESHOOTING.md)** · 🌐 **[Site do projeto](https://technabo33.github.io/blueandme-usb-bridge/)**

> **Estado:** motor da v0.5.6 validado em Raspberry Pi Zero W com Alfa Romeo MiTo 2010 e Blue&Me original. O **instalador comunitário**, adaptado para computadores e telemóveis diferentes, foi sujeito a testes de sintaxe e testes de geração FAT32, mas ainda precisa de validação completa numa instalação limpa.

> **Versão estável de referência:** [v0.5.8 NAVFIX](https://github.com/technabo33/blueandme-usb-bridge/releases/tag/v0.5.8). Áudio USB/Bluetooth validado pelo utilizador no MiTo, sem WheelControl. É um patch para a instalação antiga `blueandme-bt-v056.service`; segue o guia incluído no ZIP. A instalação comunitária de raiz abaixo continua na v0.5.6.

> **Pré-release beta disponível em paralelo:** [v0.6.1-beta.1 — NAVFIX v0.5.8 + WheelControl v0.6.1](https://github.com/technabo33/blueandme-usb-bridge/releases/tag/v0.6.1-beta.1). [Instalação, limites e rollback](beta/v0.6.1-beta.1/README.pt-PT.md). Pacote para a instalação antiga `blueandme-bt-v056.service`; não é uma atualização automática do instalador comunitário abaixo. Ensaios prolongados no carro ainda pendentes.

## O problema

Alguns sistemas Blue&Me antigos conseguem reproduzir música de uma pen USB, mas não aceitam música Bluetooth A2DP através dessa entrada. Um adaptador Bluetooth USB normal não é reconhecido como biblioteca de música.

## A solução

```text
Telemóvel / Spotify / outras apps
          | Bluetooth A2DP
          v
 Raspberry Pi Zero W
   BlueZ + BlueALSA + Python
          | áudio PCM em RAM
          v
   FAT32 virtual, 48 WAV
          | NBD + g_mass_storage
          v
USB de dados do carro → Blue&Me → rádio
```

O Raspberry apresenta-se ao carro como uma **pen USB de armazenamento, apenas de leitura**. Os ficheiros WAV e a playlist estão numa imagem FAT32 *sparse*, mas os dados de áudio são fornecidos em tempo real a partir do Bluetooth. Não há conversão para AUX, nem emissor FM, nem modificação do rádio.

## Demonstração e resultados medidos

No sistema de referência:

| Etapa | Tempo aproximado |
| --- | ---: |
| Pen USB disponível | 63 s |
| Ligação e captura A2DP | ~79 s |
| Primeiras amostras PCM válidas enviadas pela USB | ~89 s |

A música foi observada como audível aos 80 s num teste cronometrado separado. Os relógios dos testes não foram sincronizados, por isso não apresentamos um tempo único garantido. A reprodução foi relatada como estável nos testes anteriores com o MiTo.

## Material

- Raspberry Pi **Zero W** ou, experimentalmente, Zero 2 W (não validado neste projeto).
- microSD de **16 GB ou mais**, preferencialmente 32 GB de boa qualidade.
- Alimentação USB **5 V estável**.
- Cabo **micro-USB de dados**, ligado à porta **USB** do Pi Zero W, não à porta **PWR IN**. Pode ser necessário um adaptador OTG adequado conforme a instalação.
- Telemóvel Android com A2DP (outros modelos e iOS ainda por testar).
- Rádio/automóvel capaz de ler pens FAT32 e WAV PCM de **44,1 kHz, 16 bits, estéreo**.

> A compatibilidade é determinada pelo leitor USB do automóvel. **Não** funciona automaticamente em todos os rádios ou todas as versões do Blue&Me.

## Instalação rápida

Começa com **Raspberry Pi OS Lite 32-bit**, SSH e Wi-Fi a funcionar. **Não uses a tua instalação funcional como cobaia**: experimenta preferencialmente noutro microSD.

```bash
sudo apt update
sudo apt install -y git
# Depois de criares/abrires o repositório público:
git clone https://github.com/technabo33/blueandme-usb-bridge.git
cd blueandme-usb-bridge
sudo bash scripts/install.sh
sudo reboot
```

Depois, emparelha o telemóvel e define-o como dispositivo prioritário. **Começa pelo [guia simples](QUICKSTART.pt-PT.md) e, se necessário, consulta o [guia completo](INSTALL.pt-PT.md).** Não saltes os passos de emparelhamento nem atives o OverlayFS antes de terminar a configuração.

## Segurança e privacidade

Consulta também [PRIVACY.md](PRIVACY.md) para informações sobre dados guardados localmente.

- A ponte aceita apenas telemóveis previamente **emparelhados e marcados como Trusted**.
- A unidade USB é exportada como **read-only**, evitando alterações no FAT32 pelo leitor.
- Os logs operacionais ficam em `/run/blueandme`, na RAM.
- Não existem passwords, SSIDs, IPs domésticos, endereços Bluetooth reais ou imagens de cartões SD no repositório.
- **OverlayFS + proteção da partição de arranque** são recomendados para automóveis com cortes de alimentação, mas não substituem alimentação elétrica estável.
- Não publiques `bluetoothctl info`, logs, ficheiros de configuração locais ou fotografias identificáveis sem os reveres.

## Estrutura

```text
app/                   motor USB e captura A2DP v0.5.6
scripts/install.sh     instalação para um Pi novo
scripts/set-phone.sh   seleção segura do telemóvel
scripts/health-check.sh diagnóstico
systemd/               serviços
INSTALL.pt-PT.md       instalação passo a passo
TROUBLESHOOTING.md     problemas frequentes
SAFETY.md              segurança e proteção do microSD
docs/                  website GitHub Pages
.github/workflows/     testes automáticos do código
```

## Limitações conhecidas

- O rádio pode fazer cache ou leitura antecipada e provocar silêncio quando se muda de ficheiro/faixa.
- A virtualização USB exige um controlador USB gadget OTG, não basta um PC genérico.
- O projeto usa uma imagem FAT32 de **16 GiB lógicos** para 24 horas, mas ocupa muito menos espaço real enquanto continuar *sparse* num sistema compatível.
- A reprodução de áudio depende da app do telemóvel; o projeto não força o Spotify a iniciar.
- Na versão comunitária v0.5.6, os botões do volante ainda não controlam o telemóvel. O pacote beta separado acrescenta controlo experimental Next/Previous por AVRCP, inferido das leituras WAV, com intervalo mínimo de 9 segundos entre eventos.
- Ligação automática depende do Android/BlueZ e de emparelhamento anterior.

## Ajudar o projeto

Relata o modelo e ano do automóvel, versão do Blue&Me, Raspberry, sistema operativo e resultados de teste (sem divulgar MAC, IP, SSID ou dados pessoais). Consulta [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença e marcas

Código publicado sob [MIT](LICENSE). Projeto **não oficial**, sem afiliação a Alfa Romeo, Fiat, Stellantis, Microsoft, Spotify ou Raspberry Pi. Todas as marcas pertencem aos respetivos titulares. **Não contém música, gravações ou conteúdo protegido de terceiros.**
