# Blue&Me WheelControl v0.6.1 Beta: Seguinte / Anterior

**Compatibilidade:** Raspberry Pi Zero W, ponte Blue&Me USB/NAVFIX v0.5.8 funcional e WheelControl v0.6.0 Beta previamente instalado.

Esta beta troca **apenas `/opt/blueandme-wheel-v060/detector.py`**. O `monitor.py`, `wheelctl.py`, `avrcp.py`, serviço USB (`blueandme-bt-v056.service`), imagem FAT32, áudio A2DP, BlueALSA e emparelhamento Bluetooth permanecem inalterados.

## Regras

- Se há leitura sustentada de `FLX00010.WAV` e passa para `FLX00011.WAV` **antes do fim natural**: emitir evento provável `next`.
- Se a reprodução sustentada passa de `FLX00010.WAV` para `FLX00009.WAV`: emitir evento provável `previous`.
- A identificação usa linhas `STATUS` com áudio, duas amostras consecutivas para estabelecer o WAV atual e três amostras com progressão temporal no WAV seguinte (habitualmente cerca de 6 segundos).
- `FILE_READ` e `NAVFIX` isolados, scans de todos os WAV e trocas não adjacentes **não** originam um comando. Mudança natural de WAV nos últimos ~50 segundos não origina Next.
- Cada evento tem proteção temporal para reduzir duplicados. Os eventos são **inferências**: a USB não fornece o estado real dos botões; leituras de cache podem continuar a produzir falsos positivos. Comandos muito rápidos podem não ser reconhecidos.
- O envio de comandos AVRCP por defeito permanece `observe` (desligado). **A v0.6.1 não controla automaticamente o Spotify até optares por ativar.**

## Instalar

No Windows PowerShell, depois de descarregar o ZIP para Downloads:

```powershell
scp "$env:USERPROFILE\Downloads\BlueAndMe_WheelControl_v061_Botoes.zip" UTILIZADOR@IP_DO_RASPBERRY:~
```

No Raspberry:

```bash
cd ~
unzip -o BlueAndMe_WheelControl_v061_Botoes.zip
cd BlueAndMe_WheelControl_v061_Botoes
sudo bash install-v061.sh
```

O instalador executa testes, valida o ficheiro original da v0.6.0, cria cópia de segurança, desativa o modo automático, atualiza só o detetor e reinicia somente o processo auxiliar. Se o serviço não arrancar, tenta restabelecer a cópia original. Instalação recusada se OverlayFS estiver ativo.

## Testar no Windows sem enviar comandos

1. Abre o WAV 1 e deixa-o reproduzir 15 segundos.
2. Passa ao WAV 2 e deixa-o reproduzir pelo menos 12 segundos.
3. Volta ao WAV 1 e deixa-o reproduzir 12 segundos.
4. Espera alguns segundos e lê o relatório:

```bash
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py report
```

Deverá surgir `TRACK_CHANGE_PROBABLE,next,1,2,NOT_CONFIRMED` e `TRACK_CHANGE_PROBABLE,previous,2,1,NOT_CONFIRMED`, dependendo do leitor e do padrão de acesso. Estes eventos **não** provam que foram pressionados botões no carro.

## Ativar AVRCP automático **só depois de validar o relatório**

Confirma primeiro que o Spotify responde a comandos manuais `next` e `previous`, tal como já testaste. Se ambos os marcadores manuais existem, ativa:

```bash
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py auto-on --confirmed
```

Para desativar imediatamente:

```bash
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py auto-off
```

Consulta as ações efetuadas:

```bash
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py report
```

`AVRCP_SENT` indica aceitação do pedido pelo D-Bus; **não** comprova que o Spotify mudou efetivamente de música.

## Recuperar versão anterior

```bash
cd ~/BlueAndMe_WheelControl_v061_Botoes
sudo bash rollback-v061.sh
```

Restaura somente o detetor v0.6.0 e deixa o envio automático desligado.

## Nota sobre o MiTo

O teste Windows é útil para validar deteção e AVRCP, mas **não substitui uma validação no Blue&Me**. O comportamento de cache USB pode ser diferente. Faz testes no carro apenas com o veículo parado e estacionado. Com OverlayFS desligado, os CSV de diagnóstico são escritos no microSD; remove o serviço de diagnóstico temporário quando já não for necessário para diminuir escritas.
