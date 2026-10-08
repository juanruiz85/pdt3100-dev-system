#!/usr/bin/env python3
"""
exe2hex.py - Convierte un .EXE de 16-bit a formato Intel HEX
para carga en el Symbol PDT 3100 via SENDHEX.

El PDT 3100 espera archivos Intel HEX con:
- Registros ESA (type 02) cada 1024 bytes
- Primer segmento con tamaño especial para alinear a 0x400
- Line endings CRLF (DOS estricto)
- Ctrl-Z (0x1A) al final como EOF marker
- Checksums válidos

USO:
    python exe2hex.py input.exe output.hex [base_address]

    base_address: dirección lineal base (default: 0xBC160)

NOTAS:
- El .EXE debe ser de 16-bit (compilado con MSVC 1.52 o similar)
- El formato HEX replica exactamente la estructura del runtime.hex original
- El PDT 3100 verifica el contenido con CRC16-CCITT después de escribir
"""

import sys, struct, os

def read_exe(path):
    """Lee un archivo .EXE y retorna el código binario + entry point."""
    with open(path, 'rb') as f:
        data = f.read()
    
    if data[:2] != b'MZ':
        print(f"Error: {path} no es un EXE válido (sin header MZ)")
        sys.exit(1)
    
    # Parsear header MZ
    last_block = struct.unpack('<H', data[2:4])[0]
    num_blocks = struct.unpack('<H', data[4:6])[0]
    num_relocs = struct.unpack('<H', data[6:8])[0]
    hdr_size = struct.unpack('<H', data[8:10])[0]  # en párrafos (16 bytes)
    
    hdr_bytes = hdr_size * 16
    exe_size = num_blocks * 512 - (512 - last_block) if last_block else num_blocks * 512
    
    print(f"EXE header:")
    print(f"  Header size: {hdr_bytes} bytes ({hdr_size} paragraphs)")
    print(f"  Image size: {exe_size} bytes")
    print(f"  Relocations: {num_relocs}")
    
    # Extraer imagen del programa (sin header)
    image = data[hdr_bytes:hdr_bytes + exe_size]
    
    # CS:IP y SS:SP del header
    ip = struct.unpack('<H', data[20:22])[0]
    cs = struct.unpack('<H', data[22:24])[0]
    ss = struct.unpack('<H', data[14:16])[0]
    sp = struct.unpack('<H', data[16:18])[0]
    
    print(f"  CS:IP = 0x{cs:04X}:0x{ip:04X}")
    print(f"  SS:SP = 0x{ss:04X}:0x{sp:04X}")
    
    return image, cs, ip, ss, sp, num_relocs

def checksum(data_bytes):
    """Calcula checksum Intel HEX."""
    return (-sum(data_bytes)) & 0xFF

def data_record(offset, data):
    """Genera un data record Intel HEX (type 00)."""
    bc = len(data)
    addr_hi = (offset >> 8) & 0xFF
    addr_lo = offset & 0xFF
    body = bytes([bc, addr_hi, addr_lo, 0x00]) + data
    cs = checksum(body)
    return ":" + (body + bytes([cs])).hex().upper()

def esa_record(segment):
    """Genera un Extended Segment Address record (type 02)."""
    seg_hi = (segment >> 8) & 0xFF
    seg_lo = segment & 0xFF
    body = bytes([0x02, 0x00, 0x00, 0x02, seg_hi, seg_lo])
    cs = checksum(body)
    return ":" + (body + bytes([cs])).hex().upper()

def bin_to_ihex(blob, base_addr, line_len=0x10):
    """Convierte binario a Intel HEX con formato DOS del PDT 3100."""
    lines = []
    seg_step = 0x40
    bytes_per_normal_seg = 0x400  # 1024 bytes por segmento
    
    # Tamaño del primer segmento (alinea a 0x400)
    first_seg_size = (bytes_per_normal_seg - (base_addr % bytes_per_normal_seg)) % bytes_per_normal_seg
    first_seg_size = min(first_seg_size if first_seg_size > 0 else bytes_per_normal_seg, len(blob))
    
    cur_seg = (base_addr >> 4) & 0xFFFF
    pos = 0
    total_size = len(blob)
    
    # Primer segmento
    lines.append(esa_record(cur_seg))
    block_end = min(pos + first_seg_size, total_size)
    block_offset = 0
    while pos < block_end:
        chunk_size = min(line_len, block_end - pos)
        chunk = blob[pos:pos+chunk_size]
        lines.append(data_record(block_offset, chunk))
        pos += chunk_size
        block_offset += chunk_size
    cur_seg += first_seg_size // 16
    
    # Segmentos siguientes
    while pos < total_size:
        lines.append(esa_record(cur_seg))
        block_end = min(pos + bytes_per_normal_seg, total_size)
        block_offset = 0
        while pos < block_end:
            chunk_size = min(line_len, block_end - pos)
            chunk = blob[pos:pos+chunk_size]
            lines.append(data_record(block_offset, chunk))
            pos += chunk_size
            block_offset += chunk_size
        cur_seg += seg_step
    
    lines.append(":00000001FF")  # EOF
    # Formato DOS: CRLF + Ctrl-Z
    return "\r\n".join(lines) + "\r\n\x1a"

def main():
    if len(sys.argv) < 3:
        print("Uso: python exe2hex.py input.exe output.hex [base_address]")
        print()
        print("  base_address: dirección lineal base (default: 0xBC160)")
        sys.exit(1)
    
    exe_path = sys.argv[1]
    hex_path = sys.argv[2]
    base_addr = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0xBC160
    
    print(f"=== Convirtiendo {exe_path} → {hex_path} ===")
    print(f"Base address: 0x{base_addr:06X}")
    print()
    
    # Leer EXE
    image, cs, ip, ss, sp, num_relocs = read_exe(exe_path)
    
    print(f"Imagen binaria: {len(image)} bytes")
    print()
    
    # Convertir a Intel HEX
    hex_text = bin_to_ihex(image, base_addr)
    
    # Guardar
    with open(hex_path, "w", encoding="latin-1") as f:
        f.write(hex_text)
    
    hex_size = os.path.getsize(hex_path)
    print(f"HEX generado: {hex_path}")
    print(f"  Tamaño: {hex_size:,} bytes ({hex_size/1024:.1f} KB)")
    print(f"  Líneas: {hex_text.count(chr(13))}")
    print()
    print(f"Cargar al PDT 3100:")
    print(f"  1. Boot to Command Mode (F+I+PWR)")
    print(f"  2. Seleccionar 'Program Loader'")
    print(f"  3. Configurar: 19200 baud, 7 data, Odd parity, Xon/Xoff")
    print(f"  4. En PC: sendhex {os.path.splitext(os.path.basename(hex_path))[0]} 19200 2")

if __name__ == "__main__":
    main()
