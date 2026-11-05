# Blue&Me NAVFIX v0.5.8 (experimental)

## Objetivo

Na v0.5.6, a passagem para outro WAV virtual pode pedir áudio 1800 segundos à frente, mas o buffer Bluetooth tem apenas 40 segundos. O resultado pode ser silêncio no Blue&Me, embora a mesma troca funcione no Windows.

Esta experiência corrige **apenas o mapeamento de áudio entre WAVs**: cada WAV secundário passa a ter um ponto de sincronização independente, sem alterar a referência da faixa inicial quando o Blue&Me lê ficheiros antecipadamente. Não envia comandos AVRCP e **não muda o Spotify**.

É um teste em laboratório e no carro; **não está validado no MiTo**. O próprio rádio pode usar cache dos dados lidos anteriormente, que esta alteração não consegue controlar.

## O que NÃO muda

* `blueandme-bt-v056.service`, `start_bt_v056.sh`, Bluetooth, BlueALSA e FASTPCM;
* A imagem FAT32 e os 48 WAV virtuais;
* O buffer A2DP de oito segundos;
* O software do carro.

A versão continua a apresentar o nome `blueandme-bt-v056.service` porque esta experiência altera apenas o ficheiro Python carregado por esse serviço. A cópia original fica guardada.

## Instalação no Raspberry, com alimentação estável

**Pré-requisitos:** ter revertido a v0.5.7 para a v0.5.6 e ter o OverlayFS desativado. Confirma `findmnt -n -o FSTYPE /` = `ext4` e `systemctl is-active blueandme-bt-v056.service` = `active`.

No Windows, depois de descarregar o ZIP:

```powershell
scp "$env:USERPROFILE\Downloads\BlueAndMe_NAVFIX_v058.zip" utilizador@IP_DO_RASPBERRY:~/
```

Substitui `utilizador@IP_DO_RASPBERRY` pelos dados da tua instalação.

No Raspberry, com a USB virtual **ejetada no Windows**:

```bash
cd ~/blueandme-live
unzip -o ~/BlueAndMe_NAVFIX_v058.zip -d ~/blueandme-live
sudo bash ~/blueandme-live/navfix-v058/install-navfix-v058.sh ~/blueandme-live
```

O instalador confirma que a v0.5.6 é exatamente a versão original, testa a correção, cria uma cópia e, se o gadget USB não iniciar, restaura automaticamente o motor original.

## Teste

1. Primeiro, no Windows, verifica se o streaming Bluetooth continua estável ao avançar e recuar pelos WAV.
2. No MiTo **parado e estacionado**, começa com a reprodução normal.
3. Carrega uma vez em faixa seguinte. Espera alguns segundos e verifica se a música continua.
4. Volta à faixa anterior e confirma o mesmo.
5. Se houver qualquer falha de reconexão ou som, não prossigas com experiências AVRCP e executa o rollback.

## Diagnóstico em casa

```bash
systemctl is-active blueandme-bt-v056.service
sudo grep -E 'NAVFIX058|FILE_READ|PREFETCH/SEEK' /run/blueandme/reads-bt-v056.log | tail -35
```

Os logs em `/run` desaparecem com o desligamento. Evita partilhar logs Bluetooth completos sem ocultar os identificadores dos telemóveis.

## Reversão imediata

Com a unidade USB ejetada:

```bash
sudo bash ~/blueandme-live/navfix-v058/rollback-navfix-v058.sh ~/blueandme-live
```

**Não publicar como release estável no GitHub antes de validação física.** A v0.5.6 original permanece a referência.
