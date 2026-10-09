# 🔧 PDT 3100 Development System

> Sistema de desarrollo custom para crear aplicaciones en C para el **Symbol PDT 3100/3168** (80186, DR-DOS) sin necesidad del ADK oficial de Symbol.

![Platform](https://img.shields.io/badge/platform-Symbol%20PDT%203168-orange)
![CPU](https://img.shields.io/badge/CPU-Intel%2080186-red)
![OS](https://img.shields.io/badge/OS-DR--DOS-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 📱 Dispositivo objetivo

| Parámetro | Valor |
|---|---|
| **Modelo** | PDT3168-S84E2016 |
| **Teclado** | 46 teclas alfanumérico |
| **CPU** | Intel 80c88 (80188-class, 8 MHz) |
| **OS** | DR-DOS (compatible IBM PC-DOS) |
| **Memoria** | 640KB TPA, 0KB EMS |
| **Display** | 8 líneas × 20 caracteres LCD |
| **Scanner** | Láser integrado |
| **Versión SER** | 3000 1.09-00 |
| **Versión BIOS** | 3100 1.09-00 |
| **S/N** | K444134 |
| **Fecha fabricación** | Julio 1998 |

### Boot modes (46-key)

| Modo | Combinación | Función |
|---|---|---|
| Warm Boot | `4` + `5` + `PWR` | Reset OS, preserva RAM |
| Cold Boot | `A` + `B` + `D` + `PWR` | Reset completo, borra RAM (preserva NVM) |
| Command Mode | `F` + `I` + `PWR` | Self Test, Program Loader, Memory Transfer |

### Comunicación con PC

| Parámetro | Valor |
|---|---|
| Baud rate | 19200 |
| Data bits | 7 |
| Paridad | Odd |
| Flow control | Xon/Xoff |
| Cable | RS-232 null modem via cradle |

---

## 🏗️ Arquitectura

```
PC (DOSBox + MSVC 1.52c)
    │
    ├── Compilar C → EXE (16-bit DOS)
    ├── Convertir EXE → HEX (Intel HEX format)
    └── SENDHEX.EXE → Cargar al PDT 3100
            │
            │ RS-232 19200 baud
            │
PDT 3100 (80186 + DR-DOS)
    ├── Chip U8 (128KB) = BIOS + DR-DOS
    ├── Chip U9 (128KB) = NVM Loader 1.02-00
    └── Chip U11 (128KB) = EEPROM (aplicaciones)
```

---

## 📁 Estructura del proyecto

```
pdt3100-dev-system/
├── README.md                    ← Este archivo
├── docs/                        ← Documentación de referencia
│   ├── PDT-3100-Product-Reference-Guide-english.pdf
│   ├── Series-3000-Application-Programmers-Guide.pdf
│   ├── 7240649.pdf
│   ├── scanner_photos/          ← Fotos del dispositivo
│   └── mame_rom/                ← ROM del MAME (BIOS completo)
│       ├── *.u8  (128KB) = DR-DOS + BIOS
│       ├── *.u9  (128KB) = NVM Loader
│       └── *.u11 (128KB) = EEPROM
├── include/                     ← Headers C (BIOS API)
├── src/                         ← Código fuente
├── tools/                       ← Herramientas de build
├── tests/                       ← Log de pruebas
└── worklog.md                   ← Bitácora del proyecto
```

---

## 🔨 Compilador

### Microsoft Visual C++ 1.52c (recomendado)
- Descargar: https://archive.org/details/Microsoft_Visual_C_-_Version_1.52c_Microsoft_1995
- Alternativa: https://archive.org/details/ms-vc152

### Compiladores alternativos open source
- **Open Watcom C/C++**: https://github.com/open-watcom/
- **Bruce's C Compiler (bcc)**: https://gitlab.com/FreeDOS/devel/bcc
- **Smaller C**: https://hackaday.io/project/5569-smaller-c

---

## 📚 Documentación

| Documento | Páginas | Contenido |
|---|---|---|
| PDT 3100 Product Reference Guide | 136 | Boot modes, Command Mode, Program Loader |
| Series 3000 Application Programmer's Guide | 386 | ADK install, C programming, APIs |
| MAME ROM pdt3100.zip | 3 chips | BIOS completo del PDT 3100 |

---

## 📝 Log de pruebas

Ver `tests/test_log.md` para el registro completo de pruebas.

---

## ⚠️ Disclaimer

- El Symbol PDT 3100 es un dispositivo descontinuado
- Este proyecto crea herramientas de desarrollo INDEPENDIENTES del ADK oficial
- Las APIs del BIOS se documentan a partir del análisis del MAME ROM
- No se distribuye software con copyright de Symbol Technologies

---

<sub>Proyecto para desarrollar aplicaciones en C para el Symbol PDT 3100/3168.</sub>
