# Base v0.5.6-community.1 — instalação limpa

Pacote completo da base comunitária para um Raspberry Pi Zero W com microSD novo e Raspberry Pi OS Lite 32-bit. Inclui motor USB/Bluetooth, instalador, serviços, testes e documentação. Não é uma imagem de cartão: prepara primeiro o sistema operativo.

Esta base fica disponível separadamente da v0.5.8 NAVFIX e da v0.6.1-beta.1. Não inclui NAVFIX nem WheelControl.

## Como instalar
1. Grava Raspberry Pi OS Lite 32-bit com Raspberry Pi Imager. Configura utilizador, Wi-Fi 2,4 GHz e SSH.
2. Descarrega e descomprime `BlueAndMe_Base_v0.5.6-community.1.zip` no Raspberry.
3. Na pasta extraída:
```bash
sudo bash scripts/install.sh
sudo reboot
```
4. Segue `QUICKSTART.pt-PT.md` para emparelhar e autorizar o telemóvel, configurar a prioridade e testar áudio.

O Raspberry necessita de Internet para instalar dependências. O instalador cria os ficheiros em `/opt/blueandme-bridge` e instala `blueandme-bt-v056.service`. O nome `systemd/blueandme-bt.service` é o ficheiro de origem, que o instalador copia com o sufixo v056.

## Validação
O motor original foi testado num MiTo. O instalador comunitário tem verificações automáticas, mas a instalação completa num cartão limpo e a compatibilidade com versões atuais dos pacotes do Raspberry Pi OS ainda exigem validação física. Usa um cartão separado da instalação funcional.

## Atualizações e recuperação
Os patches NAVFIX e WheelControl continuam disponíveis nas respetivas releases. Não os apliques automaticamente sobre esta base: o motor comunitário tem diferenças e os hashes exigidos pelos patches antigos podem não corresponder. Ter o mesmo nome de serviço não garante compatibilidade.

Para desativar a base, consulta `scripts/uninstall.sh` e o guia detalhado. O procedimento conserva dados, Bluetooth e configuração USB.

O ZIP está fixado ao commit `17df629c7cde344e5b5473904d673ea43c80864f`, anterior à adição dos pacotes beta. Novas releases não substituem este asset. O ficheiro SHA256SUMS.txt permite verificar integridade.
