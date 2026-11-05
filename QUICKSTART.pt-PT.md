# Começar do zero: versão simples

> **Importante:** esta edição comunitária deriva de uma v0.5.6 funcional num Raspberry Pi Zero W e num Alfa Romeo MiTo Blue&Me. O instalador para cartões novos ainda está em validação; utiliza um microSD de teste e não substituas uma instalação que já funciona.

## Material necessário

- Raspberry Pi Zero W; microSD de 16 GB ou mais (32 GB recomendado).
- Cabo micro-USB de **dados**; ligação à porta `USB` do Pi (perto da mini-HDMI), não à `PWR IN`.
- Alimentação estável 5 V; computador Windows/macOS/Linux para preparar o cartão; rede Wi-Fi **2,4 GHz**.
- Telemóvel com Bluetooth A2DP; rádio que leia uma pen FAT32 com WAV PCM.

## 1. Preparar o cartão

1. Instala **Raspberry Pi Imager** no computador.
2. Seleciona **Raspberry Pi Zero W**, **Raspberry Pi OS Lite (32-bit)** e o microSD.
3. Na personalização, define um **nome de utilizador à tua escolha**, uma palavra-passe forte, o Wi-Fi 2,4 GHz e o país correto. Ativa **SSH**.
4. Grava o cartão, coloca-o no Pi e liga a alimentação. Aguarda que se ligue ao Wi-Fi.
5. Descobre o IP no router ou tenta `raspberrypi.local` e liga-te por SSH. Exemplo (troca `utilizador`): `ssh utilizador@raspberrypi.local`.

O Pi deve ter acesso à Internet. Mantém o acesso SSH por Wi-Fi: a porta USB de dados ficará ocupada pelo gadget.

## 2. Instalar o software

No terminal SSH, cola os comandos **um de cada vez**:

```bash
sudo apt update
sudo apt install -y git
git clone https://github.com/technabo33/blueandme-usb-bridge.git
cd blueandme-usb-bridge
sudo bash scripts/install.sh
sudo reboot
```

O instalador descarrega os pacotes necessários, cria a imagem FAT32 com WAV virtuais e configura o arranque automático. Pode demorar no Pi Zero W. Se `apt` indicar um pacote inexistente, consulta [resolução de problemas](TROUBLESHOOTING.md) e abre uma issue com a versão do Raspberry Pi OS, sem incluir dados pessoais.

## 3. Confirmar a pen USB

```bash
systemctl is-active blueandme-bt-v056.service
sudo bash /opt/blueandme-bridge/diagnostico-v056.sh
```

Liga a porta `USB` do Pi a um computador com um **cabo de dados**. Deve aparecer uma unidade `BMSTREAM`. Os WAV são virtuais e podem reproduzir silêncio até ligares o telemóvel. **Não formates a unidade**. Ejeta-a antes de desligar o Pi.

## 4. Emparelhar o telemóvel

No Pi, por SSH:

```bash
sudo systemctl stop blueandme-bt-v056.service
sudo bluetoothctl
```

Dentro do `bluetoothctl`:

```text
power on
agent on
default-agent
pairable on
discoverable on
```

Abre o Bluetooth do telemóvel e emparelha com o Raspberry. Confirma o código de emparelhamento, quando pedido. Na consola, executa (substitui o MAC do exemplo pelo endereço que aparece em `devices Paired`):

```text
devices Paired
info AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
discoverable off
pairable off
quit
```

De volta ao terminal SSH:

```bash
cd ~/blueandme-usb-bridge
sudo bash scripts/set-phone.sh AA:BB:CC:DD:EE:FF
sudo systemctl start blueandme-bt-v056.service
```

Se o telemóvel não mostrar A2DP como disponível, consulta o [guia completo](INSTALL.pt-PT.md).

## 5. Testar áudio antes de instalar no carro

- Liga a unidade ao PC e confirma que `BMSTREAM` aparece.
- Liga o telemóvel ao Raspberry como dispositivo de **áudio multimédia**. Inicia música no telemóvel.
- No rádio do carro, seleciona **USB / Media Player** e deixa reproduzir um WAV.
- Se não houver som, verifica logs em [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

A unidade não contém faixas gravadas; cada WAV representa uma janela do áudio Bluetooth em tempo real. Alguns leitores podem guardar silêncio em cache.

## 6. Proteger o microSD contra cortes de alimentação

**Só depois de tudo funcionar** e após guardar a configuração do telemóvel:

```bash
sudo sync
sudo raspi-config
```

Escolhe **Performance Options → Overlay File System** e ativa o OverlayFS e a proteção da partição de arranque. Reinicia, e confirma:

```bash
findmnt -n -o FSTYPE /
findmnt -n -o TARGET,OPTIONS /boot/firmware
```

A primeira linha deve ser `overlay`; a partição de arranque deve mostrar `ro`. Alterações feitas depois disto serão temporárias e **desaparecem ao reiniciar**. Para atualizar o software ou trocar de telemóvel, desativa o OverlayFS no `raspi-config`, reinicia, altera e volta a ativá-lo. Não corta a alimentação enquanto estiveres a configurar.

O OverlayFS reduz bastante o risco de corrupção, mas não substitui uma alimentação estável nem elimina todos os riscos de falha física.

## Diagnóstico rápido

```bash
systemctl status blueandme-bt-v056.service --no-pager
sudo tail -40 /run/blueandme/capture-bt-v056.log
sudo bash scripts/health-check.sh
```

**Privacidade:** os logs contêm frequentemente MACs Bluetooth. Antes de partilhar, consulta [PRIVACY.md](PRIVACY.md).
