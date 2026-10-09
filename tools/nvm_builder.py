#!/usr/bin/env python3
"""
nvm_builder.py - Construye una imagen NVM completa para el Symbol PDT 3100.

Toma el runtime.hex original como base y reemplaza MAIN.EXE con nuestro programa.
Mantiene toda la estructura del filesystem (boot sector, FAT, directorio, CONFIG.SYS).

USO:
    python nvm_builder.py runtime.hex program.com output.hex

    runtime.hex: firmware original del PDT 3100
    program.com: nuestro programa en formato .COM (o .EXE)
    output.hex:  imagen NVM resultante lista para flashear
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
    
    # Construir blob contiguo
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

def build_mz_exe(code, min_mem=0, max_mem=0xFFFF):
    """Crea un MZ EXE mínimo que contiene el código dado."""
    # Header MZ: 28 bytes mínimo (hdr_size = 2 paragraphs = 32 bytes)
    hdr_size_para = 2  # 32 bytes
    hdr_bytes = hdr_size_para * 16  # 32
    
    # Calcular tamaño de la imagen
    # num_blocks = ceil((hdr_bytes + len(code)) / 512)
    total = hdr_bytes + len(code)
    num_blocks = (total + 511) // 512
    last_block = total - (num_blocks - 1) * 512
    if last_block == 512:
        last_block = 0
        num_blocks += 0  # ya está bien
    
    # Padding a múltiplo de 16
    padded_code = bytearray(code)
    while (len(padded_code) + hdr_bytes) % 16 != 0:
        padded_code.append(0x90)  # NOP padding
    
    # Header MZ (28 bytes, padded to 32)
    header = bytearray(32)
    header[0:2] = b'MZ'
    struct.pack_into('<H', header, 2, last_block)
    struct.pack_into('<H', header, 4, num_blocks)
    struct.pack_into('<H', header, 6, 0)  # num_relocs = 0
    struct.pack_into('<H', header, 8, hdr_size_para)
    struct.pack_into('<H', header, 10, min_mem)
    struct.pack_into('<H', header, 12, max_mem)
    struct.pack_into('<H', header, 14, 0)  # SS
    struct.pack_into('<H', header, 16, 0xFFFE)  # SP
    struct.pack_into('<H', header, 18, 0)  # checksum
    struct.pack_into('<H', header, 20, 0)  # IP
    struct.pack_into('<H', header, 22, 0)  # CS
    struct.pack_into('<H', header, 24, 0x1C)  # reloc_table_offset
    struct.pack_into('<H', header, 26, 0)  # overlay
    
    return bytes(header) + bytes(padded_code)

def checksum(data_bytes):
    return (-sum(data_bytes)) & 0xFF

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
        chunk = blob[pos:pos+chunk_size]
        lines.append(data_record(block_offset, chunk))
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
            chunk = blob[pos:pos+chunk_size]
            lines.append(data_record(block_offset, chunk))
            pos += chunk_size
            block_offset += chunk_size
        cur_seg += seg_step
    
    lines.append(":00000001FF")
    return "\r\n".join(lines) + "\r\n\x1a"

def data_record(offset, data):
    bc = len(data)
    body = bytes([bc, (offset>>8)&0xFF, offset&0xFF, 0x00]) + data
    cs = checksum(body)
    return ":" + (body + bytes([cs])).hex().upper()

def esa_record(segment):
    body = bytes([0x02, 0x00, 0x00, 0x02, (segment>>8)&0xFF, segment&0xFF])
    cs = checksum(body)
    return ":" + (body + bytes([cs])).hex().upper()

def main():
    if len(sys.argv) < 4:
        print("Uso: python nvm_builder.py runtime.hex program.com output.hex")
        print()
        print("  runtime.hex:  firmware original del PDT 3100")
        print("  program.com:  nuestro programa (.COM o .EXE o binario raw)")
        print("  output.hex:  imagen NVM resultante")
        sys.exit(1)
    
    runtime_path = sys.argv[1]
    program_path = sys.argv[2]
    output_path = sys.argv[3]
    
    print(f"=== NVM Builder ===")
    print(f"Base: {runtime_path}")
    print(f"Programa: {program_path}")
    print(f"Output: {output_path}")
    print()
    
    # 1. Parsear runtime.hex original
    print("1. Parseando runtime.hex original...")
    runtime_bin, base_addr = parse_ihex(runtime_path)
    print(f"   Binario: {len(runtime_bin)} bytes, base 0x{base_addr:06X}")
    
    # 2. Leer nuestro programa
    print("2. Leyendo programa...")
    program_data = open(program_path, 'rb').read()
    print(f"   Programa: {len(program_data)} bytes")
    
    # 3. Si es .COM, convertir a MZ EXE
    if program_data[:2] != b'MZ':
        print("3. Convirtiendo .COM a MZ EXE...")
        program_exe = build_mz_exe(program_data)
        print(f"   EXE generado: {len(program_exe)} bytes")
    else:
        print("3. Programa ya es MZ EXE")
        program_exe = program_data
    
    # 4. Encontrar MAIN.EXE en el runtime.bin
    # MAIN.EXE MZ header está en file_off 0x2577
    # MAIN.EXE size = 11792 bytes (según FAT directory entry)
    main_off = runtime_bin.find(b'MZ', 0x2000)  # buscar MZ después de offset 0x2000
    if main_off == -1:
        print("ERROR: No se encontró MZ header de MAIN.EXE")
        sys.exit(1)
    
    # Buscar el segundo MZ (SCAN3000.EXE está antes)
    main_off2 = runtime_bin.find(b'MZ', main_off + 1)
    if main_off2 != -1 and main_off2 - main_off < 100:
        # El primer MZ encontrado podría ser SCAN3000, buscar el siguiente
        main_off = runtime_bin.find(b'MZ', main_off2 + 1)
        if main_off == -1:
            main_off = main_off2  # usar el segundo
    
    # Verificar que es un MZ válido
    hdr_size = struct.unpack('<H', runtime_bin[main_off+8:main_off+10])[0] * 16
    num_blocks = struct.unpack('<H', runtime_bin[main_off+4:main_off+6])[0]
    last_block = struct.unpack('<H', runtime_bin[main_off+2:main_off+4])[0]
    exe_size = num_blocks * 512 - (512 - last_block) if last_block else num_blocks * 512
    
    print(f"4. MAIN.EXE encontrado:")
    print(f"   Offset: 0x{main_off:06X} (addr 0x{base_addr+main_off:06X})")
    print(f"   Header size: {hdr_size} bytes")
    print(f"   Image size: {exe_size} bytes ({exe_size/1024:.1f} KB)")
    
    # 5. Reemplazar MAIN.EXE con nuestro programa
    print("5. Reemplazando MAIN.EXE...")
    new_bin = bytearray(runtime_bin)
    
    # Nuestro programa debe caber en el espacio de MAIN.EXE
    if len(program_exe) > exe_size:
        print(f"   WARNING: Programa ({len(program_exe)}B) > MAIN.EXE ({exe_size}B)")
        print(f"   Truncando a {exe_size} bytes")
        program_exe = program_exe[:exe_size]
    else:
        # Padding con zeros
        padded = bytearray(program_exe)
        while len(padded) < exe_size:
            padded.append(0)
        program_exe = bytes(padded)
    
    # Reemplazar
    new_bin[main_off:main_off+exe_size] = program_exe
    print(f"   Reemplazados {exe_size} bytes en offset 0x{main_off:06X}")
    
    # 6. Convertir a Intel HEX
    print("6. Generando Intel HEX...")
    hex_text = bin_to_ihex(bytes(new_bin), base_addr)
    
    with open(output_path, 'w', encoding='latin-1') as f:
        f.write(hex_text)
    
    hex_size = os.path.getsize(output_path)
    print(f"   HEX: {output_path} ({hex_size:,} bytes, {hex_text.count(chr(13))} líneas)")
    print()
    print("=== Listo para cargar ===")
    print(f"1. Boot to Command Mode (F+I+PWR)")
    print(f"2. Program Loader")
    print(f"3. 19200 baud, 7 data, Odd parity, Xon/Xoff")
    print(f"4. sendhex {os.path.splitext(os.path.basename(output_path))[0]} 19200 2")
    print(f"5. Esperar Status 0000")
    print(f"6. Cold Boot (A+B+D+PWR)")

if __name__ == "__main__":
    main()
