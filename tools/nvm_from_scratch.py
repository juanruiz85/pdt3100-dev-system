#!/usr/bin/env python3
"""
nvm_from_scratch.py - Crea una imagen NVM desde cero para el Symbol PDT 3100.

Construye un NVM image completo con:
1. Header (80 bytes) - copiado del original
2. Far pointer table (apuntando a nuestros recursos)
3. CONFIG.SYS simple
4. Boot sector "MSI BOOT" con BPB
5. FAT12 filesystem
6. Root directory con entradas de archivos
7. Data area con nuestros archivos

USO:
    python nvm_from_scratch.py program.bin output.hex [runtime.hex]

    program.bin:  código binario 8086 (o .COM sin PSP)
    output.hex:   imagen NVM resultante en Intel HEX
    runtime.hex:  (opcional) runtime.hex original para copiar header y estructura
"""

import sys, struct, os

def parse_ihex(path):
    """Parsea Intel HEX a binario."""
    ext_seg = 0
    segments = {}
    cur_base = None
    cur = bytearray()
    last_addr = None
    
    with open(path, 'r', encoding='latin-1') as f:
        for line in f:
            line = line.rstrip('\r\n\x1a')
            if not line or not line.startswith(':'):
                continue
            raw = bytes.fromhex(line[1:])
            if len(raw) < 5:
                continue
            byte_count = raw[0]
            addr = (raw[1] << 8) | raw[2]
            rtype = raw[3]
            data = raw[4:4+byte_count]
            
            if rtype == 0x00:
                full_addr = (ext_seg << 4) + addr
                if cur_base is None:
                    cur_base = full_addr
                    cur = bytearray(data)
                    last_addr = full_addr + byte_count
                elif full_addr == last_addr:
                    cur.extend(data)
                    last_addr += byte_count
                else:
                    segments[cur_base] = bytes(cur)
                    cur_base = full_addr
                    cur = bytearray(data)
                    last_addr = full_addr + byte_count
            elif rtype == 0x01:
                break
            elif rtype == 0x02:
                if cur_base is not None and cur:
                    segments[cur_base] = bytes(cur)
                    cur = bytearray()
                    cur_base = None
                ext_seg = (data[0] << 8) | data[1]
    
    if cur_base is not None and cur:
        segments[cur_base] = bytes(cur)
    
    if not segments:
        return b'', 0
    min_base = min(segments.keys())
    max_end = max(b + len(d) for b, d in segments.items())
    size = max_end - min_base
    blob = bytearray(size)
    for base, data in segments.items():
        off = base - min_base
        blob[off:off+len(data)] = data
    return bytes(blob), min_base


def build_mz_exe(code):
    """Crea un MZ EXE mínimo que contiene el código dado."""
    hdr_size_para = 2  # 32 bytes header
    hdr_bytes = hdr_size_para * 16
    
    # Padding a múltiplo de 16
    padded_code = bytearray(code)
    while (len(padded_code) + hdr_bytes) % 16 != 0:
        padded_code.append(0x90)  # NOP
    
    total = hdr_bytes + len(padded_code)
    num_blocks = (total + 511) // 512
    last_block = total - (num_blocks - 1) * 512
    if last_block == 512:
        last_block = 0
    
    header = bytearray(32)
    header[0:2] = b'MZ'
    struct.pack_into('<H', header, 2, last_block)
    struct.pack_into('<H', header, 4, num_blocks)
    struct.pack_into('<H', header, 6, 0)      # num_relocs
    struct.pack_into('<H', header, 8, hdr_size_para)
    struct.pack_into('<H', header, 10, 0)    # min_mem
    struct.pack_into('<H', header, 12, 0xFFFF)  # max_mem
    struct.pack_into('<H', header, 14, 0)    # SS
    struct.pack_into('<H', header, 16, 0xFFFE)  # SP
    struct.pack_into('<H', header, 18, 0)    # checksum
    struct.pack_into('<H', header, 20, 0)    # IP = 0
    struct.pack_into('<H', header, 22, 0)    # CS = 0
    struct.pack_into('<H', header, 24, 0x1C) # reloc_offset
    struct.pack_into('<H', header, 26, 0)    # overlay
    
    return bytes(header) + bytes(padded_code)


def build_nvm_image(program_code, runtime_bin=None):
    """Construye una imagen NVM completa desde cero."""
    
    # === Parámetros del filesystem (copiados del original) ===
    BYTES_PER_SECTOR = 512
    SECTORS_PER_CLUSTER = 2
    CLUSTER_SIZE = BYTES_PER_SECTOR * SECTORS_PER_CLUSTER  # 1024 bytes
    RESERVED_SECTORS = 1
    NUM_FATS = 2
    ROOT_ENTRIES = 112
    SECTORS_PER_FAT = 1
    TOTAL_SECTORS = 640  # 320 KB total disk image
    MEDIA_DESCRIPTOR = 0xFF
    
    # === 1. Crear MZ EXE para nuestro programa ===
    print("1. Creando MZ EXE para nuestro programa...")
    hello_exe = build_mz_exe(program_code)
    print(f"   EXE: {len(hello_exe)} bytes")
    
    # === 2. Crear CONFIG.SYS ===
    print("2. Creando CONFIG.SYS...")
    # shell=a:shell.com b:hello.exe
    # Esto le dice a DR-DOS que use shell.com (en ROM, drive A:)
    # para cargar hello.exe (en NVM, drive B:)
    config_sys = b"break = off\r\nfiles = 20\r\nshell = a:shell.com b:hello.exe\r\n"
    config_sys += b"\x1a"  # EOF marker
    # Pad a 256 bytes
    while len(config_sys) < 0x86:  # 0x1C6 - 0x140 = 0x86 = 134 bytes
        config_sys += b'\x00'
    config_sys = config_sys[:0x86]
    print(f"   CONFIG.SYS: {len(config_sys)} bytes")
    print(f"   Contenido: {config_sys[:80]!r}")
    
    # === 3. Calcular offsets de cada componente ===
    # Estructura del NVM image:
    # [0x000-0x04F] Header (80 bytes)
    # [0x050-0x12F] Far pointer table (224 bytes = 56 entries)
    # [0x130-0x13F] Padding (16 bytes)
    # [0x140-0x1C5] CONFIG.SYS (134 bytes)
    # [0x1C6-0x3C5] Boot sector (512 bytes) - incluye BPB + FAT + directorio + data
    # [0x3C6-end]   Más data area (clusters)
    
    HEADER_SIZE = 0x50        # 80 bytes
    FAR_PTR_TABLE_SIZE = 0xE0 # 224 bytes = 56 entries × 4 bytes
    PADDING_SIZE = 0x10      # 16 bytes
    CONFIG_OFFSET = 0x140
    BOOT_SECTOR_OFFSET = 0x1C6
    BOOT_SECTOR_SIZE = 0x200  # 512 bytes
    
    # Dentro del boot sector (relativo a 0x1C6):
    # [0x00-0x23] BPB header (36 bytes)
    # [0x24-0x43] FAT data (32 bytes) - FAT12 entries
    # [0x44-...]  Directory entries + padding
    # [data...]   File data
    
    BPB_OFFSET = 0x00  # dentro del boot sector
    FAT_OFFSET = 0x24  # dentro del boot sector (empieza después del BPB)
    DIR_OFFSET = 0x4A  # dentro del boot sector (después de FAT)
    DATA_OFFSET = 0x200  # Data area empieza después del boot sector (en 0x3C6)
    
    # === 4. Crear header (copiar del original o crear nuevo) ===
    print("3. Creando header...")
    if runtime_bin:
        header = bytearray(runtime_bin[:HEADER_SIZE])
        print(f"   Header copiado del original ({len(header)} bytes)")
    else:
        header = bytearray(HEADER_SIZE)
        print(f"   Header nuevo ({len(header)} bytes)")
    
    # === 5. Crear far pointer table ===
    print("4. Creando far pointer table...")
    far_ptr_table = bytearray(FAR_PTR_TABLE_SIZE)
    
    # Entry [0]: apunta a CONFIG.SYS (offset 0x140 en el binario)
    # seg = 0xB000, off = 0xC2A0 → linear 0xBC2A0 → file_off 0x140
    struct.pack_into('<HH', far_ptr_table, 0*4, 0xC2A0, 0xB000)
    
    # Entry [1]: apunta al boot sector (offset 0x1C6)
    # seg = 0xB000, off = 0xC326 → linear 0xBC326 → file_off 0x1C6
    struct.pack_into('<HH', far_ptr_table, 1*4, 0xC326, 0xB000)
    
    # Entry [2]: apunta al directorio (dentro del boot sector)
    # file_off = 0x1C6 + 0x4A = 0x210
    # seg = 0xB000, off = 0xC210 → linear 0xBC210 → file_off 0xB0... hmm
    # Recalcular: linear = BASE + file_off = 0xBC160 + 0x210 = 0xBC370
    # seg = linear >> 4 = 0xBC37, off = linear & 0xF = 0x0
    # Pero el original usa seg=0xB000, off=0xC2A0 (que da 0xB0000+0xC2A0=0xBC2A0)
    # Entonces: para file_off X, seg=0xB000, off=0xB0000+X-0xBC160+0xB0000
    # Simplificar: off = X + 0xB0000 - 0xBC160 = X + (0xB0000 - 0xBC160) = X - 0xC160
    # Pero 0xC160 > 0xFFFF para X pequeño... el original usa file_off=0x140
    # off = 0x140 + 0xB0000 - 0xBC160 = 0x140 + 0xFFC4A0 = ... no
    # linear = 0xB000 * 16 + off = 0xB0000 + off
    # file_off = linear - 0xBC160 = 0xB0000 + off - 0xBC160 = off - 0xC160
    # Para file_off = 0x140: off = 0x140 + 0xC160 = 0xC2A0 ✓ (dentro de 16 bits!)
    # Para file_off = 0x1C6: off = 0x1C6 + 0xC160 = 0xC326 ✓
    
    BASE = 0xBC160
    def make_far_ptr(file_off):
        """Convierte file_off a (offset, segment=0xB000) far pointer."""
        off = (file_off + 0xC160) & 0xFFFF
        return off, 0xB000
    
    # Entry [0]: CONFIG.SYS @ file_off 0x140
    off, seg = make_far_ptr(0x140)
    struct.pack_into('<HH', far_ptr_table, 0*4, off, seg)
    
    # Entry [1]: Boot sector @ file_off 0x1C6
    off, seg = make_far_ptr(0x1C6)
    struct.pack_into('<HH', far_ptr_table, 1*4, off, seg)
    
    # Entry [2]: Directory entries @ file_off 0x1C6 + 0x4A = 0x210
    off, seg = make_far_ptr(0x210)
    struct.pack_into('<HH', far_ptr_table, 2*4, off, seg)
    
    # Entry [3]: Data area start @ file_off 0x3C6
    off, seg = make_far_ptr(0x3C6)
    struct.pack_into('<HH', far_ptr_table, 3*4, off, seg)
    
    print(f"   Far pointer table: {len(far_ptr_table)} bytes ({len(far_ptr_table)//4} entries)")
    for i in range(4):
        off, seg = struct.unpack('<HH', far_ptr_table[i*4:i*4+4])
        lin = seg * 16 + off
        foff = lin - BASE
        print(f"   [{i}] off=0x{off:04X} seg=0x{seg:04X} → file_off=0x{foff:04X}")
    
    # === 6. Padding ===
    padding = bytearray(PADDING_SIZE)
    
    # === 7. Crear boot sector con BPB ===
    print("5. Creando boot sector...")
    boot_sector = bytearray(BOOT_SECTOR_SIZE)
    
    # BPB header (36 bytes)
    boot_sector[0:3] = b'\x00\x00\x00'  # jump (NOP)
    boot_sector[3:11] = b'MSI BOOT\x00'  # OEM name
    struct.pack_into('<H', boot_sector, 0x0B, BYTES_PER_SECTOR)  # bytes/sector
    boot_sector[0x0D] = SECTORS_PER_CLUSTER
    struct.pack_into('<H', boot_sector, 0x0E, RESERVED_SECTORS)
    boot_sector[0x10] = NUM_FATS
    struct.pack_into('<H', boot_sector, 0x11, ROOT_ENTRIES)
    struct.pack_into('<H', boot_sector, 0x13, TOTAL_SECTORS)
    boot_sector[0x15] = MEDIA_DESCRIPTOR
    struct.pack_into('<H', boot_sector, 0x16, SECTORS_PER_FAT)
    struct.pack_into('<H', boot_sector, 0x18, 8)  # sectors/track
    struct.pack_into('<H', boot_sector, 0x1A, 2)  # heads
    struct.pack_into('<I', boot_sector, 0x1C, 0)  # hidden sectors
    
    print(f"   BPB: {boot_sector[:36].hex()}")
    
    # === 8. Crear FAT12 ===
    print("6. Creando FAT12...")
    fat = bytearray(BOOT_SECTOR_SIZE - 0x24)  # FAT data dentro del boot sector
    
    # FAT12 entries:
    # [0] = media descriptor + 0xFF (2 bytes en FAT12 = 0xFF8 + media)
    # [1] = end of chain marker (0xFFF)
    # [2] = end of chain (nuestro archivo usa 1 cluster)
    
    # FAT12 encoding: cada entrada es 1.5 bytes
    # entry[0] = 0xFF (media byte high), entry[1] = 0xFF
    # Para FAT12: entry[0] y entry[1] forman los primeros 3 bytes
    # byte[0] = entry[0] & 0xFF
    # byte[1] = ((entry[0] >> 8) & 0x0F) | ((entry[1] & 0x0F) << 4)  
    # byte[2] = (entry[1] >> 4) & 0xFF
    
    # entry[0] = 0xFF8 (media), entry[1] = 0xFFF (reserved)
    fat[0] = 0xF8  # entry[0] low
    fat[1] = 0xFF  # entry[0] high + entry[1] low
    fat[2] = 0xFF  # entry[1] high
    
    # entry[2] = 0xFFF (end of chain - nuestro archivo usa cluster 2)
    fat[3] = 0xFF  # entry[2] (odd) = (byte[2]>>4) | (byte[3]<<4) = 0xF | 0xF0 = 0xFF... 
    # Actually FAT12:
    # entry[2] (even): byte[3] | ((byte[4] & 0x0F) << 8)
    fat[3] = 0xFF  # entry[2] low byte
    fat[4] = 0x0F  # entry[2] high nibble = 0xF (so entry[2] = 0xFFF)
    
    # Copy FAT into boot sector
    boot_sector[0x24:0x24+len(fat)] = fat[:BOOT_SECTOR_SIZE - 0x24]
    
    print(f"   FAT: {fat[:8].hex()}")
    
    # === 9. Crear directory entries ===
    print("7. Creando directory entries...")
    dir_offset_in_boot = 0x4A  # offset dentro del boot sector
    
    # Crear entrada para HELLO.EXE
    dir_entry = bytearray(32)
    # Nombre: HELLO    (8 chars padded with spaces)
    dir_entry[0:8] = b'HELLO   '
    # Extension: EXE
    dir_entry[8:11] = b'EXE'
    # Attribute: normal file (0x00)
    dir_entry[11] = 0x00
    # Reserved, time, date (zeros)
    dir_entry[12:26] = b'\x00' * 14
    # Cluster: 2 (primer cluster de datos)
    struct.pack_into('<H', dir_entry, 26, 2)
    # Size: tamaño del EXE
    struct.pack_into('<I', dir_entry, 28, len(hello_exe))
    
    # Colocar entrada en el boot sector
    boot_sector[dir_offset_in_boot:dir_offset_in_boot+32] = dir_entry
    
    # Marcar fin de directorio (siguiente entrada = 0x00)
    boot_sector[dir_offset_in_boot+32] = 0x00
    
    print(f"   Directory entry: {dir_entry.hex()}")
    print(f"   File: HELLO.EXE, cluster=2, size={len(hello_exe)}B")
    
    # === 10. Crear data area ===
    print("8. Creando data area...")
    # El data area empieza después del boot sector (file_off 0x3C6)
    # Nuestro archivo va en cluster 2 (que es el primer cluster de datos)
    # Cluster 2 está en file_off = DATA_START + (2-2) * CLUSTER_SIZE = 0x3C6
    
    # El EXE ocupa len(hello_exe) bytes, padding a cluster size
    exe_padded = bytearray(hello_exe)
    while len(exe_padded) < CLUSTER_SIZE:
        exe_padded.append(0x00)
    
    data_area = bytes(exe_padded)
    print(f"   Data area: {len(data_area)} bytes (cluster 2)")
    
    # === 11. Ensamblar imagen NVM completa ===
    print("9. Ensamblando imagen NVM...")
    nvm_image = bytearray()
    nvm_image += header
    nvm_image += far_ptr_table
    nvm_image += padding
    nvm_image += config_sys
    nvm_image += boot_sector
    nvm_image += data_area
    
    # Padding final a TOTAL_SECTORS * BYTES_PER_SECTOR (327680 bytes = 320KB)
    # Pero el runtime.hex original tiene 147104 bytes (no llega a 320KB)
    # Vamos a padding al tamaño del original
    if runtime_bin:
        target_size = len(runtime_bin)
    else:
        target_size = 147104  # mismo tamaño que runtime.hex original
    
    while len(nvm_image) < target_size:
        nvm_image += b'\xFF'  # padding con 0xFF (flash borrado)
    
    nvm_image = nvm_image[:target_size]
    
    print(f"   NVM image: {len(nvm_image)} bytes ({len(nvm_image)/1024:.1f} KB)")
    print(f"   Estructura:")
    print(f"     [0x000-0x04F] Header ({HEADER_SIZE}B)")
    print(f"     [0x050-0x12F] Far ptr table ({FAR_PTR_TABLE_SIZE}B)")
    print(f"     [0x130-0x13F] Padding ({PADDING_SIZE}B)")
    print(f"     [0x140-0x1C5] CONFIG.SYS ({len(config_sys)}B)")
    print(f"     [0x1C6-0x3C5] Boot sector ({BOOT_SECTOR_SIZE}B)")
    print(f"     [0x3C6-...]   Data area ({len(data_area)}B)")
    print(f"     [padding]     0xFF fill to {target_size}B")
    
    return bytes(nvm_image)


def checksum(data_bytes):
    return (-sum(data_bytes)) & 0xFF

def data_record(offset, data):
    bc = len(data)
    body = bytes([bc, (offset>>8)&0xFF, offset&0xFF, 0x00]) + data
    cs = checksum(body)
    return ":" + (body + bytes([cs])).hex().upper()

def esa_record(segment):
    body = bytes([0x02, 0x00, 0x00, 0x02, (segment>>8)&0xFF, segment&0xFF])
    cs = checksum(body)
    return ":" + (body + bytes([cs])).hex().upper()

def bin_to_ihex(blob, base_addr, line_len=0x10):
    lines = []
    seg_step = 0x40
    bytes_per_seg = 0x400
    
    first_seg_size = (bytes_per_seg - (base_addr % bytes_per_seg)) % bytes_per_seg
    first_seg_size = min(first_seg_size if first_seg_size > 0 else bytes_per_seg, len(blob))
    
    cur_seg = (base_addr >> 4) & 0xFFFF
    pos = 0
    total_size = len(blob)
    
    lines.append(esa_record(cur_seg))
    block_end = min(pos + first_seg_size, total_size)
    block_offset = 0
    while pos < block_end:
        chunk_size = min(line_len, block_end - pos)
        lines.append(data_record(block_offset, blob[pos:pos+chunk_size]))
        pos += chunk_size
        block_offset += chunk_size
    cur_seg += first_seg_size // 16
    
    while pos < total_size:
        lines.append(esa_record(cur_seg))
        block_end = min(pos + bytes_per_seg, total_size)
        block_offset = 0
        while pos < block_end:
            chunk_size = min(line_len, block_end - pos)
            lines.append(data_record(block_offset, blob[pos:pos+chunk_size]))
            pos += chunk_size
            block_offset += chunk_size
        cur_seg += seg_step
    
    lines.append(":00000001FF")
    return "\r\n".join(lines) + "\r\n\x1a"


def main():
    if len(sys.argv) < 3:
        print("Uso: python nvm_from_scratch.py program.bin output.hex [runtime.hex]")
        sys.exit(1)
    
    program_path = sys.argv[1]
    output_path = sys.argv[2]
    runtime_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"=== NVM Builder desde cero ===")
    print(f"Programa: {program_path}")
    print(f"Output: {output_path}")
    if runtime_path:
        print(f"Base (header): {runtime_path}")
    print()
    
    # Leer programa
    program_code = open(program_path, 'rb').read()
    print(f"Programa: {len(program_code)} bytes")
    
    # Leer runtime.hex original (para copiar header)
    runtime_bin = None
    if runtime_path:
        print(f"Parseando {runtime_path}...")
        runtime_bin, base_addr = parse_ihex(runtime_path)
        print(f"  Base: {len(runtime_bin)} bytes, addr 0x{base_addr:06X}")
    
    # Construir NVM
    base_addr = 0xBC160  # dirección base del NVM
    nvm_bin = build_nvm_image(program_code, runtime_bin)
    
    # Convertir a Intel HEX
    print()
    print("Generando Intel HEX...")
    hex_text = bin_to_ihex(nvm_bin, base_addr)
    
    with open(output_path, 'w', encoding='latin-1') as f:
        f.write(hex_text)
    
    hex_size = os.path.getsize(output_path)
    print(f"HEX: {output_path} ({hex_size:,} bytes, {hex_text.count(chr(13))} líneas)")
    print()
    print("=== Listo para cargar ===")
    print(f"1. Boot to Command Mode (F+I+PWR)")
    print(f"2. Program Loader")
    print(f"3. 19200 baud, 7 data, Odd parity, Xon/Xoff")
    print(f"4. sendhex {os.path.splitext(os.path.basename(output_path))[0]} 19200 2")
    print(f"5. Status 0000")
    print(f"6. Cold Boot (A+B+D+PWR)")

if __name__ == "__main__":
    main()
