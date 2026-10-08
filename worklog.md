---
Task ID: 1
Agent: main
Task: Crear proyecto pdt3100-dev-system para desarrollo de aplicaciones en C para Symbol PDT 3100

Work Log:
- Creado repo en GitHub: https://github.com/juanruiz85/pdt3100-dev-system
- Creado README.md con info completa del dispositivo (PDT3168-S84E2016)
- Creados headers C iniciales: bios.h, display.h, scanner.h
- Creado src/hello.c (programa Hello World)
- Creado tools/exe2hex.py (convertidor EXE → Intel HEX)
- Copiada documentación de referencia al repo:
  - PDT 3100 Product Reference Guide (136 páginas)
  - Series 3000 Application Programmer's Guide (386 páginas)
  - MAME ROM con 3 chips del BIOS (U8=DR-DOS+BIOS, U9=NVM Loader, U11=EEPROM)
  - Fotos del dispositivo (pantalla de boot + etiqueta)
- Creado tests/test_log.md con historial de pruebas

Stage Summary:
- Repo creado y estructurado
- Próximos pasos: descargar MSVC 1.52c de archive.org y compilar hello.c

---
Task ID: 2
Agent: main
Task: Búsqueda del ADK de Symbol Series 3000

Work Log:
- Buscado en archive.org, GitHub, Zebra.com, IBM, foros
- Encontrado IBM DCConnect menciona LWP4_02_07.ZIP y BLDINIT
- Encontrado A1SI (ez-snap) - empresa que desarrolló apps para PDT 3100 (1997-2001)
- ADK versión 4.42 mencionada en IBM (circa 2004)
- Symbol Developer Zone (software.symbol.com/devzone) está offline
- Zebra support.zebra.com tiene artículos de Series 3000 pero no descargas del ADK
- YUMPU tiene el Programmer's Guide completo (386p) pero no el software

Stage Summary:
- ADK NO disponible públicamente
- Alternativa: crear sistema custom con MSVC 1.52c + headers C + exe2hex.py
- Documentado todo en docs/ADK_SEARCH_LOG.md
