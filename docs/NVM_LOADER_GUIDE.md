# Guía: Usar el NVM Loader del PDT 3100

## Qué es el NVM Loader

Cuando el BIOS no puede verificar el NVM (porque se borró o tiene contenido inválido),
el dispositivo entra automáticamente al **NVM Loader**. Este modo permite descargar
aplicaciones individuales al NVM, en lugar de flashear la imagen completa.

## Cómo entrar al NVM Loader

1. Flashear un NVM inválido (ej: hello_scratch.hex) via Program Loader
2. El dispositivo borrará el NVM y mostrará "NVM Loader 1.20-00"
3. Aparece el menú "Protocol" con opciones: Standard, 2-Way, Spectrum

## Configuración

Seleccionar **Standard** (comunicación serial via cradle):
- Baud rate: 19200
- Data bits: 7
- Parity: Odd
- Flow control: Xon/Xoff

## Herramientas para Windows 11

### Opción 1: PuTTY (RECOMENDADO para conexión serial)
1. Descargar PuTTY de: https://www.putty.org/
2. Tipo de conexión: **Serial**
3. Puerto: **COM2** (o el que use tu cradle)
4. Velocidad: **19200**
5. En Configuration → Terminal:
   - Terminal-type string: **xterm** o **dumb**
   - Local echo: **Force on** (para ver lo que escribes)
6. En Connection → Data:
   - Terminal-type string: **dumb**
7. Conectar

### Opción 2: Tera Term (MEJOR para transferencia XMODEM)
1. Descargar Tera Term de: https://ttssh2.osdn.jp/
2. Tipo: **Serial**
3. Puerto: **COM2**
4. Speed: **19200**
5. Setup → Terminal: Local Echo = ON
6. Para enviar archivos: File → Transfer → XMODEM → Send

### Opción 3: ExtraPuTTY (PuTTY con soporte XMODEM)
- https://extraputty.com/
- Incluye transferencia de archivos XMODEM/YMODEM/ZMODEM

### Opción 4: Línea de comandos con Windows 11
```cmd
# Usar mode para configurar el puerto COM
mode COM2: BAUD=19200 PARITY=ODD DATA=7 STOP=1 XON=ON

# Copiar un archivo via XMODEM
# Windows 11 no incluye XMODEM nativo, usar:
# - Tera Term (recomendado)
# - O un script de Python con pyserial
```

## Qué esperar del NVM Loader

Al conectar via serial, el NVM Loader debería mostrar algo como:
```
NVM Loader 1.20-00
Protocol: Standard
Connecting to host...
```

Y luego esperar a recibir un archivo via XMODEM.

## Diferencia con Program Loader

| Program Loader | NVM Loader |
|---|---|
| Escribe NVM completo (147KB) | Descarga archivos individuales |
| BIOS verifica CRC al bootear | Podría NO verificar CRC |
| Necesita imagen completa con FS | Solo necesita el archivo .EXE |
| Se accede via Command Mode | Aparece automáticamente en boot fallido |

## Archivos a probar

### Para NVM Loader (archivo individual):
- `src/hello_bare.bin` - código 8086 puro (359 bytes)
- Un .EXE construido con MZ header

### Para Program Loader (imagen completa):
- `src/hello_scratch.hex` - imagen NVM completa (416KB)
- Se sabe que falla por CRC

## Próximos pasos

1. Flashear hello_scratch.hex para forzar entrada al NVM Loader
2. Seleccionar Standard protocol
3. Conectar desde Windows 11 con PuTTY/Tera Term
4. Observar qué muestra el NVM Loader
5. Intentar enviar un archivo via XMODEM
6. Documentar el resultado
