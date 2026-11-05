# Instalação detalhada (português de Portugal)

**Primeira instalação?** Segue primeiro o [guia rápido para principiantes](QUICKSTART.pt-PT.md).

**Este guia destina-se a um Raspberry Pi Zero W com microSD novo e Raspberry Pi OS Lite 32-bit.** O motor original foi testado num MiTo, mas a instalação do repositório num cartão novo ainda tem de ser validada por terceiros.

## 1. Preparar Raspberry Pi OS

1. Grava **Raspberry Pi OS Lite (32-bit)** usando Raspberry Pi Imager. O Zero W original não é um dispositivo 64-bit.
2. Nas opções do Imager configura um utilizador, SSH, Wi-Fi, país `PT` (ou o teu país) e a palavra-passe de tua escolha. Usa uma rede 2,4 GHz compatível com o Zero W.
3. Liga o Pi à alimentação e acede por SSH através do endereço atribuído pelo teu router.
4. Faz atualizações e reinicia se houver atualizações do kernel.

```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

**Mantém SSH pelo Wi-Fi**, porque a porta USB de dados será utilizada como dispositivo de armazenamento.

## 2. Obter e instalar o projeto

```bash
sudo apt install -y git
git clone https://github.com/technabo33/blueandme-usb-bridge.git
cd blueandme-usb-bridge
sudo bash scripts/install.sh
```

O instalador instala as dependências via APT, copia o motor para `/opt/blueandme-bridge`, gera uma imagem FAT32 *sparse* de **24 horas** (48 WAV), configura serviços e ativa o controlador `dwc2` para modo gadget. **Não substitui uma v0.5.6 antiga instalada fora de `/opt`** para proteger instalações já funcionais.

O ficheiro de configuração criado é `/etc/default/blueandme-bt`; não o publiques nem copies para o GitHub.

Se tiveres um utilizador de instalação especial, podes defini-lo explicitamente:

```bash
sudo BM_INSTALL_USER=omeuutilizador bash scripts/install.sh
```

Opcionalmente, para usar uma biblioteca virtual mais curta:

```bash
sudo BM_HOURS=12 bash scripts/install.sh
```

> A variável `BM_HOURS` aplica-se à geração inicial de uma imagem inexistente. O instalador **preserva** imagens já criadas.

## 3. Reiniciar e verificar a pen virtual

```bash
sudo reboot
```

No Raspberry:

```bash
systemctl is-active blueandme-bt-v056.service
sudo bash /opt/blueandme-bridge/diagnostico-v056.sh
```

Liga a porta **USB de dados** do Zero W ao computador com cabo de dados. O computador deverá identificar uma unidade `BMSTREAM` com WAV e uma playlist. **Nunca a formates.** Ejeta-a antes de parar o serviço ou desligar o Pi. O volume é apenas de leitura e contém WAV lógicos, não música gravada.

## 4. Emparelhar o telemóvel com o Pi

Antes do emparelhamento, o Pi deve estar ligado por SSH. A ponte desativa o modo de descoberta por segurança, por isso para temporariamente o serviço:

```bash
sudo systemctl stop blueandme-bt-v056.service
sudo bluetoothctl
```

Dentro da consola `bluetoothctl`:

```text
power on
agent on
default-agent
pairable on
discoverable on
```

Nas definições Bluetooth do telemóvel, procura o Raspberry Pi e inicia o emparelhamento. Confirma o mesmo código em ambos os dispositivos, se for apresentado. Depois usa o endereço Bluetooth do **teu** telemóvel:

```text
devices Paired
info AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
discoverable off
pairable off
quit
```

Confirma que `info` apresenta `Paired: yes`, `Trusted: yes` e suporte `Audio Source` (UUID A2DP). Substitui o MAC de exemplo pelo do teu dispositivo. Não publiques esse endereço nos relatórios de erro.

### Tornar a reconexão mais rápida

```bash
cd ~/blueandme-usb-bridge
sudo bash scripts/set-phone.sh AA:BB:CC:DD:EE:FF
sudo systemctl start blueandme-bt-v056.service
```

O script só aceita um dispositivo que já esteja emparelhado, autorizado e com A2DP Source. A ponte nunca autoriza um telemóvel só por conhecer o endereço MAC.

No telemóvel, seleciona o Raspberry Pi como dispositivo de áudio e inicia música numa aplicação. O rádio deverá tocar enquanto estiver a ler os WAV virtuais.

## 5. Instalação no automóvel

- Usa a **porta USB original que aceita pens USB**.
- Fornece 5 V estáveis ao Pi. Verifica que a energia disponibilizada pelo carro é suficiente para o hardware.
- No rádio, seleciona a fonte Media Player/USB e deixa ler os WAV.
- Não uses o conector **PWR IN** do Pi para fazer a ligação de dados ao carro.
- Não tentes emparelhar o carro diretamente ao Pi como se este fosse um telefone mãos-livres. O Pi apresenta-se ao carro como **pen USB**.

## 6. Proteger o cartão contra desligamentos da ignição

**Só faz isto depois de o som e o emparelhamento funcionarem.**

```bash
sudo sync
sudo raspi-config
```

Em **Performance Options → Overlay File System**, ativa **Overlay** e **Write-protect Boot Partition**; termina e reinicia.

```bash
findmnt -n -o FSTYPE /           # esperado: overlay
findmnt -n -o TARGET,OPTIONS /boot/firmware
```

Confirma que a partição de arranque apresenta `ro`. O OverlayFS permite escritas temporárias em RAM, mas descarta alterações após reiniciar. A proteção reduz o risco de corrupção por cortes de energia, **não o elimina completamente**.

> Para atualizar ou alterar configurações: desativa OverlayFS e proteção do boot no `raspi-config`, reinicia, faz as alterações, volta a ativar e reinicia outra vez.

## 7. Diagnóstico

```bash
sudo bash ~/blueandme-usb-bridge/scripts/health-check.sh
journalctl -b -u blueandme-bt-v056.service -o short-monotonic --no-pager | tail -50
sudo tail -30 /run/blueandme/capture-bt-v056.log
sudo tail -30 /run/blueandme/reads-bt-v056.log
```

**Não publiques os logs sem ocultar endereços MAC.** Consulta [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Desinstalação conservadora

Com o OverlayFS desativado:

```bash
cd ~/blueandme-usb-bridge
sudo bash scripts/uninstall.sh
```

Por segurança, este comando só remove o serviço. Preserva o diretório de dados, a configuração Bluetooth e a configuração `dwc2`, que poderão ser usados por outras aplicações.
