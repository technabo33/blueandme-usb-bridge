# Blue&Me v0.6.1-beta.1 — NAVFIX + WheelControl

Pré-release beta para testes. Reúne NAVFIX v0.5.8 e WheelControl v0.6.1, mantendo os motores e instaladores originais. Não inclui v0.6.1a nem a futura página local de diagnóstico.

## Estado de validação

- NAVFIX v0.5.8: funcionamento relatado pelo utilizador no Alfa Romeo MiTo.
- WheelControl v0.6.1: Next e Previous relatados como funcionais; intervalo mínimo de 9 segundos entre eventos. Não é um atraso de resposta garantido.
- Ensaios prolongados em viagens e instalação limpa desta combinação: pendentes.
- Testes automáticos são verificações offline e não validam o hardware.

## Escolher a instalação correta

Este é um pacote de atualização para a instalação antiga que utiliza `blueandme-bt-v056.service`. O instalador comunitário na raiz do repositório utiliza `blueandme-bt.service`: esta combinação não está validada e os instaladores beta recusam-na. Não renomear serviços para contornar as verificações.

Se já tens NAVFIX v0.5.8 + WheelControl v0.6.1 funcionais, não precisas de reinstalar. Esta release arquiva essa configuração para testes e distribuição.

Descomprime o ZIP e abre a pasta `BlueAndMe_v0.6.1-beta.1`.

### NAVFIX já instalada, WheelControl ainda não instalado

```bash
sudo bash wheel-v060/install-v060.sh
sudo bash wheel-v061/install-v061.sh
```

### WheelControl v0.6.0 já instalado

```bash
sudo bash wheel-v061/install-v061.sh
```

### Ainda com a ponte antiga v0.5.6

Ejeta primeiro a unidade USB no leitor. Substitui `/CAMINHO/DA/PONTE` pela pasta real que contém `start_bt_v056.sh` e `live_bt_nbd_v056.py`.

```bash
sudo bash navfix-v058/install-navfix-v058.sh /CAMINHO/DA/PONTE
sudo bash wheel-v060/install-v060.sh
sudo bash wheel-v061/install-v061.sh
```

O instalador NAVFIX verifica o hash da v0.5.6 original. Não serve para a versão comunitária modificada. OverlayFS deve estar desativado para persistir a instalação.

### Se tens WheelControl v0.6.1a

Usa o `rollback-v061a.sh` do pacote v0.6.1a previamente instalado. O instalador v0.6.1 não faz downgrade direto dessa versão. Não reinstales a v0.6.0 por cima.

## Ativar os botões

Os instaladores desligam o modo automático. Testa primeiro os dois comandos manuais e confirma o efeito no telemóvel:

```bash
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py next
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py previous
sudo python3 /opt/blueandme-wheel-v060/wheelctl.py auto-on --confirmed
```

Para observar sem enviar comandos: `sudo python3 /opt/blueandme-wheel-v060/wheelctl.py auto-off`.

## Testar

Com o carro parado, testa áudio, Next e Previous, deixando mais de 9 segundos entre comandos. Confirma que Previous seleciona mesmo o WAV anterior: alguns leitores reiniciam primeiro o WAV atual. Regista o tempo de arranque, reconexão, cortes e comandos inesperados durante os ensaios. Consulta `sudo python3 /opt/blueandme-wheel-v060/wheelctl.py report`.

## Rollback

Reverte apenas os componentes instalados, pela ordem inversa:

```bash
sudo bash wheel-v061/rollback-v061.sh
sudo bash wheel-v060/uninstall-v060.sh
sudo bash navfix-v058/rollback-navfix-v058.sh /CAMINHO/DA/PONTE
```

O primeiro comando regressa ao detetor v0.6.0; o segundo remove o serviço auxiliar; o terceiro restaura a ponte antiga v0.5.6. Não executes os três se apenas queres reverter WheelControl. A reposição requer as cópias criadas pelos instaladores. O modo automático deve ser reativado explicitamente depois de testes.

## Privacidade e compatibilidade

Não inclui logs nem configurações do equipamento do utilizador. O motor NAVFIX original conserva o utilizador de captura predefinido do pacote antigo; configura `BM_CAPTURE_USER` no serviço conforme a tua instalação. Não é um instalador universal para novos Raspberry.

Código MIT, conforme a licença do repositório. Projeto independente e não oficial.
