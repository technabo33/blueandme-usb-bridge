# Blue&Me USB Bluetooth Bridge (English)

An independent, open-source prototype that turns a **Raspberry Pi Zero W** into a **read-only FAT32 USB mass-storage device**, while feeding its virtual WAV tracks with live audio received over Bluetooth A2DP.

**Tested core:** Raspberry Pi Zero W + original 2010 Alfa Romeo MiTo Blue&Me. The new general-purpose installation scripts have been syntax/unit-tested but **not yet confirmed on a clean SD card**.

## Why it exists

Some older car infotainment systems can play WAV files from USB flash drives but cannot receive modern Bluetooth music over the original USB interface. A generic USB Bluetooth adapter is not understood as music storage.

## How it works

```text
Android phone / music app → Bluetooth A2DP → Pi Zero W
            → BlueALSA → PCM ring buffer (RAM)
            → sparse FAT32 with 48 virtual WAV tracks
            → nbdkit + nbd-client + USB mass storage gadget
            → original USB port → Blue&Me radio
```

The USB disk is exposed as **read-only**. Audio is streamed, not recorded to the SD card. A 24-hour library is **16 GiB logical**, but the sparse image occupies far less real disk space.

## Quick start

1. Install Raspberry Pi OS Lite **32-bit**, Wi-Fi and SSH on a fresh SD card.
2. Connect the Pi via Wi-Fi SSH. Use the Pi Zero's **USB data port**, not PWR IN, for the car/computer.
3. Install:

```bash
sudo apt update
sudo apt install -y git
git clone https://github.com/technabo33/blueandme-usb-bridge.git
cd blueandme-usb-bridge
sudo bash scripts/install.sh
sudo reboot
```

4. Stop the bridge (`sudo systemctl stop blueandme-bt-v056.service`), run `sudo bluetoothctl`, enable `agent on`, `default-agent`, `pairable on`, `discoverable on`, then pair the phone from its Bluetooth settings. Verify `Paired: yes` and `Trusted: yes`; execute `trust AA:BB:CC:DD:EE:FF` if required. Turn discoverable/pairable off again.
5. Configure your own paired/trusted phone: `sudo bash scripts/set-phone.sh AA:BB:CC:DD:EE:FF` and start the service.
6. Confirm the virtual USB drive is detected, then connect to the car's original USB port. On the car, select USB media and play one of the virtual WAV tracks.
7. After validation, enable Raspberry Pi OS **Overlay File System + write-protect boot partition** using `sudo raspi-config`.

More detail (Portuguese): [INSTALL.pt-PT.md](INSTALL.pt-PT.md). Diagnostics: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Limitations

Radio FAT32/WAV USB support is necessary and not sufficient. Read-ahead/caching can add silence. Automatic A2DP reconnect varies by phone and OS. Steering-wheel controls, track metadata and universal compatibility are **not implemented**. No mobile apps, music, ROMs or firmware blobs are bundled.

**Not an official Alfa Romeo/Fiat/Stellantis/Microsoft/Spotify project.** Code licensed under MIT.
