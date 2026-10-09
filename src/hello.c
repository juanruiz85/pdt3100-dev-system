/*
 * hello.c - Programa "Hello World" para Symbol PDT 3100
 *
 * Compilar con MSVC 1.52c:
 *   cl /AT /Gs /Oilt hello.c
 *
 * O con Open Watcom:
 *   wcl -0 -os -ml hello.c
 *
 * Convertir a HEX:
 *   python tools/exe2hex.py hello.exe hello.hex
 *
 * Cargar al PDT 3100:
 *   sendhex hello 19200 2
 */

/* BIOS interrupt functions - definidas en libbios/ */
/* Por ahora usamos直接 INT calls */

#include <dos.h>

/* INT 0xA1 con AH=0x0E: imprimir carácter en pantalla */
void putc_bios(char c) {
    union REGS regs;
    regs.h.ah = 0x0E;
    regs.h.al = c;
    int86(0xA1, &regs, &regs);
}

/* INT 0xA1 con AH=0x01, CX=0: leer tecla (wait) */
int getc_bios(void) {
    union REGS regs;
    regs.h.ah = 0x01;
    regs.x.cx = 0;
    int86(0xA1, &regs, &regs);
    return regs.h.al;
}

/* Imprimir string */
void puts_bios(const char *s) {
    while (*s) {
        putc_bios(*s);
        s++;
    }
}

/* Programa principal */
void main(void) {
    /* Limpiar pantalla (imprimir form feed) */
    putc_bios(0x0C);  /* CLS */
    
    /* Posicionar cursor en línea 3, columna 4 */
    /* (usando secuencia de escape del BIOS) */
    
    /* Mostrar mensaje */
    puts_bios("=== PDT 3100 ===\r\n");
    puts_bios("\r\n");
    puts_bios("Hello World!\r\n");
    puts_bios("\r\n");
    puts_bios("Press any key...\r\n");
    
    /* Esperar tecla */
    getc_bios();
    
    /* Limpiar y salir */
    putc_bios(0x0C);
}
