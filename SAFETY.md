# Proteção do microSD, eletricidade e privacidade

## OverlayFS para automóveis

A ignição pode cortar a energia subitamente. A configuração recomendada é iniciar com o sistema raiz em **OverlayFS** e a partição de arranque em modo **apenas de leitura**. As alterações temporárias vão para RAM, reduzindo escritas persistentes e o risco de corrupção do sistema. Isto **não elimina** o risco de falhas de alimentação, corrupção já existente ou defeitos físicos do cartão.

Ativa apenas depois de concluir a instalação e emparelhamento:

```bash
sudo raspi-config
# Performance Options -> Overlay File System -> Yes
# Write-protect boot partition -> Yes
sudo reboot
findmnt -n -o FSTYPE /
```

## Alimentação e segurança

Usa uma fonte estável de **5 V** e um cabo USB com ligação de dados correta. Evita instalações com cablagem exposta, ligações improvisadas aos circuitos do automóvel ou alterações no sistema elétrico do carro. Não configures dispositivos nem testes o sistema enquanto conduzes.

## Salvaguarda da instalação

Antes de ativar OverlayFS, conserva uma cópia do cartão ou dos ficheiros de configuração. Para atualizar o projeto, desativa OverlayFS, reinicia, instala, testa, e volta a ativá-lo. O serviço guarda os seus logs temporários em `/run/blueandme`.

## Privacidade dos contributos

Nunca publiques `/etc/default/blueandme-bt`, `prefer-phone.txt`, registos completos de emparelhamento, palavras-passe, ficheiros de rede, tokens, IPs domésticos ou endereços MAC de telemóveis.

## Estado de compatibilidade

Funcional no conjunto Pi Zero W + Blue&Me de um MiTo 2010 testado. Não existem garantias sobre versões diferentes do Blue&Me, outros modelos de automóvel, alteração de faixas por comandos do volante ou restauro automático da reprodução de aplicações móveis.

Para privacidade na publicação de diagnósticos, consulta [PRIVACY.md](PRIVACY.md).
