# Privacidade e publicação de relatórios

Este repositório **não inclui** credenciais de Wi-Fi, endereços IP privados, endereços Bluetooth reais, ficheiros de configuração da máquina, logs de sessões reais, nomes pessoais ou cópias do microSD.

A conta GitHub autora do repositório é publicamente visível por natureza. O nome e o modelo do automóvel de referência são informação técnica de compatibilidade e não contêm matrícula, localização nem número de identificação do veículo.

## Onde ficam os dados em cada instalação

- `/etc/default/blueandme-bt`: opções locais, incluindo o MAC do telemóvel; modo recomendado `0600`.
- `/var/lib/bluetooth`: emparelhamentos do BlueZ, com identificadores dos dispositivos.
- `/run/blueandme`: logs temporários em RAM, que podem incluir endereços MAC e nomes de dispositivos.
- `prefer-phone.txt`: preferência local opcional, excluída do Git pelo `.gitignore`.

**Nunca publiques estes ficheiros nem fotografias com matrículas, endereços, chaves, credenciais ou informação de localização.** Oculta IPs, SSIDs e MACs antes de abrir uma issue.

O instalador não envia diagnósticos ou dados do telemóvel para servidores do projeto. Requer Internet para obter dependências do Raspberry Pi OS e fazer `git clone`.
