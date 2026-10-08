/* display.h - API del display LCD para Symbol PDT 3100
 *
 * Display: 8 líneas × 20 caracteres LCD monocromático
 */

#ifndef _DISPLAY_H_
#define _DISPLAY_H_

#define DISP_ROWS 8
#define DISP_COLS 20

/* Limpiar pantalla */
void disp_clear(void);

/* Posicionar cursor (row=0-7, col=0-19) */
void disp_gotoxy(int row, int col);

/* Imprimir carácter en posición actual */
void disp_putc(char c);

/* Imprimir string en posición actual */
void disp_puts(const char *s);

/* Imprimir string en posición específica */
void disp_puts_at(int row, int col, const char *s);

/* Limpiar línea específica */
void disp_clear_line(int row);

/* Dibujar borde/box */
void disp_box(int row, int col, int height, int width);

/* Mostrar mensaje temporal (con wait) */
void disp_message(const char *s, int wait_ms);

/* Mostrar menú simple */
void disp_menu(const char *title, const char *items[], int count, int selected);

#endif /* _DISPLAY_H_ */
