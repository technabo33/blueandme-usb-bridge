# Diagnóstico e resolução de problemas

## 1. A unidade BMSTREAM não aparece

```bash
systemctl status blueandme-bt-v056.service --no-pager
lsmod | grep -E '^(dwc2|g_mass_storage|nbd) '
lsblk /dev/nbd0
journalctl -b -u blueandme-bt-v056.service -o short-monotonic --no-pager | tail -80
```

Verifica o cabo de **dados**, a porta **USB** do Pi Zero W, `dtoverlay=dwc2`, a alimentação e o suporte de gadget no kernel. Não ligues o gadget por USB a mais do que um host ao mesmo tempo. A imagem não deve ser aberta como sistema de ficheiros em modo de escrita no Pi enquanto o dispositivo USB está ativo.

Mensagens `nbd_client: Connection refused` durante os primeiros segundos podem ser normais: são tentativas antes de o plugin nbdkit aceitar conexões. Se continuarem indefinidamente, consulta `/run/blueandme/server-bt-v056.log`.

## 2. O telemóvel não aparece ou não liga

```bash
systemctl status bluetooth.service bluealsa.service --no-pager
bluetoothctl devices Paired
bluetoothctl info AA:BB:CC:DD:EE:FF
bluealsa-cli list-pcms
```

Confirma `Paired: yes`, `Trusted: yes` e suporte A2DP Audio Source. O `FASTPCM` só acelera um telefone anteriormente autorizado. Se estiveres a emparelhar um telefone novo, para o serviço temporariamente, ativa `pairable on` e `discoverable on`, e repõe ambos em `off` depois.

## 3. O Bluetooth liga mas o rádio só reproduz silêncio

```bash
sudo grep -E 'FASTPCM|Fonte ativa|A2DP arecord' /run/blueandme/capture-bt-v056.log | tail -20
sudo grep -E 'RESYNC|nonzero=' /run/blueandme/reads-bt-v056.log | tail -20
```

O `arecord` precisa de iniciar e o BlueALSA tem de apresentar um PCM. Em `reads`, `nonzero=0` pode significar silêncio digital ou que o telemóvel ainda não começou a reproduzir. Se o rádio já leu silêncio antes de o Bluetooth estar pronto, poderá ter colocado dados em cache. Tenta mudar de ficheiro WAV ou ejetar/remontar a USB com segurança, em vez de formatar a unidade.

## 4. O BlueALSA não inicia

O projeto foi testado com BlueALSA **4.3.1**. Nas versões 5.x, os nomes de certos executáveis mudaram; esta edição **ainda não está validada** nessa versão. Confirma:

```bash
bluealsa --version
command -v bluealsa-cli
systemctl cat bluealsa.service
```

Se o serviço existente não fornecer o perfil `a2dp-sink`, configura-o segundo as instruções da tua distribuição. O instalador não sobrepõe um serviço BlueALSA fornecido pelo sistema.

## 5. Alterações desaparecem depois do reboot

É o comportamento esperado quando o **OverlayFS** está ativo. Para instalar versões, alterar MAC ou configurar Wi-Fi, desativa-o temporariamente com `sudo raspi-config` e reinicia. Não uses `mount -o remount,rw /` como substituto improvisado do processo normal de manutenção.

## 6. Tempos de arranque longos

```bash
systemd-analyze time
journalctl -b -u blueandme-bt-v056.service -o short-monotonic --no-pager | grep BMSTART
```

No sistema de referência, o NBD demorava ~13 s a aceitar ligações depois de ser lançado. Os tempos variam com o cartão, versão do sistema e telefone. **Não desatives serviços de rede à distância sem um plano de recuperação**, especialmente se dependes de SSH.

## 7. Como partilhar logs num issue

Oculta endereços MAC, nomes de dispositivos, IPs, SSIDs e outros dados pessoais antes de publicar. Informa apenas o modelo/ano do carro, sistema Raspberry Pi OS, versão do projeto, sintomas e passos de reprodução.
