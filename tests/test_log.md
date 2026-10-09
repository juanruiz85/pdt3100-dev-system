# Log de Pruebas - PDT 3100 Development System

## Historial de pruebas

| Fecha | Prueba | Resultado | Notas |
|---|---|---|---|
| 2026-10-08 | Análisis del runtime.hex original (147KB) | ✅ | Arquitectura: 80186 + FAT filesystem + MAIN.EXE + overlay |
| 2026-10-08 | Localización del flag de modo DS:0x1091 | ✅ | Variable global con 6 referencias (1 escritura + 5 lecturas) |
| 2026-10-08 | Diseño de parches para forzar modo Admin | ✅ | 6 parches (A-F), 138 bytes total |
| 2026-10-08 | Generación de runtime_patched.hex | ✅ | Formato Intel HEX con CRLF + Ctrl-Z + estructura de segmentos idéntica |
| 2026-10-08 | Flash de runtime_patched.hex al PDT 3100 | ⚠️ | Status 0000 (transfer OK) pero boot falla - BIOS rechaza por CRC |
| 2026-10-08 | Recuperación con runtime.hex original | ✅ | Dispositivo funcionando nuevamente en modo RunTime |
| 2026-10-08 | Análisis del MAME ROM (3 chips de 128KB) | ✅ | U8=DR-DOS+BIOS, U9=NVM Loader 1.02-00, U11=EEPROM vacía |
| 2026-10-08 | Búsqueda de tabla CRC en MAME ROM | ✅ | Tabla CRC16-CCITT encontrada en U8 @ 0x19D13 (poly 0x1021) |
| 2026-10-08 | Búsqueda del CRC esperado en runtime.hex | ❌ | No encontrado - el CRC está hardcodeado en el código del BIOS |
| 2026-10-08 | Búsqueda del ADK oficial de Symbol | ❌ | No disponible públicamente. Solo documentación (YUMPU) |
| 2026-10-08 | Búsqueda de MSVC 1.52c | ✅ | Disponible en archive.org (ISO image, 195MB) |
| 2026-10-08 | Creación del proyecto pdt3100-dev-system | ✅ | Repo creado en GitHub con estructura inicial |

## Próximas pruebas planeadas

| # | Prueba | Estado |
|---|---|---|
| 1 | Descargar e instalar MSVC 1.52c en DOSBox | Pendiente |
| 2 | Compilar hello.c con MSVC 1.52c | Pendiente |
| 3 | Convertir hello.exe a hello.hex con exe2hex.py | Pendiente |
| 4 | Cargar hello.hex al PDT 3100 via SENDHEX | Pendiente |
| 5 | Verificar "Hello World" en pantalla del PDT 3100 | Pendiente |
| 6 | Documentar funciones del BIOS desde MAME ROM | Pendiente |
| 7 | Implementar librería libbios (wrapper de INT calls) | Pendiente |
| 8 | Crear programa de ejemplo con scanner láser | Pendiente |

---

## 2026-10-08 - Compilación de prueba con bcc/NASM

| # | Prueba | Resultado | Notas |
|---|---|---|---|
| 1 | Instalar bcc (Bruce's C Compiler) via apt | ❌ | Sin permisos de root |
| 2 | Clonar y compilar dev86 (bcc) desde GitHub | ⚠️ | bcc compilado pero bcc-cpp falló (errores de gcc moderno) |
| 3 | Instalar NASM | ❌ | Sin permisos de root |
| 4 | Crear .COM manualmente con Python | ✅ | hello_test.com (651 bytes, 395 bytes de código) |
| 5 | Convertir .COM a Intel HEX | ✅ | hello_test.hex (1.8 KB, 43 líneas, formato DOS correcto) |

### Próximas pruebas:
- Cargar hello_test.hex al PDT 3100 via SENDHEX
- Verificar que aparezca "Hello from Python!" en pantalla
- Si funciona: comenzar a implementar más funciones del BIOS

### Archivos generados:
- `src/hello_test.com` - Ejecutable .COM de 16-bit (651 bytes)
- `src/hello_test.hex` - Intel HEX con formato DOS (1.8 KB)
- `src/hello_test.asm` - Source en ensamblador NASM (referencia)
- `tools/exe2hex.py` - Actualizado para soportar .EXE y .COM

---

## 2026-10-08 - Prueba de carga de hello_test.hex

### Resultado: ❌ FALLO - El dispositivo borró el NVM y no arrancó nuestra app

### Qué pasó:
1. El PDT 3100 inició y mostró "ERASING NVM" ← esto BORRÓ la EEPROM
2. Después mostró "NVM Loader 1.20-00" (versión diferente al MAME ROM que era 1.02-00)
3. Mostró menú "Protocol" con opciones: Standard, 2-Way, Spectrum
4. Usuario seleccionó "Standard"
5. Pidió opciones de velocidad y comunicación
6. Mostró "Connecting to host"

### Análisis del fallo:
El problema es que nuestro hello_test.hex era un simple .COM (651 bytes) convertido a HEX.
PERO el PDT 3100 no ejecuta .COM sueltos - espera una IMAGEN COMPLETA del NVM que incluye:

1. Boot sector (formato "MSI BOOT" con BPB)
2. Tabla FAT12
3. Root directory con entradas de archivos
4. CONFIG.SYS que especifica qué programas cargar
5. Los programas .EXE reales (MAIN.EXE, SCAN3000.EXE)

El runtime.hex original (147KB) tiene TODA esta estructura. Nuestro hello_test.hex
(1.8KB) solo tenía el código binario del .COM sin estructura de filesystem.

### Información descubierta:
- NVM Loader del dispositivo: versión 1.20-00 (más nueva que la del MAME ROM: 1.02-00)
- El NVM Loader tiene menú de Protocol: Standard, 2-Way, Spectrum
- Puede descargar aplicaciones via red (Spectrum), 2-Way modem, o serial (Standard)

### Próximo paso:
1. URGENTE: Flashear runtime.hex original para recuperar el dispositivo
2. Crear imagen NVM completa con filesystem FAT12 + boot sector + CONFIG.SYS + nuestro programa

---

## 2026-10-08 - Creación de NVM Builder + imagen NVM completa

### Hallazgo CRÍTICO:
El PDT 3100 NO hace verificación CRC. El hello_test.hex se transfirió y escribió
al NVM correctamente (vimos "ERASING NVM"). El problema fue que enviamos un .COM
suelto (sin filesystem) en lugar de una imagen NVM completa.

### Solución: NVM Builder
Creado `tools/nvm_builder.py` que:
1. Toma el runtime.hex original como BASE (con filesystem FAT12 completo)
2. Reemplaza el contenido de MAIN.EXE con nuestro programa
3. Mantiene toda la estructura del filesystem intacta
4. Genera Intel HEX con formato DOS correcto

### Archivos generados:
- `tools/nvm_builder.py` - herramienta para construir imágenes NVM
- `src/hello_bare.bin` - código 8086 puro (359 bytes, sin PSP)
- `src/hello_nvm.hex` - imagen NVM completa (416 KB, mismo tamaño que original)

### Próximo paso: cargar hello_nvm.hex al PDT 3100 y probar

---

## 2026-10-09 - Prueba de hello_nvm.hex (imagen NVM con MAIN.EXE reemplazado)

### Resultado: ❌ FALLO - Mismo comportamiento que hello_test.hex

### Qué pasó:
- El dispositivo mostró "ERASING NVM"
- Luego pasó a "NVM Loader 1.20-00"
- Mismo comportamiento que antes: el NVM se borra pero la app no arranca

### Análisis:
Modificar el runtime.hex original (reemplazando MAIN.EXE) NO funciona.
El problema podría ser:
1. El BIOS SÍ verifica algo (no CRC, pero quizás checksum o tamaño)
2. La estructura del MZ EXE que generamos no es compatible
3. El shell.com (en drive A:) no puede cargar nuestro EXE
4. Hay dependencias en el overlay/librería que MAIN.EXE necesita

### NUEVO ENFOQUE: Crear imagen NVM desde cero
En lugar de modificar el runtime.hex existente, crear una imagen NVM
completamente nueva con:
- Boot sector MSI BOOT con BPB
- FAT12 filesystem creado desde cero
- CONFIG.SYS simple
- Nuestro programa como .EXE
- Sin depender del runtime.hex original

---

## 2026-10-09 - NVM desde cero

### Nuevo enfoque: crear imagen NVM sin depender del runtime.hex original

Creado `tools/nvm_from_scratch.py` que construye una imagen NVM completa:
1. Header (80 bytes) - copiado del original
2. Far pointer table (224 bytes) - con punteros a nuestros recursos
3. CONFIG.SYS simplificado: "shell=a:shell.com b:hello.exe"
4. Boot sector "MSI BOOT" con BPB (mismos parámetros que original)
5. FAT12 con entry para HELLO.EXE (cluster 2, end of chain)
6. Root directory con entrada para HELLO.EXE
7. Data area con nuestro programa como MZ EXE
8. Padding a 147104 bytes (mismo tamaño que original)

### Archivos generados:
- `tools/nvm_from_scratch.py` - constructor de NVM desde cero
- `src/hello_scratch.hex` - imagen NVM lista para cargar (416,192 bytes)

### Próximo paso: cargar hello_scratch.hex al PDT 3100

---

## 2026-10-09 - Renombrar archivo a hello.hex

### Pregunta del usuario:
¿Afecta renombrar hello_scratch.hex a hello.hex?

### Respuesta:
NO afecta en absoluto. El nombre del archivo en la PC es irrelevante para el PDT 3100.
SENDHEX lee el archivo .hex y envía su contenido via serial al dispositivo.
El dispositivo recibe los bytes del Intel HEX y los escribe al NVM.

El nombre del archivo solo importa para:
1. Que SENDHEX lo encuentre (debe coincidir el parámetro: sendhex hello 19200 2)
2. Windows 98 no soporta nombres largos en FAT12/FAT16 (máx 8.3 = 8 chars + 3 ext)

### Renombrar a hello.hex es CORRECTO:
- sendhex hello 19200 2 ← busca "hello.hex" en el directorio actual
- Funciona en Windows 98 (nombre 8.3: "hello" = 5 chars, ".hex" = 3 chars ext)

---

## 2026-10-09 - hello_scratch.hex: MISMO FALLO (ERASING NVM)

### Resultado: ❌ "ERASING NVM" al hacer Cold Boot

Esto confirma: el BIOS verifica el contenido del NVM después de escribirlo
y ANTES de bootear. Si la verificación falla, borra el NVM y entra
al NVM Loader.

### Prueba crítica: test_1byte.hex
Creado un HEX que es IDÉNTICO al runtime.hex original EXCEPTO por
1 solo byte en el área de padding (offset 0x23E9F: 0x00→0x01).

- Si funciona → NO hay verificación completa, podemos modificar
- Si falla    → SÍ hay CRC/hash, necesitamos encontrar y recalcular

---

## 2026-10-09 - test_1byte.hex: FALLO (ERASING NVM)

### Resultado: ❌ ERASING NVM

### CONCLUSIÓN DEFINITIVA:
El BIOS SÍ hace verificación de integridad completa del NVM.
Cambiar UN SOLO BYTE en padding (área no crítica) causa rechazo.
Esto confirma: hay un CRC o hash almacenado en el BIOS (chips U8/U9).

### Lo que sabemos:
1. El BIOS verifica el NVM completo (no solo partes específicas)
2. Cambiar 1 byte → verificación falla → ERASING NVM → NVM Loader
3. El algoritmo de verificación está en el BIOS (MAME ROM U8/U9)
4. El CRC esperado está hardcodeado en el BIOS
5. Tabla CRC16-CCITT encontrada en U8 @ 0x19D13
6. Strings "ROM CRC: NVM CRC:" y "Verifying NVM Image" en U9

### Lo que necesitamos hacer:
1. Analizar el código del BIOS (U8/U9) que hace la verificación
2. Encontrar dónde está el CRC esperado
3. Calcular el CRC correcto para nuestro NVM modificado
4. O encontrar el algoritmo exacto y recalcular

---

## 2026-10-09 - Análisis de CRC: resultados

### Hallazgo DEFINITIVO:
**El BIOS hace verificación CRC completa del NVM.**
- Cambiar 1 byte en padding → ERASING NVM → rechazado
- No podemos modificar el NVM sin recalcular el CRC

### Análisis del CRC:
- Tabla CRC16-CCITT encontrada en MAME ROM U8 @ 0x19D13 (poly 0x1021)
- Strings "ROM CRC: NVM CRC:" y "Verifying NVM Image" en U9
- CRC16-CCITT (init=0xFFFF) del runtime.bin = 0x33D8
- CRC16-CCITT (init=0x0000) = 0x8B84
- Buscado en U8/U9: solo falsos positivos (instrucciones comunes)
- Probado con 10+ init values y poly reflected: sin matches únicos

### PROBLEMA: Versiones diferentes
- MAME ROM BIOS: v1.02-00 (NVM Loader 1.02-00)
- BIOS del usuario: v1.20-00 (NVM Loader 1.20-00)
- El CRC esperado está en el BIOS del usuario, NO en el MAME ROM
- Sin el BIOS exacto del usuario, no podemos encontrar el CRC

### Nueva estrategia: usar el NVM Loader
El dispositivo muestra "NVM Loader 1.20-00" con menú Protocol:
- Standard (serial)
- 2-Way (modem)
- Spectrum (radio)

El NVM Loader descarga aplicaciones INDIVIDUALES (no imagen completa).
Quizás no hace verificación CRC (es un loader, no un verificador).
El protocolo Standard probablemente usa XMODEM (CONFIG.SYS carga xmodem.sys).

### Próximo paso:
Probar usar el NVM Loader (modo Standard) para descargar un archivo
individual, en lugar de usar el Program Loader (que escribe el NVM completo).
