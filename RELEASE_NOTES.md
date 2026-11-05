# Primeira release pública: v0.5.6-community.1

**Blue&Me USB Bluetooth Bridge** disponibiliza música Bluetooth A2DP pela entrada USB original, usando uma FAT32 virtual apenas de leitura e streaming PCM em RAM.

### Conteúdo
- Motor Python/BlueALSA v0.5.6 com reconexão FASTPATH e FASTPCM.
- 48 ficheiros WAV virtuais de 30 minutos cada (24 horas por defeito).
- Servidor nbdkit e USB gadget de armazenamento read-only.
- Instalador Raspberry Pi OS Lite 32-bit e configuração manual segura do emparelhamento.
- OverlayFS documentado para proteção do microSD.
- Site GitHub Pages e documentação PT-PT/English.

### Validação
- **Motor e arquitetura:** testados num Raspberry Pi Zero W com Alfa Romeo MiTo 2010 Blue&Me.
- **Instalador novo:** validado por sintaxe e testes locais, não testado ainda num cartão limpo e num segundo veículo.
- **Compatibilidade:** nenhuma garantia para outros modelos/radios/BlueALSA 5.x.

### Instalação
Ver [INSTALL.pt-PT.md](INSTALL.pt-PT.md). Faz backup do cartão antes de experimentar.
