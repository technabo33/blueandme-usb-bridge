#!/usr/bin/env python3
"""Sparse FAT32 read-only virtual USB for long Blue&Me WAV playlist.

One track every 30 minutes. Default 48 tracks = 24 hours; optional 1..48 hours.
Logical image is sized automatically (4/8/16/32 GiB); real space on ext4
is small because all PCM payloads are holes, overlaid by the NBD plugin.
Creates static metadata and never edits a volume exposed over USB.
"""
import argparse
import math
import os
import struct
from pathlib import Path

SECTOR = 512
SPC = 64  # 32 KiB clusters
CLUSTER_BYTES = SECTOR * SPC
RESERVED = 32
NFATS = 2
RATE = 44100
BPS = RATE * 4
TRACK_SECONDS = 1800
TRACK_SIZE = TRACK_SECONDS * BPS + 44
FILE_CLUSTERS = (TRACK_SIZE + CLUSTER_BYTES - 1) // CLUSTER_BYTES
LABEL = b'BMSTREAM   '
PLAYLIST_SHORT = b'LISTA   M3U'


def track_name(index):
    return f'FLX{index:05d}.WAV'


def shortname(index):
    return f'FLX{index:05d}'.encode() + b'WAV'


def playlist_data(tracks):
    return ('#EXTM3U\r\n' + ''.join(track_name(i) + '\r\n' for i in range(1, tracks + 1))).encode('ascii')


def wav_header():
    count = TRACK_SECONDS * BPS
    return (b'RIFF' + struct.pack('<I', count + 36) + b'WAVEfmt ' +
            struct.pack('<IHHIIHH', 16, 1, 2, RATE, BPS, 4, 16) +
            b'data' + struct.pack('<I', count))


def geometry(tracks):
    # Minimum capacity + margin; power-of-two GiB is accepted by Windows.
    required = (3 + FILE_CLUSTERS * tracks + 128) * CLUSTER_BYTES
    gib = 4
    while gib * 1024**3 < required * 1.03:
        gib *= 2
    if gib > 32:
        raise ValueError('Mais de 32 GiB logicos; reduz o numero de horas')
    total = gib * 1024**3 // SECTOR
    spf = 1
    while True:
        data_clusters = (total - RESERVED - NFATS * spf) // SPC
        needed = math.ceil((data_clusters + 2) * 4 / SECTOR)
        if needed == spf:
            break
        spf = needed
    count = (total - RESERVED - NFATS * spf) // SPC
    if not (65525 <= count < 0x0ffffff5):
        raise ValueError('Numero de clusters FAT32 invalido')
    if 3 + FILE_CLUSTERS * tracks >= count:
        raise ValueError('Falta espaco na imagem')
    return total, spf, count, gib


def boot_sector(total, spf, tracks):
    boot = bytearray(SECTOR)
    boot[:3] = b'\xeb\x58\x90'
    boot[3:11] = b'MSDOS5.0'
    struct.pack_into('<H', boot, 11, SECTOR)
    boot[13] = SPC
    struct.pack_into('<H', boot, 14, RESERVED)
    boot[16] = NFATS
    struct.pack_into('<H', boot, 17, 0)
    struct.pack_into('<H', boot, 19, 0)
    boot[21] = 0xf8
    struct.pack_into('<H', boot, 22, 0)
    struct.pack_into('<H', boot, 24, 63)
    struct.pack_into('<H', boot, 26, 255)
    struct.pack_into('<I', boot, 28, 0)
    struct.pack_into('<I', boot, 32, total)
    struct.pack_into('<I', boot, 36, spf)
    struct.pack_into('<H', boot, 40, 0)
    struct.pack_into('<H', boot, 42, 0)
    struct.pack_into('<I', boot, 44, 2)
    struct.pack_into('<H', boot, 48, 1)  # FSInfo
    struct.pack_into('<H', boot, 50, 6)  # backup boot
    boot[64] = 0x80
    boot[66] = 0x29
    struct.pack_into('<I', boot, 67, 0x20265000 + tracks)
    boot[71:82] = LABEL
    boot[82:90] = b'FAT32   '
    boot[510:512] = b'\x55\xaa'
    return bytes(boot)


def fsinfo_sector():
    b = bytearray(SECTOR)
    struct.pack_into('<I', b, 0, 0x41615252)
    struct.pack_into('<I', b, 484, 0x61417272)
    struct.pack_into('<I', b, 488, 0xffffffff)  # unknown free clusters
    struct.pack_into('<I', b, 492, 0xffffffff)
    struct.pack_into('<I', b, 508, 0xaa550000)
    return bytes(b)


def _read_layout(file):
    first = file.read(SECTOR)
    if len(first) != SECTOR or first[-2:] != b'\x55\xaa':
        raise ValueError('Boot sector FAT32 invalido')
    bps = struct.unpack_from('<H', first, 11)[0]
    spc = first[13]
    rsvd = struct.unpack_from('<H', first, 14)[0]
    fats = first[16]
    spf = struct.unpack_from('<I', first, 36)[0]
    root = struct.unpack_from('<I', first, 44)[0]
    tot = struct.unpack_from('<I', first, 32)[0]
    if (bps, spc, rsvd, fats, root) != (SECTOR, SPC, RESERVED, NFATS, 2):
        raise ValueError('Geometria FAT32 inesperada')
    if tot * SECTOR != os.fstat(file.fileno()).st_size:
        raise ValueError('Tamanho da imagem nao coincide com o boot sector')
    return spf, (rsvd + fats * spf) * SECTOR


def image_regions(image):
    """Validate volume and return [(filename, pcm_from, pcm_to), ...]."""
    with open(image, 'rb') as f:
        spf, data_start = _read_layout(f)
        f.seek(data_start)
        root = f.read(CLUSTER_BYTES)
        if root[:11] != LABEL or root[11] != 8:
            raise ValueError('Volume label inesperado')
        regions = []
        index = 1
        while index <= 96:
            entry = root[index * 32:(index + 1) * 32]
            if entry[0] == 0 or entry[0:11] == PLAYLIST_SHORT:
                break
            if entry[0:11] != shortname(index) or entry[11] != 0x20:
                raise ValueError(f'Ficheiro FAT32 inesperado: #{index}')
            cluster = ((struct.unpack_from('<H', entry, 20)[0] << 16) |
                       struct.unpack_from('<H', entry, 26)[0])
            size = struct.unpack_from('<I', entry, 28)[0]
            if size != TRACK_SIZE or cluster != 3 + (index - 1) * FILE_CLUSTERS:
                raise ValueError(f'Cluster ou tamanho invalido: {track_name(index)}')
            start = data_start + (cluster - 2) * CLUSTER_BYTES
            f.seek(start)
            if f.read(44) != wav_header():
                raise ValueError(f'Cabecalho WAV invalido: {track_name(index)}')
            regions.append((track_name(index), start + 44, start + TRACK_SIZE))
            index += 1
        if not regions:
            raise ValueError('Sem faixas')
        if 3 + FILE_CLUSTERS * len(regions) > (os.path.getsize(image) - data_start) // CLUSTER_BYTES:
            raise ValueError('Faixas excedem o volume')
        entry = root[(len(regions) + 1) * 32:(len(regions) + 2) * 32]
        if entry[0:11] != PLAYLIST_SHORT or entry[11] != 0x20:
            raise ValueError('LISTA.M3U em falta')
        playlist_cluster = (struct.unpack_from('<H', entry, 20)[0] << 16) | struct.unpack_from('<H', entry, 26)[0]
        playlist_size = struct.unpack_from('<I', entry, 28)[0]
        expected_playlist = playlist_data(len(regions))
        if (playlist_cluster != 3 + FILE_CLUSTERS * len(regions) or
                playlist_size != len(expected_playlist)):
            raise ValueError('LISTA.M3U: cluster ou tamanho incorretos')
        f.seek(data_start + (playlist_cluster - 2) * CLUSTER_BYTES)
        if f.read(playlist_size) != expected_playlist:
            raise ValueError('LISTA.M3U: texto invalido')
        return regions


def create_image(path, hours):
    if hours < 1 or hours > 48 or hours != int(hours):
        raise ValueError('Usa entre 1 e 48 horas inteiras')
    tracks = hours * 2
    total, spf, count, gib = geometry(tracks)
    image = Path(path)
    if image.exists():
        raise FileExistsError(f'Imagem ja existe, nao alterada: {image}')
    fat = bytearray(spf * SECTOR)
    struct.pack_into('<III', fat, 0, 0x0ffffff8, 0xffffffff, 0x0fffffff)
    for index in range(tracks):
        first = 3 + index * FILE_CLUSTERS
        last = first + FILE_CLUSTERS - 1
        for cluster in range(first, last):
            struct.pack_into('<I', fat, cluster * 4, cluster + 1)
        struct.pack_into('<I', fat, last * 4, 0x0fffffff)
    # A playlist is a real file in the static FAT, not dynamically generated.
    pl_cluster = 3 + tracks * FILE_CLUSTERS
    struct.pack_into('<I', fat, pl_cluster * 4, 0x0fffffff)
    pl_data = playlist_data(tracks)
    if len(pl_data) > CLUSTER_BYTES:
        raise ValueError('LISTA.M3U demasiado grande')
    root = bytearray(CLUSTER_BYTES)
    root[:11] = LABEL
    root[11] = 0x08
    fatdate = ((2026 - 1980) << 9) | (11 << 5) | 5
    for index in range(1, tracks + 1):
        off = index * 32
        first = 3 + (index - 1) * FILE_CLUSTERS
        root[off:off + 11] = shortname(index)
        root[off + 11] = 0x20
        struct.pack_into('<H', root, off + 20, first >> 16)
        struct.pack_into('<H', root, off + 24, fatdate)
        struct.pack_into('<H', root, off + 26, first & 0xffff)
        struct.pack_into('<I', root, off + 28, TRACK_SIZE)
    pl_entry = (tracks + 1) * 32
    root[pl_entry:pl_entry + 11] = PLAYLIST_SHORT
    root[pl_entry + 11] = 0x20
    struct.pack_into('<H', root, pl_entry + 20, pl_cluster >> 16)
    struct.pack_into('<H', root, pl_entry + 24, fatdate)
    struct.pack_into('<H', root, pl_entry + 26, pl_cluster & 0xffff)
    struct.pack_into('<I', root, pl_entry + 28, len(pl_data))
    data_start = (RESERVED + NFATS * spf) * SECTOR
    try:
        with image.open('xb') as f:
            f.truncate(total * SECTOR)
            boot = boot_sector(total, spf, tracks)
            fsinfo = fsinfo_sector()
            f.seek(0); f.write(boot)
            f.seek(SECTOR); f.write(fsinfo)
            f.seek(6 * SECTOR); f.write(boot)
            f.seek(7 * SECTOR); f.write(fsinfo)
            f.seek(RESERVED * SECTOR); f.write(fat)
            f.write(fat)
            f.seek(data_start); f.write(root)
            header = wav_header()
            for index in range(tracks):
                cluster = 3 + index * FILE_CLUSTERS
                f.seek(data_start + (cluster - 2) * CLUSTER_BYTES)
                f.write(header)
            f.seek(data_start + (pl_cluster - 2) * CLUSTER_BYTES)
            f.write(pl_data)
            f.flush(); os.fsync(f.fileno())
        checked = image_regions(image)
        if len(checked) != tracks:
            raise ValueError('Numero de faixas nao validado')
    except Exception:
        try: image.unlink()
        except OSError: pass
        raise
    print(f'FAT32 pronta: {image} | {hours}h | {tracks} WAV consecutivos de 30min')
    print(f'Tamanho apresentado ao USB: {gib} GiB (imagem sparse)')
    print('Playlist estatica: LISTA.M3U (ordem FLX00001 a ultima)')
    print(f'Espaco real usado: {image.stat().st_blocks * 512 / 1024**2:.1f} MiB')
    print('NOTA: a reproducao tem o limite configurado e depende do comportamento do leitor.')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('image')
    p.add_argument('--hours', type=int, default=24, help='1..48 horas, por defeito 24')
    args = p.parse_args()
    create_image(args.image, args.hours)
