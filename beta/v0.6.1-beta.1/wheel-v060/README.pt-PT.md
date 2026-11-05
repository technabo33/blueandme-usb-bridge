# Blue&Me Bridge v0.6.0 Beta: controlos do volante → Spotify

**Experiência independente para quem já usa a v0.5.8 NAVFIX**, instalada por cima do serviço v0.5.6. **Não é um novo motor de áudio.** Foi preparada para um Alfa Romeo MiTo/Blue&Me com Raspberry Pi Zero W, mas a deteção de botões ainda tem de ser comprovada no carro.

## O que faz

1. Mantém a v0.5.8 NAVFIX, a imagem FAT32, os 48 WAV, BlueALSA e o serviço `blueandme-bt-v056.service` intactos.
2. Adiciona `blueandme-wheel-v060.service`, um processo auxiliar que só **lê** `/run/blueandme/reads-bt-v056.log`.
3. Procura sequências de leituras progressivas em dois WAV adjacentes. Ignora saltos isolados, leituras antecipadas, silêncio, perda da ligação Bluetooth e mudanças naturais no fim de 30 minutos.
4. Guarda candidatos à mudança de faixa num CSV simples, sem endereços Bluetooth, IP ou SSID: `/var/lib/blueandme-wheel/observations.csv`.
5. Inclui um comando AVRCP manual e **opcionalmente** o envio automático de `Next`/`Previous` ao telemóvel, através da interface `org.bluez.MediaPlayer1`.

> **Importante:** observar leituras USB não permite saber com 100% de certeza se um botão foi premido. A lógica de deteção é experimental. O modo automático está **desligado por defeito**, mesmo após reiniciar. Primeiro valida os resultados no teu carro, parado e estacionado.

## Requisitos

- v0.5.8 NAVFIX a funcionar, com o nome de serviço original `blueandme-bt-v056.service`.
- Raspberry Pi OS com Python 3 e BlueZ (`busctl`, `bluetoothctl`); não é necessário instalar bibliotecas Python extra.
- OverlayFS desativado durante a instalação. Confirma com `findmnt -n -o FSTYPE /`, que deverá indicar `ext4`.
- Telemóvel previamente emparelhado, marcado como Trusted e com áudio A2DP a funcionar.
- Testes sempre com o veículo **parado e estacionado**.

## Instalar (a partir do Windows)

Descarrega o ZIP e abre o PowerShell. Substitui `utilizador@IP_DO_RASPBERRY` pelos dados da tua instalação:

```powershell
scp "$env:USERPROFILE\Downloads\BlueAndMe_WheelControl_v060_Beta.zip" utilizador@IP_DO_RASPBERRY:~/
```

No Raspberry, se o ZIP ainda estiver em `~/`:

```bash
cd ~
unzip -o BlueAndMe_WheelControl_v060_Beta.zip
cd BlueAndMe_v060_WheelControl
sudo bash install-v060.sh
```

Confirma:

```bash
systemctl is-active blueandme-bt-v056.service
systemctl is-active blueandme-wheel-v060.service
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py report
```

Ambos os serviços devem indicar `active`. O primeiro é a ponte de áudio já validada e não deve mudar. O relatório pode inicialmente conter só `START`.

## Passo 1: testar AVRCP em casa, sem o carro

Com o telemóvel ligado ao Raspberry por Bluetooth e com o Spotify a tocar, executa:

```bash
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py status
```

Se aparecer `Player AVRCP ... disponivel`, envia apenas um comando manual:

```bash
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py next
```

Confirma no telemóvel se o Spotify realmente avançou. Depois testa:

```bash
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py previous
```

**O D-Bus aceitar o comando não garante que o Spotify o executou.** Se não funcionar, não atives o modo automático: primeiro precisamos de diagnosticar o perfil AVRCP/Android.

## Passo 2: teste passivo no MiTo, sem SSH

Deixa o modo por defeito em `observe`. O serviço arranca sozinho com o Raspberry.

Com o carro parado e estacionado:

1. Espera que a música comece a tocar normalmente.
2. Não toques nos botões durante 20 segundos.
3. Prime **Seguinte** uma vez e aguarda 15 segundos.
4. Prime **Anterior** uma vez e aguarda 15 segundos.
5. Repete os dois botões com pausas iguais.
6. Deixa tocar sem tocar nos comandos mais 20 segundos.

O programa regista **apenas mudanças de WAV prováveis**. Uma deteção pode ser falsa ou pode não ser detetada, porque depende do padrão de leitura do rádio.

Quando regressares a casa, liga novamente o Raspberry e consulta:

```bash
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py report
```

O relatório é persistente porque o teu OverlayFS está desativado. Como existe risco de corte brusco de alimentação no automóvel, cada evento é gravado e sincronizado. Isso reduz mas não elimina o risco de corrupção do microSD. Ao voltar a casa, se possível encerra corretamente o Raspberry.

Podes copiar apenas o CSV anonimizado para o Windows:

```powershell
scp utilizador@IP_DO_RASPBERRY:/var/lib/blueandme-wheel/observations.csv .
```

Se o acesso a esse ficheiro estiver protegido (permissões `600`), usa no Raspberry:

```bash
sudo cp /var/lib/blueandme-wheel/observations.csv ~/wheel-observations.csv
sudo chown "$USER":"$USER" ~/wheel-observations.csv
```

E depois no Windows:

```powershell
scp utilizador@IP_DO_RASPBERRY:~/wheel-observations.csv .
```

### Interpretar o relatório

- `START` significa que o processo auxiliar iniciou.
- `TRACK_CHANGE_PROBABLE` é um candidato, não prova física de pressão no botão.
- Se aparecerem eventos sem teres tocado nos botões, **não atives o modo automático**.
- Se não aparecer nenhum evento após os botões, teremos de melhorar a identificação dos padrões reais antes de avançar.

## Passo 3 (opcional): ativar o envio automático

**Só depois de confirmar** que os dois comandos AVRCP manuais alteram o Spotify e que o relatório passivo não apresenta falsos positivos durante o teste:

```bash
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py auto-on --confirmed
```

A partir daí, quando o detetor considerar uma mudança suficientemente provável, o serviço envia o comando AVRCP no processo auxiliar, sem bloquear as leituras USB. Isto ainda é experimental e deve ser testado **apenas com o carro parado**. Não garante deteção perfeita nem compatibilidade com todos os modelos Blue&Me.

Para desativar os comandos a qualquer momento, preservando o resto do sistema:

```bash
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py auto-off
```

## Recuperação imediata

Para parar o processo auxiliar sem remover a instalação:

```bash
sudo systemctl disable --now blueandme-wheel-v060.service
```

Para desinstalar o serviço auxiliar:

```bash
cd ~/BlueAndMe_v060_WheelControl
sudo bash uninstall-v060.sh
```

**Nenhum destes comandos modifica a v0.5.8 NAVFIX nem o serviço Bluetooth original.**

## Limitações atuais

- Não é possível identificar diretamente uma pressão do volante via USB mass storage: é necessário inferir pela sequência de leituras.
- Leituras antecipadas podem parecer navegação; por isso usamos confirmação progressiva e rejeitamos mudanças perto do fim natural de cada WAV.
- O comando AVRCP é independente do WAV e pode chegar ao Android com atraso.
- O primeiro botão depois do arranque pode não ser observado até existirem três amostras de áudio do WAV atual.
- Pressões muito rápidas podem ser ignoradas de propósito para evitar comandos duplicados.
- A instalação foi validada por testes em ambiente de desenvolvimento, **não foi testada ainda no teu MiTo**.
- O modo automático deve permanecer desligado até obtermos um relatório do teu carro.

## Testes do pacote

```bash
python3 -m unittest discover -s tests -v
```
