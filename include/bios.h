/* bios.h - BIOS API para Symbol PDT 3100 (80186 + DR-DOS)
 *
 * Documentado a partir del análisis del MAME ROM (pdt3100.zip)
 * y del Series 3000 Application Programmer's Guide.
 *
 * El BIOS expone funciones via interrupciones software.
 * Estas son las funciones identificadas en el análisis del firmware.
 */

#ifndef _BIOS_H_
#define _BIOS_H_

/* ===== INT 0xA1 - Display Functions ===== */

/* Imprimir carácter en pantalla
 * AH = 0x0E, AL = carácter ASCII
 */
void bios_putc(char c);

/* Imprimir carácter con atributo
 * AH = 0x02, AL = carácter, BL = atributo/color
 */
void bios_putc_attr(char c, unsigned char attr);

/* Leer tecla (con wait)
 * AH = 0x01, CX = 0 (modo normal) o CX = 0x2000 (modo especial)
 * Retorna: AL = carácter ASCII
 */
int bios_getc(void);

/* Limpiar pantalla */
void bios_cls(void);

/* Posicionar cursor
 * AH = 0x02, DH = fila, DL = columna
 */
void bios_gotoxy(unsigned char row, unsigned char col);

/* ===== INT 0xA7 - System Functions ===== */

/* Delay/pausa
 * AX = 0x8000, CX = milisegundos, DX = ?
 */
void bios_delay(unsigned int ms);

/* Función del sistema 0x8300
 * (identificada en código del NVM Loader)
 */
void bios_sys_8300(void);

/* Función del sistema 0x8340
 * (identificada en código del NVM Loader)
 */
void bios_sys_8340(void);

/* ===== INT 0xA6 - Scanner (estimado) ===== */

/* Inicializar scanner
 * (AX = 0x8000, INT 0xA6 - a confirmar)
 */
void bios_scanner_init(void);

/* Leer dato escaneado
 * (a documentar)
 */
int bios_scanner_read(char *buf, int maxlen);

/* ===== INT 0xB3 - Communications ===== */

/* Transferir datos al/desde NVM
 * AH = 0x00, SI = puntero buffer, CX = tamaño
 */
int bios_nvm_transfer(void far *buf, unsigned int size);

/* ===== INT 0xA1 - Sound ===== */

/* Beep
 * AH = 0x0E, AL = 0x07 (BEL character)
 */
void bios_beep(void);

/* ===== Utilidades ===== */

/* Imprimir string */
void bios_puts(const char *s);

/* Imprimir string con formato (printf-like) */
void bios_printf(const char *fmt, ...);

/* Leer estado de batería
 * (devuelve: 0=GOOD, 1=LOW, 2=DEAD)
 */
int bios_battery_status(void);

/* Obtener memoria disponible (en bytes) */
unsigned int bios_mem_available(void);

#endif /* _BIOS_H_ */
