#!/usr/bin/env python3
"""exe2hex.py - Convierte .EXE o .COM de 16-bit a formato Intel HEX
para carga en el Symbol PDT 3100 via SENDHEX.

USO:
    python exe2hex.py input.exe output.hex [base_address]
    python exe2hex.py input.com output.hex [base_address]

    base_address: dirección lineal base (default: 0xBC160)
"""

import sys, struct, os

def read_exe(path):
    """Lee un .EXE (con header MZ) y retorna la imagen binaria."""
    with open(path, 'rb') as f:
        data = f.read()
    
    if data[:2] != b'MZ':
        return None, "No es EXE (sin header MZ)"
    
    last_block = struct.unpack('<H', data[2:4])[0]
    num_blocks = struct.unpack('<H', data[4:6])[0]
    hdr_size = struct.unpack('<H', data[8:10])[0]
    hdr_bytes = hdr_size * 16
    exe_size = num_blocks * 512 - (512 - last_block) if last_block else num_blocks * 512
    
    print(f"EXE: hdr={hdr_bytes}B, image={exe_size}B")
    return data[hdr_bytes:hdr_bytes + exe_size], None

def read_com(path):
    """Lee un .COM (sin header MZ, empieza en offset 0x100)."""
    with open(path, 'rb') as f:
        data = f.read()
    
    print(f"COM: {len(data)}B (incluye PSP de 256B)")
    return data, None  # Retornar todo (incluyendo PSP)

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
    """Convierte binario a Intel HEX con formato DOS del PDT 3100."""
    lines = []
    seg_step = 0x40
    bytes_per_seg = 0x400
    
    first_seg_size = (bytes_per_seg - (base_addr % bytes_per_seg)) % bytes_per_seg
    first_seg_size = min(first_seg_size if first_seg_size > 0 else bytes_per_seg, len(blob))
    
    cur_seg = (base_addr >> 4) & 0xFFFF
    pos = 0
    total_size = len(blob)
    
    # Primer segmento
    lines.append(esa_record(cur_seg))
    block_end = min(pos + first_seg_size, total_size)
    block_offset = 0
    while pos < block_end:
        chunk_size = min(line_len, block_end - pos)
        lines.append(data_record(block_offset, blob[pos:pos+chunk_size]))
        pos += chunk_size
        block_offset += chunk_size
    cur_seg += first_seg_size // 16
    
    # Segmentos siguientes
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
        print("Uso: python exe2hex.py input.exe|input.com output.hex [base_address]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    hex_path = sys.argv[2]
    base_addr = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0xBC160
    
    ext = os.path.splitext(input_path)[1].lower()
    
    if ext == '.com':
        blob, err = read_com(input_path)
    elif ext == '.exe':
        blob, err = read_exe(input_path)
    else:
        # Intentar EXE primero, luego COM
        blob, err = read_exe(input_path)
        if blob is None:
            blob, err = read_com(input_path)
    
    if blob is None:
        print(f"Error: {err}")
        sys.exit(1)
    
    hex_text = bin_to_ihex(blob, base_addr)
    
    with open(hex_path, "w", encoding="latin-1") as f:
        f.write(hex_text)
    
    hex_size = os.path.getsize(hex_path)
    print(f"\nHEX: {hex_path} ({hex_size:,}B, {hex_text.count(chr(13))} líneas)")
    print(f"\nCargar: sendhex {os.path.splitext(os.path.basename(hex_path))[0]} 19200 2")

if __name__ == "__main__":
    main()
