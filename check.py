#!/usr/bin/env python3

from tracer import Tracer
import keithley
import time
import datetime as dt
import sys
import statistics as stats

def main(argv):

  if len(argv) < 2:
    print('Usage: check <1,2>   for R1 or R2')
    exit(0)
  if argv[1] != '1' and argv[1] != '2':
    print('Error, must specify R1 or R2')
    print('Usage: check <1,2>   for R1 or R2')
    exit(0)

  if len(argv) > 2:
    init_comms = '1' == argv[2]
  else:
    init_comms = True

  print('=== Initializing TraceR Module ===')
  Tracer.init_serial('/dev/ttyACM0')
  if init_comms:
    if not Tracer.init_comm_link():
      print('failed to initialize TraceR comm link')
      exit(0)
  tr1 = Tracer(Tracer.TR1)
  tr2 = Tracer(Tracer.TR2)

  if argv[1] == '1':
    tr = tr1 
  elif argv[1] == '2':
    tr = tr2 

  # get serial number and make filename
  tr.command(tr.IDENT)
  chkfile = 'rcheck-'+tr.ident.lower()+'-r'+tr.which+'-cal.dat'
  print('Opening:', chkfile)
  fpo = open(chkfile, 'w')
  
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


  print('=== Performing calibration check over all counts ===')
  begtime = str( dt.datetime.now() )
  print('# Began on: ', begtime )
  print('# Began on: ', begtime, file=fpo)
  for rcmd in range(0,300):

    tr.command(Tracer.OHMS, rcmd)
    print('# rcmd, ohms:', rcmd, tr.ohms)

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

    print( rcmd, 
        f'{stats.mean(ohms):.2f}', 
        f'{stats.stdev(ohms):.4f}',
        len(ohms),
        [o for o in ohms], 
           sep='\t', file = fpo )
    fpo.flush()


  endtime = str( dt.datetime.now() )
  print('# Ended on: ', endtime, file=fpo)
  print('# Began on: ', begtime )
  print('# Ended on: ', endtime )
  fpo.close()

if __name__ == "__main__":
  main(sys.argv)

