## Originally copied from https://files.waveshare.com/upload/d/db/LCD1602_I2C_Module_code.zip

# -*- coding: utf-8 -*-
from time import sleep
from machine import I2C
from ulogging import uLogger
from display import driver_registry
from config import SDA_PIN, SCL_PIN, I2C_ID

#Device I2C address
LCD_ADDRESS   =  (0x7c>>1)

LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

#flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

#flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

#flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

#flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x8DOTS = 0x00

class LCD1602:
	"""Driver for the LCD1602 16x2 character LED display"""

	def __init__(self) -> None:
		"""Configure and connect to display via I2C, throw error on connection issue."""
		self.log = uLogger("LCD1602")
		self.log.info("Init LCD1602 display driver")
		self._row = 16
		self._col = 2

		try:
			self.LCD1602_I2C = I2C(I2C_ID, sda = SDA_PIN, scl = SCL_PIN, freq = 400000)
			self._showfunction = LCD_4BITMODE | LCD_1LINE | LCD_5x8DOTS
			self._begin(self._row)
		except BaseException:
			self.log.error("Error connecting to LCD display on I2C bus. Check I2C pins and ID and that correct module (I2C address) is connected.")
			raise
				
	def _command(self, cmd: int) -> None:
		"""Execute a command against the display driver. Refer to command constants."""
		self.LCD1602_I2C.writeto_mem(LCD_ADDRESS, 0x80, chr(cmd))

	def _write(self, data: int) -> None:
		self.LCD1602_I2C.writeto_mem(LCD_ADDRESS, 0x40, chr(data))

	def setCursor(self, col: int, row: int) -> None:
		"""Position the cursor ahead of writing a character or string."""
		if(row == 0):
			col|=0x80
		else:
			col|=0xc0
		self.LCD1602_I2C.writeto(LCD_ADDRESS, bytearray([0x80, col]))

	def clear(self) -> None:
		"""Clear the entire screen."""
		self._command(LCD_CLEARDISPLAY)
		sleep(0.002)
		 
	def print_startup(self, version: str) -> None:
		"""Render startup information on screen."""
		self.print_on_line(0, "S.M.I.B.H.I.D.")
		self.print_on_line(1, f"Loading: v{version}")

	def printout(self, arg: str) -> None:
		"""Print a string to the cursor position."""
		if(isinstance(arg, int)):
			arg=str(arg)

		for x in bytearray(arg, 'utf-8'):
			self._write(x)

	def _text_to_line(self, text: str) -> str:
		"""Internal function to ensure line fits the screen and no previous line text is present for short strings."""
		text = text[:16]
		text = "{:<16}".format(text)
		return text
	
	def print_on_line(self, line: int, text: str) -> None:
		"""Print up to 16 characters on line 0 or 1."""
		self.setCursor(0, line)
		self.printout(self._text_to_line(text))

	def _display(self) -> None:
		"""Turn on display."""
		self._showcontrol |= LCD_DISPLAYON 
		self._command(LCD_DISPLAYCONTROL | self._showcontrol)
	
	def print_space_state(self, state: str) -> None:
		"""Abstraction for space state formatting and placement."""
		self.print_on_line(0, "S.M.I.B.H.I.D.")
		self.print_on_line(1, f"Space: {state}")
 
	def _begin(self, lines: int) -> None:
		"""Configure and set initial display output."""
		if (lines > 1):
				self._showfunction |= LCD_2LINE 
		 
		self._numlines = lines 
		self._currline = 0 

		sleep(0.05)

		# Send function set command sequence
		self._command(LCD_FUNCTIONSET | self._showfunction)
		#delayMicroseconds(4500);  # wait more than 4.1ms
		sleep(0.005)
		# second try
		self._command(LCD_FUNCTIONSET | self._showfunction)
		#delayMicroseconds(150);
		sleep(0.005)
		# third go
		self._command(LCD_FUNCTIONSET | self._showfunction)
		# finally, set # lines, font size, etc.
		self._command(LCD_FUNCTIONSET | self._showfunction)
		# turn the display on with no cursor or blinking default
		self._showcontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF 
		self._display()
		# clear it off
		self.clear()
		# Initialize to default text direction (for romance languages)
		self._showmode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT 
		# set the entry mode
		self._command(LCD_ENTRYMODESET | self._showmode)
		# backlight init

driver_registry.register_driver("LCD1602", LCD1602)