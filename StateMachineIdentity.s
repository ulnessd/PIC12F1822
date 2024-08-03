
; PIC12F1822 Configuration Bit Settings

; Assembly source line config statements

; CONFIG1
  CONFIG  FOSC = INTOSC         ; Oscillator Selection (INTOSC oscillator: I/O function on CLKIN pin)
  CONFIG  WDTE = OFF            ; Watchdog Timer Enable (WDT disabled)
  CONFIG  PWRTE = OFF           ; Power-up Timer Enable (PWRT disabled)
  CONFIG  MCLRE = OFF            ; MCLR Pin Function Select (MCLR/VPP pin function is MCLR)
  CONFIG  CP = OFF              ; Flash Program Memory Code Protection (Program memory code protection is disabled)
  CONFIG  CPD = OFF             ; Data Memory Code Protection (Data memory code protection is disabled)
  CONFIG  BOREN = ON            ; Brown-out Reset Enable (Brown-out Reset enabled)
  CONFIG  CLKOUTEN = OFF        ; Clock Out Enable (CLKOUT function is disabled. I/O or oscillator function on the CLKOUT pin)
  CONFIG  IESO = OFF            ; Internal/External Switchover (Internal/External Switchover mode is disabled)
  CONFIG  FCMEN = OFF           ; Fail-Safe Clock Monitor Enable (Fail-Safe Clock Monitor is disabled)

; CONFIG2
  CONFIG  WRT = OFF             ; Flash Memory Self-Write Protection (Write protection off)
  CONFIG  PLLEN = ON            ; PLL Enable (4x PLL enabled)
  CONFIG  STVREN = OFF          ; Stack Overflow/Underflow Reset Enable (Stack Overflow or Underflow will cause a Reset)
  CONFIG  BORV = LO             ; Brown-out Reset Voltage Selection (Brown-out Reset Voltage (Vbor), low trip point selected.)
  CONFIG  DEBUG = OFF           ; In-Circuit Debugger Mode (In-Circuit Debugger disabled, ICSPCLK and ICSPDAT are general purpose I/O pins)
  CONFIG  LVP = ON              ; Low-Voltage Programming Enable (Low-voltage programming enabled)

// config statements should precede project file includes.
#include <xc.inc>
  

PSECT resetVect, class=CODE, delta=2
resetVect:
    PAGESEL main
    goto main
    
    
PSECT code, delta=2
 
main:
    BANKSEL OSCCON ; move to the bank OSCCON is on (Bank1)
    clrf OSCCON
    movlw 0b01101011 ; this sets the oscillator to 4 MHz see page 65 to change
    movwf OSCCON
    BANKSEL PORTA ; move to the bank PORTA is on (Bank0)
    clrf PORTA ; clear PORTA for good measure
    BANKSEL LATA ; Move to the the bank LATA is on (bank 2)
    clrf LATA ; clear LATA for digital I/O
    
  
    BANKSEL ANSELA ; move to the bank ANSELA is on (bank3)
    clrf ANSELA ; clear ANSEL 
    ;bsf ANSELA, 0 ;sets RA0 to analog 
    BANKSEL TRISA ; Move to the bank TRISA is on (bank 1) 
    movlw 0b00101000 ; seting the RA0 - RA5 pins (0 output, 1 input, note not GPx)
    movwf TRISA
    
    ;UART setup
    BANKSEL BAUDCON ; move to bank 3 note this is also the bank for the other URART registers
    movlw 0b00000000 ; this will not use SBPRGH
    movwf 0x19C ; this is SBPRGH
    
    movlw 0b11001111; this will use a factor of 207 to set baud rate see page 282
    movwf 0x19B ; this is SBPRGL
    bcf BAUDCON, 3 ; this clears BRG16
    
    ;assigning the pins
    BANKSEL APFCON
    bsf APFCON, 2 ; sets RA4 as TX page 114
    bsf APFCON, 7 ; sets RA5 as RX page 114
    
    ;transmit setup also need RCSTA, 7 set
    BANKSEL TXSTA
    bsf TXSTA, 5 ; this sets TXEN --- UART transmission enabled
    bcf TXSTA, 2 ; this clears BRGH
    bcf TXSTA, 4 ; this clears SYNC---asynchronous transmission mode
    bcf TXSTA, 6 ; this clears TX9---8 bits not 9 per word
    
    ;receive setup. Aslo need SYNC cleared
    BANKSEL RCSTA
    bsf RCSTA, 7 ; serial ports enabled SPEN bit
    bcf RCSTA, 6 ; 8 bit reception RX9 bit
    bsf RCSTA, 4 ; enables reciever CREN bit


 
startloop: ;this loops waiting for the start of the process
      ; Indicate start of the program with LED on RA0
    BANKSEL PORTA 
    bsf RA0
    BANKSEL PIR1
    btfss PIR1, 5    ; Check if RCIF is set
    goto startloop       ; If not, keep checking
    BANKSEL RCREG 
    movf RCREG, 0 ; needed to clear the RCIF!!
    
    BANKSEL PORTA
    bcf RA0
    clrf 0x020 ; start in state 0 

    
init_INDF0:    
    ; Initialization of indirect file referencing
    movlw 0x20 ; Set starting address 0x120 (lower byte)
    movwf FSR0L
    movlw 0 ; First state is label 0 then 1, 2 etc
    movwf 0x050 ; register that will carry the value of current state in the storeloop
    movlw 4 ; Number of elements in state set
    movwf 0x051 ;iteration register
    clrf INDF0 ; Precautionary clearing of INDF

storeloop:
    ; Store the state set data in memory
    movf 0x050, 0 ; Move data value to WREG
    movwf INDF0 ; Store data value to the address pointed by FSR0L
    incf 0x050, 1 ; Increment data value for the next iteration
    incf FSR0L, 1 ; Increment FSR0L to point to the next address
    decfsz 0x051, 1 ; Decrement the loop counter
    goto storeloop ; Repeat the loop

   
mainloop: ;this loops will the game is in progress
    nop

waitloop: ;this loop waits for the next bit from the computer
    BANKSEL PORTA 
    bsf RA1
    BANKSEL PIR1
    btfss PIR1, 5    ; Check if RCIF is set
    goto waitloop       ; If not, keep checking
    BANKSEL PORTA
    bcf RA1
    
    BANKSEL RCREG
    movf RCREG, 0 ; moves the bit into the working register
 
       ; Finding the state 
    BANKSEL PORTA
    movwf 0x030 ; register that carries the state to match
    movlw 4 ; this will give 4 iterations through the loop 
    movwf 0x031 ;iteration register

    
    movlw 0x020 ; Reset to the starting address 0x020
    movwf FSR0L    
match_loop:
    movf INDF0, 0 ; moves the value at addess FRS0L to working register
    movwf 0x040 ; stores the value from working register
    movf 0x030, 0 ; moves the matching target state to working register
    subwf 0x040, 0 ; subtracts target state from the inspected state 
    btfsc STATUS, 2 ; Check if the subtraction yields 0. then that is a match
    goto foundmatch ; If not set, loop here indefinitely
    incf FSR0L, 1 ; Increment FSR0L to point to the next address THIS IS WORKING CHECK decfsz 0x031
    decfsz 0x031, 1 ; reduces iterator
    goto match_loop
    goto errorhandler ; switch this to error handler later

foundmatch:
    BANKSEL PORTA
    movf INDF0, 0
    
        ;this part is for transmitting back the current state
    BANKSEL PIR1
    btfss PIR1, 4    ; Check if TXREG is empty
    goto $-1       ; If not, keep checking
 
  
    BANKSEL TXREG
    movwf TXREG ; transmits the current parity to the computer
    nop
    goto mainloop
    movlw 20 ; short delay between transmissions
    call delay
    nop


errorhandler:
    BANKSEL PORTA
    movlw 8
    
        ;this part is for transmitting back the current state
    BANKSEL PIR1
    btfss PIR1, 4    ; Check if TXREG is empty
    goto $-1       ; If not, keep checking
 
  
    BANKSEL TXREG
    movwf TXREG ; transmits the current state to the computer
    nop
    
    movlw 20 ; short delay between transmissions
    call delay
    nop
    goto mainloop    

delay: ; this is a three-layer nested loop. wouldn't need 3 but it is what I had 
	; from other programs
    movwf 0xB2
out_out_loop:
    movwf 0xB1
outer_loop:
    movwf 0xB0
delay_loop:
    decfsz 0xB0, 1
    goto delay_loop
    decfsz 0xB1, 1
    goto outer_loop
    decfsz 0xB2, 1
    goto out_out_loop
    retlw 0 ; the return sets the working register to zero. 
    nop       
    
END resetVect   
