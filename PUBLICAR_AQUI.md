# Publicar este projeto no GitHub (passo a passo)

O projeto é independente da instalação já funcional no Raspberry. **Não coloques no GitHub nenhuma cópia do cartão microSD, registos reais, dados Bluetooth nem configurações de Wi-Fi.** Publica apenas os ficheiros desta pasta.

## Opção A: através do navegador (sem Git)

1. Entra em `https://github.com/technabo33/blueandme-usb-bridge`.
2. Se o repositório estiver vazio, clica em **uploading an existing file**. Se já tiver ficheiros, usa **Add file → Upload files**.
3. Extrai o ZIP `BlueAndMe_GitHub_Publicacao_Segura_v056.zip` no PC.
4. Abre a pasta extraída `blueandme-usb-bridge` e **envia o conteúdo dessa pasta**, não a pasta exterior nem o ZIP em si. Garante que as subpastas `app`, `scripts`, `systemd`, `docs`, `tests` e `.github` ficam preservadas.
5. No fundo da página, escreve a mensagem `Publicar Blue&Me Bridge v0.5.6 Community` e seleciona **Commit changes**.
6. Abre o separador **Code** do repositório e verifica que o README, as subpastas e os scripts apareceram.

> No Windows, algumas pastas com um ponto inicial, como `.github`, podem estar ocultas. Ativa a apresentação de ficheiros ocultos ou usa a opção B para garantir que são incluídas.

## Opção B: Git no computador

Instala Git for Windows, abre PowerShell na pasta `blueandme-usb-bridge` extraída e executa:

```powershell
git init -b main
git add .
git status --short
git commit -m "Publicar Blue&Me Bridge v0.5.6 Community"
git remote add origin https://github.com/technabo33/blueandme-usb-bridge.git
git push -u origin main
```

Autentica-te pelo mecanismo normal do GitHub/Git Credential Manager quando solicitado. Nunca coloques um token ou palavra-passe em comandos partilhados.

## Ativar o website

1. No repositório GitHub, abre **Settings → Pages**.
2. Em **Build and deployment**, escolhe **Deploy from a branch**.
3. Seleciona `main` e `/docs` e guarda.
4. Confirma a publicação no separador Pages. O endereço previsto é `https://technabo33.github.io/blueandme-usb-bridge/`.

## Verificações antes de divulgar

- `README.md` e `QUICKSTART.pt-PT.md` devem aparecer na raiz.
- A página `docs/index.html` deve existir.
- A pasta `.github/workflows/test.yml` deve aparecer.
- Não publiques os ficheiros do Raspberry em `/etc/default`, `/var/lib/bluetooth` ou `/run/blueandme`.
- O instalador comunitário ainda tem de ser testado de ponta a ponta num microSD novo.
