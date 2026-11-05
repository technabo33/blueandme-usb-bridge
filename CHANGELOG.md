# Histórico de versões

## v0.5.6 community.1 (pacote público inicial)
- Mesma arquitetura de streaming da v0.5.6 validada no MiTo.
- Removidas referências específicas ao utilizador e endereço Bluetooth do sistema de referência.
- Instalação com geração automática da FAT32 *sparse* e seleção de utilizador/telemóvel.
- Documentação PT-PT, English README, testes automáticos e site GitHub Pages.
- Sem confirmação ainda de instalação limpa no hardware de terceiros.

## v0.5.6 (base privada de testes)
- Reduzida validação FAT32 duplicada no arranque.
- Adicionadas medições NBD/USB e mantido o FASTPCM.

## v0.5.5
- FASTPCM: iniciar captura A2DP assim que o PCM BlueALSA fica pronto.

## v0.5.4
- FASTPATH prioritário para telemóvel autorizado.

## v0.5.3
- Prioridade de ligação ao perfil A2DP Source, com alternativa genérica.

## v0.5.0 a v0.5.2
- FAT32 virtual com 48 WAV de 30 min e supervisão de serviços.

## Nota

As designações das versões anteriores descrevem iterações do protótipo. Só a edição comunitária está preparada para publicação nesta estrutura.

- Documentação comunitária: guia rápido a partir de microSD novo, política de privacidade e proteção das configurações locais (0600).
