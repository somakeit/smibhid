from micropython import const
from machine import I2C
from framebuf import MONO_VLSB, FrameBuffer
from time import sleep

_FRAMEBUF_FORMAT = MONO_VLSB



# register definitions
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_IREF_SELECT = const(0xAD)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)


class _SSD1306(FrameBuffer):
    """
    Base class for SSD1306 display driver
    """
    def __init__(
        self,
        buffer: memoryview,
        width: int,
        height: int,
        *,
        external_vcc: bool,
        page_addressing: bool
    ):
        super().__init__(buffer, width, height, _FRAMEBUF_FORMAT)
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.reset_pin = None
        self.page_addressing = page_addressing
        if self.reset_pin:
            self.reset_pin.switch_to_output(value=0)
        self.pages = self.height // 8
        # Note the subclass must initialize self.framebuf to a framebuffer.
        # This is necessary because the underlying data buffer is different
        # between I2C and SPI implementations (I2C needs an extra byte).
        self._power = False
        # Parameters for efficient Page Addressing Mode (typical of U8Glib libraries)
        # Important as not all screens appear to support Horizontal Addressing Mode
        if self.page_addressing:
            self.pagebuffer = bytearray(width + 1)
            self.pagebuffer[0] = 0x40  # Set first byte of data buffer to Co=0, D/C=1
            self.page_column_start = bytearray(2)
            self.page_column_start[0] = self.width % 32
            self.page_column_start[1] = 0x10 + self.width // 32
        else:
            self.pagebuffer = None
            self.page_column_start = None
        # Let's get moving!
        self.poweron()
        self.init_display()

    @property
    def power(self) -> bool:
        """True if the display is currently powered on, otherwise False"""
        return self._power

    def init_display(self) -> None:
        """Base class to initialize display"""
        # The various screen sizes available with the ssd1306 OLED driver
        # chip require differing configuration values for the display clock
        # div and com pin, which are listed below for reference and future
        # compatibility:
        #    w,  h: DISP_CLK_DIV  COM_PIN_CFG
        #  128, 64:         0x80         0x12
        #  128, 32:         0x80         0x02
        #   96, 16:         0x60         0x02
        #   64, 48:         0x80         0x12
        #   64, 32:         0x80         0x12
        for cmd in (
            SET_DISP,  # off
            # address setting
            SET_MEM_ADDR,
            0x10  # Page Addressing Mode
            if self.page_addressing
            else 0x00,  # Horizontal Addressing Mode
            # resolution and layout
            SET_DISP_START_LINE,
            SET_SEG_REMAP | 0x01,  # column addr 127 mapped to SEG0
            SET_MUX_RATIO,
            self.height - 1,
            SET_COM_OUT_DIR | 0x08,  # scan from COM[N] to COM0
            SET_DISP_OFFSET,
            0x00,
            SET_COM_PIN_CFG,
            0x02 if self.width > 2 * self.height else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV,
            0x80,
            SET_PRECHARGE,
            0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL,
            0x30,  # 0.83*Vcc  # n.b. specs for ssd1306 64x32 oled screens imply this should be 0x40
            # display
            SET_CONTRAST,
            0xFF,  # maximum
            SET_ENTIRE_ON,  # output follows RAM contents
            SET_NORM_INV,  # not inverted
            SET_IREF_SELECT,
            0x30,  # enable internal IREF during display on
            # charge pump
            SET_CHARGE_PUMP,
            0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,  # display on
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self) -> None:
        """Turn off the display (nothing visible)"""
        self.write_cmd(SET_DISP)
        self._power = False

    def contrast(self, contrast: int) -> None:
        """Adjust the contrast"""
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert: bool) -> None:
        """Invert all pixels on the display"""
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def rotate(self, rotate: bool) -> None:
        """Rotate the display 0 or 180 degrees"""
        self.write_cmd(SET_COM_OUT_DIR | ((rotate & 1) << 3))
        self.write_cmd(SET_SEG_REMAP | (rotate & 1))
        # com output (vertical mirror) is changed immediately
        # you need to call show() for the seg remap to be visible

    def write_framebuf(self) -> None:
        """Derived class must implement this"""
        raise NotImplementedError

    def write_cmd(self, cmd: int) -> None:
        """Derived class must implement this"""
        raise NotImplementedError

    def poweron(self) -> None: #TODO: Make async
        "Reset device and turn on the display."
        if self.reset_pin:
            self.reset_pin.value = 1
            sleep(0.001)
            self.reset_pin.value = 0
            sleep(0.010)
            self.reset_pin.value = 1
            sleep(0.010)
        self.write_cmd(SET_DISP | 0x01)
        self._power = True

    def show(self) -> None:
        """Update the display"""
        if not self.page_addressing:
            xpos0 = 0
            xpos1 = self.width - 1
            if self.width != 128:
                # narrow displays use centered columns
                col_offset = (128 - self.width) // 2
                xpos0 += col_offset
                xpos1 += col_offset
            self.write_cmd(SET_COL_ADDR)
            self.write_cmd(xpos0)
            self.write_cmd(xpos1)
            self.write_cmd(SET_PAGE_ADDR)
            self.write_cmd(0)
            self.write_cmd(self.pages - 1)
        self.write_framebuf()


class SSD1306_I2C(_SSD1306):
    """
    I2C class for SSD1306

    :param width: the width of the physical screen in pixels,
    :param height: the height of the physical screen in pixels,
    :param i2c: the I2C peripheral to use,
    :param addr: the 8-bit bus address of the device,
    :param external_vcc: whether external high-voltage source is connected.
    :param reset: if needed, DigitalInOut designating reset pin
    """

    def __init__(
        self,
        width: int,
        height: int,
        i2c: I2C,
        *,
        addr: int = 0x3C,
        external_vcc: bool = False,
        reset = None,
        page_addressing: bool = False
    ):
        self.i2c_device = i2c
        self.addr = addr
        self.page_addressing = page_addressing
        self.temp = bytearray(2)
        # Add an extra byte to the data buffer to hold an I2C data/command byte
        # to use hardware-compatible I2C transactions.  A memoryview of the
        # buffer is used to mask this byte from the framebuffer operations
        # (without a major memory hit as memoryview doesn't copy to a separate
        # buffer).
        self.buffer = bytearray(((height // 8) * width) + 1)
        self.buffer[0] = 0x40  # Set first byte of data buffer to Co=0, D/C=1
        super().__init__(
            memoryview(self.buffer)[1:],
            width,
            height,
            external_vcc=external_vcc,
            page_addressing=self.page_addressing,
        )

    def write_cmd(self, cmd: int) -> None:
        """Send a command to the I2C device"""
        hex = 0x80  # Co=1, D/C#=0
        self.i2c_device.writeto(self.addr, bytearray([hex, cmd])) #TODO: Gives EIO, need to review datasheet

    def write_framebuf(self) -> None:
        """Blast out the frame buffer using a single I2C transaction to support
        hardware I2C interfaces."""
        if self.page_addressing:
            for page in range(self.pages):
                self.write_cmd(0xB0 + page)
                self.write_cmd(self.page_column_start[0])
                self.write_cmd(self.page_column_start[1])
                self.pagebuffer[1:] = self.buffer[
                    1 + self.width * page : 1 + self.width * (page + 1)
                ]
                self.i2c_device.write(self.pagebuffer)
        else:
            self.i2c_device.write(self.buffer)
