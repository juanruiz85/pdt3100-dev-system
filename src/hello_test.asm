; hello_test.asm - Programa "Hello World" para Symbol PDT 3100
;
; Ensamblar: nasm -f bin -o hello_test.com hello_test.asm
;
; Usa INT 0xA1 (BIOS del PDT 3100):
;   AH=0x0E, AL=char: imprimir carácter en pantalla
;   AH=0x01, CX=0: leer tecla (wait)
;
; El .COM se carga en CS:0x0100 (estándar DOS .COM)

org 0x100          ; Los .COM empiezan en 0x100

start:
    ; Limpiar pantalla
    mov al, 0x0C          ; Form feed = CLS
    call putc

    ; Imprimir "=== PDT 3100 ===\r\n"
    mov si, msg1
    call puts

    ; Imprimir "Hello from NASM!\r\n"
    mov si, msg2
    call puts

    ; Imprimir "Press any key...\r\n"
    mov si, msg3
    call puts

    ; Leer tecla: INT 0xA1 AH=0x01 CX=0
    mov ah, 0x01
    xor cx, cx
    int 0xA1

    ; Limpiar pantalla
    mov al, 0x0C
    call putc

    ; Salir al DOS
    mov ax, 0x4C00
    int 0x21

; ===== Subrutinas =====

; putc: imprimir carácter en AL
putc:
    push ax
    mov ah, 0x0E
    int 0xA1
    pop ax
    ret

; puts: imprimir string en DS:SI (terminado en $)
puts:
    push ax
    push si
.puts_loop:
    lodsb                   ; cargar byte de [SI] en AL, SI++
    cmp al, '$'             ; fin de string?
    je .puts_done
    mov ah, 0x0E
    int 0xA1
    jmp .puts_loop
.puts_done:
    pop si
    pop ax
    ret

; ===== Datos =====
msg1: db 0x0C, '=== PDT 3100 ===', 0x0D, 0x0A, '$'
msg2: db 'Hello from NASM!', 0x0D, 0x0A, '$'
msg3: db 'Press any key...', 0x0D, 0x0A, '$'
