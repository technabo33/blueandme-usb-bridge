(() => {
  const button = document.getElementById('copy-install');
  if (!button) return;
  const commands = [
    'sudo apt update',
    'sudo apt install -y git',
    'git clone https://github.com/technabo33/blueandme-usb-bridge.git',
    'cd blueandme-usb-bridge',
    'sudo bash scripts/install.sh',
    'sudo reboot'
  ].join('\n');
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(commands);
      const previous = button.textContent;
      button.textContent = 'Copiado!';
      window.setTimeout(() => { button.textContent = previous; }, 1800);
    } catch (error) {
      button.textContent = 'Seleciona o texto';
      window.setTimeout(() => { button.textContent = 'Copiar'; }, 2200);
    }
  });
})();
