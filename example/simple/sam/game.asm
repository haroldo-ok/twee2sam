;==============================================================
; WLA-DX banking setup
;==============================================================
.memorymap
	defaultslot     0
	; rom area
	slotsize        $4000
	slot            0       $0000
	slot            1       $4000
	slot            2       $8000
	; ram area
	slotsize        $2000
	slot            3       $C000
	slot            4       $E000
.endme

.rombankmap
	bankstotal 32
	banksize $4000
	banks 32
.endro

;==============================================================
; SDSC tag and SMS rom header
;==============================================================
.sdsctag 0.02,"S.A.M. - Simple Adventure Maker","Version 0.02 - Multi-script and sound support","Haroldo O. Pinheiro"

;==============================================================
; S.A.M. Includes
;==============================================================
.include "..\..\..\sam\lib\Useful functions.inc"
.include "..\..\..\sam\lib\SAM_Interpreter.asm"
.include "..\..\..\sam\lib\math.asm"
.include "..\..\..\sam\lib\joypad.asm"
.include "..\..\..\sam\lib\sam_jumptable.asm"
.include "..\..\..\sam\lib\sam_instructions.asm"
.include "..\..\..\sam\lib\sprite.asm"
.include "..\..\..\sam\lib\resource.asm"
.include "..\..\..\sam\lib\Phantasy Star decompressors.inc"

.section "PSGMOD Code" FREE
	.include "..\..\..\sam\lib\psgmod.inc"
	.include "..\..\..\sam\lib\psgmod.asm"
.ends

.section "Data" FREE
    PaletteData:
    .db $00,$3f ; Black, White
    PaletteDataEnd:

	FontData:
	  .include "..\..\..\sam\lib\BBC Micro font.inc"
.ends

.include "Script.list.txt.inc"
.include "Music.list.txt.inc"

.slot 0
.include "Images.txt.inc"

.SLOT 2
.section "PSGMOD Vibrato" SUPERFREE
PSGMOD_VIBRATO_TABLES:
  .incbin "..\..\..\sam\lib\psgmod.vib"
.ends
