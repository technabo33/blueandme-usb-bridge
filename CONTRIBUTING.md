# Como contribuir

Obrigado por ajudares a melhorar a compatibilidade de carros antigos com música Bluetooth.

1. Abre um issue com modelo e ano do carro, versão de Blue&Me (se souberes), Raspberry, sistema operativo, resultado e passos para reproduzir.
2. Não divulgues dados pessoais: oculta MAC, IP, SSID, tokens, nomes de utilizador ou fotografias identificáveis.
3. Antes de enviar um pull request, executa:

```bash
python3 -m py_compile app/*.py
bash -n app/*.sh scripts/*.sh
python3 -m unittest discover -s tests -v
```

4. Mantém a imagem FAT32 apenas de leitura e preserva os mecanismos de verificação `Paired + Trusted`.
5. Para mudanças que afetem o gadget USB, prepara um plano de rollback; o sistema tem de continuar recuperável através de SSH ou microSD.

## Tipos de ajuda mais úteis

- Resultados de compatibilidade por modelo de rádio (sem dados privados).
- Correções ao instalador para diferentes imagens Raspberry Pi OS.
- Testes de reconexão A2DP após cortes de energia.
- Documentação e traduções para outras línguas.
- Medições de latência com cronómetros e logs do mesmo arranque.

### Código de conduta

Participa com respeito. Discussões técnicas e críticas construtivas são bem-vindas; assédio, divulgação de dados pessoais ou instruções de uso perigoso do hardware não são aceites.
