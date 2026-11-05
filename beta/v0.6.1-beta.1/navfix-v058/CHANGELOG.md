# NAVFIX v0.5.8 experimental

- Mapas de áudio independentes para WAVs secundários, sem controlar o Spotify.
- Preserva todo o código anterior a `# No audio data are written to the image.` da v0.5.6.
- `blueandme-bt-v056.service` e script de arranque não são modificados.
- Backups e reversão automáticos, com verificação SHA-256 da v0.5.6 original.
- Oito testes locais da função `pread`, simulando saltos, prefetch, rewind, troca de origem e metadados FAT32.
- Pendência: testes com a cache/algoritmo USB do Blue&Me real.
