/* scanner.h - API del scanner láser para Symbol PDT 3100
 *
 * Scanner láser integrado para lectura de códigos de barras
 */

#ifndef _SCANNER_H_
#define _SCANNER_H_

/* Tipos de código soportados */
#define BARCODE_UPCA    0x01
#define BARCODE_UPCE    0x02
#define BARCODE_EAN13   0x04
#define BARCODE_EAN8    0x08
#define BARCODE_CODE39  0x10
#define BARCODE_CODE128 0x20
#define BARCODE_CODABAR 0x40
#define BARCODE_I25     0x80

/* Inicializar scanner */
void scanner_init(void);

/* Activar scanner (trigger) */
void scanner_trigger_on(void);

/* Desactivar scanner */
void scanner_trigger_off(void);

/* Leer dato escaneado (bloqueante, espera hasta leer)
 * Retorna: longitud del dato, o 0 si timeout
 * El dato se guarda en buf (maxlen caracteres)
 */
int scanner_read(char *buf, int maxlen);

/* Configurar tipo de código a leer */
void scanner_set_type(unsigned int types);

/* Verificar si hay dato en buffer */
int scanner_data_ready(void);

/* Obtener tipo de último código leído */
int scanner_get_type(void);

#endif /* _SCANNER_H_ */
