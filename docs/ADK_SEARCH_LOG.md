# Búsqueda del ADK (Application Development Kit) de Symbol Series 3000

## Estado: NO ENCONTRADO públicamente

## Hallazgos clave:

### 1. IBM DCConnect documentation
- URL: https://publib.boulder.ibm.com/dcconn/html/dcclient/dcclient.htm
- Menciona: "LWP4_02_07.ZIP" (Lan Workplace flash load v4.02.07 de Symbol)
- Menciona: "BLDINIT" tool del ADK que genera INIT.EXE
- Menciona: "MADE W/ADK 4.42" (versión del ADK)
- El archivo LWP4_02_07.ZIP incluye drivers de flash más nuevos
- Pero el link de descarga directo no está disponible públicamente

### 2. Zebra Support
- URL: https://support.zebra.com
- Tiene artículos sobre Series 3000 (configuración de fecha/hora, EEPROM)
- NO tiene descargas del ADK legacy
- Los SDKs actuales (MC3100, MK3100) son para Windows CE, no DR-DOS

### 3. YUMPU - Series 3000 Application Programmer's Guide
- URL: https://www.yumpu.com/en/document/view/17722817/series-3000-application-programmers-guide
- Documentación completa del ADK (386 páginas)
- Describe: instalación del ADK, MSVC 1.5/1.52, BLDINIT, BLDSCAN
- Pero NO incluye el software en sí

### 4. A1SI - EZ-SNAP (ejemplo de app real)
- URL: https://www.a1si.com/projects/ezsnap-camera-order-entry
- Empresa que desarrolló apps para Symbol PDT 3100 (1997-2001)
- "Camera Order Entry System" para Olan Mills, American Family Photographers
- Usaba el scanner del PDT 3100 para captura de órdenes
- Demuestra que el desarrollo de apps era factible y comercial

### 5. TouchWindow UPG (Universal Program Generator)
- URL: https://www.touchwindow.com/mm5/graphics/00000001/datalogic/upgum.pdf
- Herramienta de terceros que usa SENDHEX.EXE
- Alternativa al ADK para generar aplicaciones simples

### 6. Symbol Developer Zone (defunto)
- URL: http://software.symbol.com/devzone (probablemente offline)
- Era el sitio oficial para descargar el ADK
- Symbol → Motorola → Zebra, el sitio ya no existe

## Versión del ADK:
- ADK 4.42 (mencionado en IBM DCConnect, circa 2004)
- El Programmer's Guide es p/n 70-16308-03, Rev A, April 2000

## Alternativa: Crear nuestro propio sistema
Sin el ADK oficial, creamos herramientas custom:
1. MSVC 1.52c (disponible en archive.org) como compilador
2. Headers C con APIs del BIOS (documentadas del MAME ROM)
3. exe2hex.py (convertidor EXE → Intel HEX)
4. SENDHEX.EXE (ya disponible) para cargar al dispositivo

## Dónde seguir buscando:
1. ex-empleados de Symbol Technologies (LinkedIn, foros)
2. Wayback Machine: web.archive.org/web/*/software.symbol.com
3. Coleccionistas de hardware vintage (eBay, foros retro)
4. Foros: barcodehelp.com, reddit r/barcode
5. Grupos de Facebook/WhatsApp de técnicos Symbol/Zebra
