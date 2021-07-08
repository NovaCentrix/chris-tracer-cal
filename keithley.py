#!/usr/bin/env python3

import sys
import socket
#import pyvisa
import time
import struct
from enum import Enum, IntEnum

class K195A:

  power_up_command = 'T6F0R6K0Q00S2M0Z0W1A0J0G4B0P2Y\r\nX'
  power_up_mode =  '195 6060002000100402=:\r\n'

  class Mode(IntEnum):
      voltage_dc = 0
      voltage_ac = 1
      resistance = 2
      current_dc = 3
      current_ac = 4

  class TriggerMode(IntEnum):
      talk_continuous = 0
      talk_one_shot = 1
      get_continuous = 2
      get_one_shot = 3
      x_continuous = 4
      x_one_shot = 5
      ext_continuous = 6
      ext_one_shot = 7

  class ValidRange(Enum):
      voltage_dc = (20e-3, 200e-3, 2, 20, 200, 1000)
      voltage_ac = (20e-3, 200e-3, 2, 20, 200, 700)
      current_dc = (20e-6, 200e-6, 2e-3, 20e-3, 200e-3, 2)
      current_ac = (20e-6, 200e-6, 2e-3, 20e-3, 200e-3, 2, 2)
      resistance = (20, 200, 2000, 20e3, 200e3, 2e6, 20e6)

  def __init__(self, instrument, interface=None):
    self.dev = instrument
    self.ctl = interface
    self.dev.timeout = 6000
    self.status_word = ''

  def write(self,val):
    return self.dev.write(val)

  def read(self):
    return self.dev.read()

  def query(self,val):
    return self.dev.query(val)

  def status(self):
    self.status_word = self.dev.query('U0DX')
    return self.status_word

  def clear(self):
    self.dev.clear()
    return 'DCL'

  def close(self):
    pass
   

  def parse_status_word(self,sw):
      """
      Returns a `dict` with the following keys:
      ``{trigger,mode,range,eoi,buffer,rate,srqmode,relative,delay,multiplex,
      selftest,dataformat,datacontrol,filter,terminator}``

      :param statusword: Byte string to be unpacked and parsed
      :type: `str`

      :return: A parsed version of the status word as a Python dictionary
      :rtype: `dict`
      """
      statusword = bytes(sw, 'ascii')

      if statusword[:3] != b'195':
          raise ValueError('Status word starts with wrong prefix, expected '
                           '195, got {}'.format(statusword))

      (trigger, function, input_range, eoi, buf, rate, srqmode, relative,
       delay, multiplex, selftest, data_fmt, data_ctrl, filter_mode,
       terminator) = struct.unpack('@4c2s3c2s5c2s', statusword[4:])

      return {'trigger': K195A.TriggerMode(int(trigger)),
              'mode': K195A.Mode(int(function)),
              'range': int(input_range),
              'eoi': (eoi == b'1'),
              'buffer': buf,
              'rate': rate,
              'srqmode': srqmode,
              'relative': (relative == b'1'),
              'delay': delay,
              'multiplex': (multiplex == b'1'),
              'selftest': selftest,
              'dataformat': data_fmt,
              'datacontrol': data_ctrl,
              'filter': filter_mode,
              'terminator': terminator}

class Remote_device:

  def __init__(self, host, port, verbose=True):
    self.host = host
    self.port = port
    self.verbose = None
    self.sock = None
    self.connect(host, port)
    self.timeout = 0 #TBD not used now
  
  def connect(self, host, port):
    self.host = host
    self.port = port
    self.sock = None
    while True:
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.settimeout(2.00)
      try:
        self.sock.connect((self.host, self.port))
      except socket.timeout as e:
        err = e.args[0]
        print(e)
        print('timed out, trying again in 2 seconds')
        time.sleep(2)
        continue
      except socket.error as e:
        print('error, trying again in 10 seconds')
        print(e)
        time.sleep(10)
        continue
      else:
        break
    #s.setblocking(True)
    self.sock.settimeout(11.000)

  def sock_write(self, message):
    self.sock.sendall(message)

  def sock_read(self):
    buff=b''
    try: 
      buff = self.sock.recv(1024)
    except socket.timeout as e:
      err = e.args[0]
      if err == 'timed out':
        # we don't care if it times out
        print('timed out')
        pass
      else:
        print(e)
    return buff

  def read(self):
    message = 'R'
    self.sock_write(message.upper().encode())
    return str( self.sock_read()[2:], 'ascii' )

  def write(self, command):
    message = 'W'+command
    self.sock_write(message.upper().encode())
    return int(self.sock_read()[2:])

  def query(self, command):
    message = 'Q'+command
    self.sock_write(message.upper().encode())
    return str( self.sock_read()[2:], 'ascii' )

  def clear(self):
    message = 'C'
    self.sock_write(message.upper().encode())
    return str( self.sock_read()[2:], 'ascii' )

def get_meter(local=False):
  instrument = None
  interface = None
  dmm = None
  # Use this method if talking to a GPIB device 
  # directly connected to this computer
  if local:
    rm = pyvisa.ResourceManager()
    instrument = rm.open_resource('GPIB0::5::INSTR')
    interface = rm.open_resource('GPIB0::INTFC')

  # Use this method if talking to a GPIB device 
  # connected to a remote computer running custom server
  if not local:
    HOST = '192.168.1.37'  # The server's hostname or IP address
    PORT = 65432        # The port used by the server
    instrument = Remote_device( HOST, PORT )
  # open the meter device
  if instrument is not None:
    dmm = K195A(instrument, interface) 

  return dmm

def meter_test(dmm=None):
  if dmm is None:
    dmm = get_meter()

  dmm.clear()
  time.sleep(0.100)

  status = dmm.query('U0DX')
  print('status:', status)

  dmm.write('F2X')
  time.sleep(3.0)

  dmm.write('R3X')
  time.sleep(0.1)
  dmm.write('P2X')
  time.sleep(0.1)
  dmm.write('S2X')
  time.sleep(0.1)
  dmm.write('T0X')
  time.sleep(0.1)

  status = dmm.query('U0DX')
  print('status:', status)

  print('Starting the loop')

  for _ in range(5):
    reply = dmm.query('')
    prefix = reply[0]
    mode = reply[1:4]
    value = reply[4:].strip()
    ohms = float(value)
    print(prefix, mode, value, ohms)

####  status = dmm.status().strip()
####  print('status:', status)
####
####  sw = dmm.parse_status_word(status)
####  print(sw)
####
####  return dmm


# U0 Status Word breakdown:
# '195 TFRKQQSMZWWAJGBPYY'

# Default status word at power up
# '195 TFRKQQSMZWWAJGBPYY'
# '195 6060002000100402=:\r\n'
#      ||||| |||| ||||||
#      ||||| |||| ||||| \__> Y=: corresponds to CR/LF terminator
#      ||||| |||| |||| \___> P2	Used with 5% digit resolution mode
#      ||||| |||| ||| \____> B0	Readings from A/D converter
#      ||||| |||| || \_____> G4	Reading with prefix, without suffix
#      ||||| |||| | \______> J0	Self-test status cleared
#      ||||| ||||  \_______> A0	Multiplex enabled
#      ||||| ||| \_________> W01 delay period 1 ms
#      ||||| || \__________> Z0	Zero disabled
#      ||||| | \___________> M0	SRQ Mode Disabled
#      |||||  \____________> S2	Line cycle integration; 2 reading samples averaged, 4-1/2 digits
#      |||| \______________> Q00 control buffer recycling mode (0), fill rate (0)
#      ||| \_______________> KO	EOI enabled
#      || \________________> R6	1000V
#      | \_________________> F0	DC Volts
#       \__________________> T6	Continuous on external
#
# Therefore, the following string will return the meter
# approximately to it's default power-up state
#
# 'T6F0R6K0Q00S2M0Z0W1A0J0G4B0P2Y\r\nX'


