# Como publicar o projeto e a página no GitHub

## 1. Criar um repositório novo

1. No GitHub, cria um repositório **público** com o nome **`blueandme-usb-bridge`**.
2. Se usares esta pasta ZIP como ponto de partida, não cries ficheiros iniciais automáticos no GitHub (`README`, `.gitignore` ou licença), porque já vêm incluídos.
3. Extrai o ZIP do projeto para uma pasta no teu computador.

## 2. Enviar os ficheiros

Na pasta extraída, abre o terminal:

```bash
git init -b main
git add .
git commit -m "Publicar BlueAndMe USB Bluetooth Bridge v0.5.6 community"
git remote add origin https://github.com/technabo33/blueandme-usb-bridge.git
git push -u origin main
```

Se o teu utilizador GitHub for diferente, substitui `technabo33` pelo correto. A autenticação do `git push` é feita pelo GitHub (por exemplo, Git Credential Manager ou SSH); não coloques passwords ou tokens em comandos que partilhes publicamente.

**Alternativa sem terminal:** usa GitHub Desktop → File → Add local repository → Publish repository, escolhendo público.

## 3. Publicar a página visual

No repositório GitHub:

1. **Settings → Pages**.
2. Em **Build and deployment → Source**, escolhe **Deploy from a branch**.
3. Seleciona branch **main**, pasta **/docs**, e carrega em **Save**.
4. Após a publicação, a página terá habitualmente o endereço `https://technabo33.github.io/blueandme-usb-bridge/`.

O site é HTML/CSS/JavaScript estático, sem base de dados, sem Jekyll e sem necessidade de instalar serviços. Se mudares o nome do repositório ou utilizador, atualiza as ligações nas páginas antes de publicares.

## 4. Configurar a apresentação do repositório

**Descrição sugerida:**

> Raspberry Pi Zero W Bluetooth A2DP to read-only USB mass storage bridge for original Blue&Me car audio systems. Open source, FAT32 virtual WAV streaming.

**Topics:** `raspberry-pi`, `bluetooth`, `a2dp`, `bluealsa`, `bluez`, `usb-gadget`, `fat32`, `alfa-romeo`, `blueandme`, `car-audio`, `python`.

**Website:** `https://technabo33.github.io/blueandme-usb-bridge/`.

Podes criar a primeira release na secção **Releases** do GitHub com o identificador `v0.5.6-community.1` e anexar o mesmo ZIP descarregado. Ainda não foi publicada qualquer release por este assistente.

## 5. Antes de tornares o repositório público

Reconfirma que não incluíste imagens `.img`, configuração de Wi-Fi, ficheiros `.env`, `/etc/default/blueandme-bt`, ficheiros de logs, tokens de acesso ou endereços MAC reais. Estes ficheiros **não** fazem parte do pacote preparado.
