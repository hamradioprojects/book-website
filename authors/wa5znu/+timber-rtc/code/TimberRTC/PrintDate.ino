// --------------------------
// PrintDate.ino
// This file provides printdate(File), to format the date and time as a file.
// It depends on the RTC shield.

// The date format is YYYY-MM-DD HH:MM:SS
// You can change it here.
void printdate (File *out) {
  if (RTC.isrunning()) {
    DateTime now = RTC.now();
    // Date: YYYY-MM-DD
    out->print(now.year(), DEC);
    out->print('/');
    zero_pad(out, now.month());
    out->print(now.month(), DEC);
    out->print('/');
    out->print(now.day(), DEC);
    // space
    out->print(' ');
    // Time: HH:MM_SS
    zero_pad(out, now.hour());
    out->print(now.hour(), DEC);
    out->print(':');
    zero_pad(out, now.minute());
    out->print(now.minute(), DEC);
    out->print(':');
    zero_pad(out, now.second());
    out->print(now.second(), DEC);
  }
}
  
// Zero pad numbers < 10 into two digits with a leading zero.
void zero_pad(File *out, byte x) {
  if (x < 10) out->print("0");
}
