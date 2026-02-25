from RPLCD.i2c import CharLCD

class I2CLCD:
    def __init__(self, cols=16, rows=2, i2c_addr="0x27"):
        self.cols = cols
        self.rows = rows
        address = int(str(i2c_addr), 16)

        self._lcd = CharLCD(
            i2c_expander='PCF8574',
            address=address,
            port=1,
            cols=self.cols,
            rows=self.rows,
            charmap='A02',
            auto_linebreaks=True
        )

    def clear(self):
        self._lcd.clear()

    def write_lines(self, line1: str, line2: str = ""):
        self._lcd.clear()
        self._lcd.write_string((line1 or "")[: self.cols])
        if self.rows > 1:
            self._lcd.crlf()
            self._lcd.write_string((line2 or "")[: self.cols])