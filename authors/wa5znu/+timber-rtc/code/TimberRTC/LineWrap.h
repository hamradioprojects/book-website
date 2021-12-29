//--------------------------------------------------
// LineWrap.h
// LCD line-wrapping code
// In your sketch, define 'lcd' variable and use #include "LineWrap.h".
// This file is written as an include file, because the type of lcd used varies, 
// so we cannot declare it as an 'extern' variable or parameter.
//--------------------------------------------------

#define LCD_COLS (16)
#define LCD_ROWS (2)

// Set to false to truncate long screens, so you see the first part.
// Set it to true to have long screenfull scroll past
#define ALLOW_LCD_SCREEN_WRAP false
#define SCREEN_WRAP_DELAY 500

byte lcdRow;
byte lcdCol;

void lcdprint(char *s) {
  lcdprint(s, strlen(s));
}

// Print specified number of characters, and wrap lines.
// If ALLOW_LCD_SCREEN_WRAP is true, wrap multiple lines
// to the next screenful; otherwise just truncate.
void lcdprint(char *s, byte n) {
  char spaceleft = LCD_COLS - lcdCol;
  if (n <= spaceleft) {
    char buf[17];
    buf[LCD_COLS] = '\0';
    strncpy(buf, s, n);
    buf[n] = '\0';
    lcd.print(buf);
    lcdCol += n;
  } else {
    lcdprint(s, spaceleft);
    setCursor(0, lcdRow + 1);
    if (lcdRow == 0) {
      if (ALLOW_LCD_SCREEN_WRAP) {
	delay(SCREEN_WRAP_DELAY);
	lcdclear();
      } else {
	return;
      }
    } 
    lcdprint(s+spaceleft, n - spaceleft);
  }
}

void lcdclear() {
  lcd.clear();
  lcdRow = 0;
  lcdCol = 0;
}

void setCursor(byte col, byte row) {
  lcdCol = col;
  lcdRow = row % LCD_ROWS;
  lcd.setCursor(lcdCol, lcdRow);
}

