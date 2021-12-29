extern void lcdbegin();
extern byte lcdRow;
extern byte lcdCol;
extern void lcdprint(char *s);
extern void lcdprint(char *s, byte n);
extern void lcdclear();
extern void lcdcolor(byte color);
extern void setCursor(byte col, byte row);
