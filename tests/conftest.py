'''
Mockups of hardware specific modules
Create classes and functions in modules to mock
Create sys objects for the modules
Populate the new modules with the classes and functions
Insert the new modules in the sys.modules dictionary
'''

import sys
import os
import asyncio
import errno
import socket
import time
import binascii
import types
import json
import struct

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Define classes and functions to be mocked in testing
class Pin:
    IN = 0 # type: int
    OUT = 1 # type: int
    PULL_DOWN = 2 # type: int
    PULL_UP = 1 # type: int

    def __init__(self, id: int|str, /, mode: int = IN, pull: int = PULL_UP) -> None:
        pass
    
    def off(self) -> None:
        """
        Sets the pin to be off.
        """
        pass

    def on(self) -> None:
        """
        Sets the pin to be on.
        """
        pass
    
    def toggle(self) -> None:
        """
        Sets the pin to high if it's currently low, and vice versa.
        """
        pass
    
class I2C:
    def __init__(self, id: int, sda, scl, freq: int):
        pass

    def scan(self):
        pass

class PWM:
    """
    Pulse width modulation (PWM), allows you to give analogue behaviours to digital
    devices, such as LEDs. This means that rather than an LED being simply on or
    off, you can control its brightness.

    Example usage::

       from machine import PWM

       pwm = PWM(pin)          # create a PWM object on a pin
       pwm.duty_u16(32768)     # set duty to 50%

       # reinitialise with a period of 200us, duty of 5us
       pwm.init(freq=5000, duty_ns=5000)

       pwm.duty_ns(3000)       # set pulse width to 3us

       pwm.deinit()
    """

    def __init__(self, pin: Pin):
        """
        Construct and return a new PWM object using the following parameters:

           - *pin* should be the pin to use.
        """
        pass

    def freq(self, frequency: int|None=...):
        """
        With no arguments the frequency in Hz is returned.

        With a single *value* argument the frequency is set to that value in Hz.  The method may raise a ``ValueError`` if the frequency is outside the valid range.
        """
        pass

    def duty_u16(self, duration: int|None=...):
        """
        Get or Set the current duty cycle of the PWM output, as an unsigned 16-bit value in the range 0 to 65535 inclusive.

        With no arguments the duty cycle is returned.

        With a single *value* argument the duty cycle is set to that value, measured as the ratio ``value / 65535``.
        """
        pass

class RTC:
    """
    Real Time Clock (RTC) class to manage date and time.
    """

    def __init__(self):
        self.datetime = (2023, 10, 1, 0, 0, 0, 0, 0)  # Default date and time

    def datetime(self, dt=None):
        if dt is not None:
            self.datetime = dt
        return self.datetime

class SPI:
    """
    SPI class to manage SPI communication.
    """

    def __init__(self, id: int, sck, mosi, miso):
        self.id = id
        self.sck = sck
        self.mosi = mosi
        self.miso = miso

    def init(self, baudrate=1000000, polarity=0, phase=0):
        pass

    def read(self, nbytes: int):
        return bytes(nbytes)

    def write(self, data: bytes):
        pass

class WLAN():
    def __init__(self, interface) -> None:
        pass

    def config(self, item: str) -> bytes:
        return bytes(0)
    
    def active(self, mode: bool):
        pass

    def connect(self, ssid: str, password: str):
        pass

    def status(self):
        return 3
    
    def ifconfig(self):
        config = ["192.168.1.100"]
        return config

def mock_collect():
    # Simulate successful garbage collection
    return None

def mock_mem_free():
    # Simulate returning free memory in bytes
    return 1024 * 1024

def rp2_country(id: str):
    return 0

# build mocked modules for testing using functions and classes above
machine = types.ModuleType('machine')
setattr(machine, 'Pin', Pin)
setattr(machine, 'I2C', I2C)
setattr(machine, 'PWM', PWM)
setattr(machine, 'RTC', RTC)
setattr(machine, 'SPI', SPI)

network = types.ModuleType('network')
setattr(network, 'WLAN', WLAN)
setattr(network, 'STA_IF', 0)

gc = types.ModuleType('gc')
setattr(gc, 'collect', mock_collect)
setattr(gc, 'mem_free', mock_mem_free)

rp2 = types.ModuleType('rp2')
setattr(rp2, 'country', rp2_country)

# Insert mocked modules into testing environment
sys.modules['machine'] = machine
sys.modules['uasyncio'] = asyncio
sys.modules['uos'] = os
sys.modules['uerrno'] = errno
sys.modules['usocket'] = socket
sys.modules['utime'] = time
sys.modules['network'] = network
sys.modules['rp2'] = rp2
sys.modules['ubinascii'] = binascii
sys.modules['gc'] = gc
sys.modules['ujson'] = json
sys.modules['ustruct'] = struct

# Ensure asyncio.core is available as a dummy module
asyncio_core = types.ModuleType('asyncio.core')
sys.modules['asyncio.core'] = asyncio_core

def mock_ticks_ms():
    # Return a fake millisecond tick count
    return int(time.time() * 1000)

setattr(time, 'ticks_ms', mock_ticks_ms)

# If you want to be extra safe, also ensure 'time' is in sys.modules
sys.modules['time'] = time

def mock_statvfs(path):
    # Return a dummy statvfs result (tuple of 10 integers, as per Python docs)
    # (f_bsize, f_frsize, f_blocks, f_bfree, f_bavail, f_files, f_ffree, f_favail, f_flag, f_namemax)
    return (4096, 4096, 100000, 80000, 80000, 10000, 8000, 8000, 0, 255)

setattr(os, 'statvfs', mock_statvfs)

def mock_uname():
    # Return a dummy object with typical uname attributes
    class Uname:
        sysname = "mockos"
        nodename = "mocknode"
        release = "1.0"
        version = "mockversion"
        machine = "mockmachine"
        def __iter__(self):
            return iter((self.sysname, self.nodename, self.release, self.version, self.machine))
        def __getitem__(self, idx):
            return (self.sysname, self.nodename, self.release, self.version, self.machine)[idx]
        def __repr__(self):
            return f"(sysname='{self.sysname}', nodename='{self.nodename}', release='{self.release}', version='{self.version}', machine='{self.machine}')"
    return Uname()

setattr(os, 'uname', mock_uname)

# Create a mock micropython module
micropython = types.ModuleType('micropython')

def mock_const(x):
    return x

setattr(micropython, 'const', mock_const)

# Insert into sys.modules so 'from micropython import const' works
sys.modules['micropython'] = micropython
