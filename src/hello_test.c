/* hello_test.c - Programa de prueba para compilar con bcc (Bruce's C Compiler)
 * 
 * Este programa usa llamadas directas al BIOS del PDT 3100 via INT 0xA1.
 * Compila a un .COM de 16-bit ejecutable en DOS.
 *
 * Compilar: bcc -o hello_test.com hello_test.c
 */

/* INT 0xA1 AH=0x0E: imprimir carácter en pantalla del PDT 3100 */
void putc_bios(char c) {
    /* En bcc (8086), usamos inline assembly para INT */
    asm volatile (
        "movb $0x0E, %%ah\n"
        "int $0xA1\n"
        : : "a"(c)
    );
}

void puts_bios(const char *s) {
    while (*s) {
        putc_bios(*s);
        s++;
    }
}

void main() {
    /* Limpiar pantalla */
    putc_bios(0x0C);
    
    /* Mensaje */
    puts_bios("=== PDT 3100 ===\r\n");
    puts_bios("Hello from C!\r\n");
    puts_bios("Press any key...\r\n");
    
    /* Esperar tecla: INT 0xA1 AH=0x01 */
    asm volatile (
        "movb $0x01, %%ah\n"
        "xorw %%cx, %%cx\n"
        "int $0xA1\n"
        : : : "ax", "cx"
    );
    
    /* Limpiar al salir */
    putc_bios(0x0C);
}
