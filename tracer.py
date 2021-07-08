#!/usr/bin/env python3
import serial
from time import sleep
from datetime import datetime, timedelta

class Tracer:
  TR1 = '1'
  TR2 = '2'
  COUNTS = 'X'
  RELAYS = 'K'
  OHMS = 'R'
  ASSIGN = '='
  QUERY = '?'
  END = '\n'
  ser = None
  port = None

  @classmethod
  def init_serial(cls,port):
    if cls.ser is None:
      cls.port = port
      cls.ser = serial.Serial( Tracer.port,
                     baudrate = 115200,
                     stopbits = serial.STOPBITS_ONE,
                     bytesize = serial.EIGHTBITS,
                     writeTimeout = 0,
                     timeout = 0.250,
                     rtscts = False,
                     dsrdtr = False )

  @classmethod
  def init_comm_link(cls):
    """Sends ctrl-C and ctrl-D to soft reboot"""
    cls.ser.reset_input_buffer()
    cls.ser.write(b'\x03')
    sleep(1.0)
    buff = str(cls.ser.read(1024).decode('ascii'))
    if buff.endswith('\r\n>>> '):
      print('TraceR Module, Ctrl-C successful')
    else:
      print('TraceR Module, Ctrl-C unsuccessful, buff:')
      print(buff)
      return False
    cls.ser.write(b'\x04')
    sleep(4.0)
    buff = str(cls.ser.read(1024).decode('ascii'))
    if buff.endswith('soft reboot\r\n\r\n> '):
      print('TraceR Module, soft reboot successful')
    else:
      print('TraceR Module, soft reboot unsuccessful, buff:')
      print(buff)
      return False
    return True

  def __init__(self, which):
    self.which=which
    self.counts=0
    self.relay=0
    self.ohms=0

  def __repr__(self):
    return f'{self.which}: {self.counts}.{self.relay} = {self.ohms}'

  def parse_reply(self,reply):
    #print('parsing reply:', reply)
    lines = reply.split('\n')
    #print('lines:', lines)
    echo = lines[0].strip()
    status = lines[1].strip()
    fields = status.split(' ')
    for f in fields: 
      #print('f:', f)
      key,val = f.split('=')
      param=key[0]
      which=key[1]
      #print('broken:', key, param, which, val)
      #print('which compare:', which, self.which)
      #print('param:', param)
      #print('value:', val)
      if param == Tracer.COUNTS:
        #print('param matched counts')
        self.counts = int(val)
      elif param == Tracer.RELAYS:
        #print('param matched relays')
        self.relay = val
      elif param == Tracer.OHMS:
        #print('param matched ohms')
        self.ohms = int(val)
      else:
        #print('param matched nothing')
        pass


  def command(self, param, value=None):
    cmd_string = param + self.which
    if value is None:
      cmd_string += Tracer.QUERY + Tracer.END
      self.ser.write( bytes(cmd_count.encode('ascii')) )
    else:
      cmd_string += Tracer.ASSIGN + str(value) + self.END
      self.ser.write( bytes(cmd_string.encode('ascii')) )

    # print(cmd_string)
    reply = str(Tracer.ser.read(1024).decode('ascii'))
    # print(reply)
    self.parse_reply(reply)

def testme():
  Tracer.init_serial('/dev/ttyACM0')
  if not Tracer.init_comm_link():
    print('failed to initialize comm link')
    exit(0)
  tr1 = Tracer(Tracer.TR1)
  tr2 = Tracer(Tracer.TR2)
  # tr.parse_reply('X1=0\r\nX1=0 K1=open\r\n> ')
  tr1.command(Tracer.COUNTS, 55)
  print(tr1.counts)
  return [tr1, tr2]

  # 'X1=0\r\nX1=0 K1=open\r\n> '
  # 'X1=1\r\nX1=1 K1=open\r\n> '
  # 'X1=2\r\nX1=2 K1=open\r\n> '
  # 'X1=3\r\nX1=3 K1=open\r\n> '
