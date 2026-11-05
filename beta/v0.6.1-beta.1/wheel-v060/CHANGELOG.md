# v0.6.0 Beta (experiência isolada de comandos do volante)

- Processo auxiliar systemd, sem alterações ao motor NAVFIX v0.5.8.
- Integração com BlueZ `org.bluez.MediaPlayer1` Next/Previous.
- Escolha de player previamente emparelhado, trusted e ligado.
- Deteção conservadora a partir de eventos `STATUS` de WAV reproduzido.
- Registos anonimizados persistentes para testes sem SSH no carro.
- Modo automático explicitamente opt-in, desligado por defeito.
- Instalação e desinstalação independentes da ponte principal.

Limitações: a deteção de botões é indireta, via leituras da pen USB virtual, e precisa de validação no carro.
