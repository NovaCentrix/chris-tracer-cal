#!/usr/bin/env python3

from tracer import Tracer
import keithley
import time
import datetime as dt
import sys
import statistics as stats

def main():

  init_comms = True
  print('=== Initializing TraceR Module ===')
  Tracer.init_serial('/dev/ttyACM0')
  if init_comms:
    if not Tracer.init_comm_link():
      print('failed to initialize TraceR comm link')
      exit(0)
  tr1 = Tracer(Tracer.TR1)
  tr2 = Tracer(Tracer.TR2)

  
  print('=== Initializing Keithley 195A GPIB Multimeter ===')
  # Talking to a GPIB device 
  # connected to a remote computer running custom server
  HOST = '192.168.1.37'  # The server's hostname or IP address
  PORT = 65432        # The port used by the server
  device = keithley.Remote_device( HOST, PORT )
  # open the meter device
  dmm = keithley.K195A(device) 

  dmm.clear()
  time.sleep(0.100)

  status = dmm.query('U0DX').strip()
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

  status = dmm.query('U0DX').strip()
  print('status:', status)
  print('Waiting for the Keithley meter...', end='')
  sys.stdout.flush()
  reply = dmm.query('')
  print(" okay, let's go!")

  fpo = open('caldata.txt', 'w')

  print('=== Performing calibration over all counts ===')
  print(dt.datetime.now())
  print('# Began on: ', dt.datetime.now(), file=fpo)
  tr = tr2
  for count in range(257):

    if count == 256:
      tr.command(Tracer.COUNTS, 0)
      tr.command(Tracer.RELAYS, 1)
      print('# counts: relay shunted')
      time.sleep(1.0)
    else: 
      tr.command(Tracer.COUNTS, count)
      print('# counts:', tr1.counts)

    ohms = []
    for loop in range(10):
      reply = dmm.query('')
      # qualify the reply...
      # NOHM+0.01198E+3
      ok_len = len(reply) >=7
      if len(reply) >= 7:
        prefix = reply[0]
        mode = reply[1:4]
        value = reply[4:].strip()
        ok_prefix = prefix == 'N'
        ok_mode = mode == 'OHM'
        if ok_len and ok_prefix and ok_mode:
          reading = float(value)
          print('# Resistance', prefix, mode, value, reading )
          ohms.append( reading )
        else:
          ohms = 0.0
          print('# Bad format:', prefix, mode, value )
      else:
        print('# Error:', reply )

    print( count, 
        f'{stats.mean(ohms):.2f}', 
        f'{stats.stdev(ohms):.4f}',
        len(ohms),
        [o for o in ohms], 
           sep='\t', file = fpo )
    fpo.flush()

    if count == 256:
      tr.command(Tracer.RELAYS, 0)
      time.sleep(1.0)

  print(dt.datetime.now())
  print('# Ended on: ', dt.datetime.now(), file=fpo)
  fpo.close()

if __name__ == "__main__":
  main()

