#!/usr/bin/env python

import sys
import csv
from operator import itemgetter

class Settings:
  def __init__( self, rnom, ract, rerr, regs ):
    self.rnom = rnom
    self.ract = ract
    self.rerr = rerr
    self.regs = regs
  def __str__(self):
    return '{s.rnom:.1f}\t'\
           '{s.regs[0]}\t{s.regs[1]}\t{s.regs[2]}\t{s.regs[3]}\t'\
           '{s.ract:.3f}\t{s.rerr:+.3f}'.format(s=self)
  def __repr__(self):
    return '{s.rnom:.1f}\t'\
           '{s.regs[0]}\t{s.regs[1]}\t{s.regs[2]}\t{s.regs[3]}\t'\
           '{s.ract:.3f}\t{s.rerr:+.3f}'.format(s=self)

class Calib:
  def __init__( self, counts, ohms, stdev, nsamples, samples ):
    self.counts = counts
    self.ohms = ohms
    self.stdev = stdev
    self.nsamples = nsamples
    self.samples = samples
  def __str__(self):
    return '{s.counts} {s.ohms}'.format(s=self)
  def __repr__(self):
    return '{s.counts} {s.ohms}'.format(s=self)

def show_help():
  print('Usage:')
  print('inverse [calibration-data-file]')
  print('Where:')
  print('  calibration-data-file   data saved by cal.py calibration run')

#   0    12.00    0.0079 10    [12.01, 12.01, 12.01, 12.01, 12.0, 12.0, 12.0, 12.0, 11.99, 11.99]
#   1    13.61    0.0042 10    [13.6, 13.6, 13.61, 13.61, 13.61, 13.61, 13.61, 13.61, 13.61, 13.61]
#   2    14.57    0.0052 10    [14.56, 14.56, 14.56, 14.56, 14.57, 14.57, 14.57, 14.57, 14.57, 14.57]
#   3    15.80    0.0000 10    [15.8, 15.8, 15.8, 15.8, 15.8, 15.8, 15.8, 15.8, 15.8, 15.8]

def calibration_read(fname):
  calib=[]
  with open(fname, 'r') as fin:
    reader = csv.reader(fin, delimiter='\t')
    npoints=0
    for row in reader:
      #print(type(row), len(row), row)
      if row[0][0] == '#': continue
      counts = int(row[0])
      ohms = float(row[1])
      stdev = float(row[2])
      nsamples = int(row[3])
      data = []
      calib.append( Calib( counts, ohms, stdev, nsamples, data ))
      npoints += 1
      #if npoints >= 3: break
  return calib

def main( argv ):
  verbose = False

  if len(argv) < 2:
    show_help()
    exit(0)

  calib = calibration_read( argv[1] )


  DELTA = 0.25

  settings = []
  # zero ohms case is special, relay is engaged, 
  # result from calibration stored at 256
  rnom = 0
  regs = [0,0,0,0]
  radj = calib[-1].ohms
  rerr = radj
  settings.append(Settings( rnom, radj, rerr, regs ))

  rbeg = None
  rend = None
  nresistances = 0

  for rnom in range(1,300):
    lo = None
    hi = None
    c0 = calib[0]
    for c in calib[1:-1]:
      if rnom > c0.ohms and rnom <= c.ohms:
        lo=c0
        hi=c
        break
      c0 = c

    if lo is not None and hi is not None:
      # save beg and end for summary
      if rbeg is None: rbeg = rnom
      rend = rnom
      nresistances += 1
      # calculate the distance from rnom to each endpoint
      dlo = rnom - lo.ohms
      dhi = hi.ohms - rnom
      # 1.  adjust lo counts by 0, +1, +2, or +3
      # 2.  adjust hi counts by 0, -1, -2, or -3
      errlo = []
      errhi = []
      for adjust in range(4):
        rladj = lo.ohms + adjust*DELTA
        rhadj = hi.ohms - adjust*DELTA
        errlo.append( abs( rnom - rladj ) )
        errhi.append( abs( rnom - rhadj ) )
      # find smallest error
      iminlo, eminlo = min(enumerate(errlo), key=itemgetter(1))
      iminhi, eminhi = min(enumerate(errhi), key=itemgetter(1))
      if eminlo < eminhi:
        winner = 'LO'
        radj = lo.ohms + iminlo*DELTA
        rerr = eminlo
        cadj = iminlo
        regs = [lo.counts] * 4
        for i in range( iminlo ): regs[i] += 1
      else:
        winner = 'HI'
        radj = hi.ohms - iminhi*DELTA
        rerr = -eminhi
        cadj = -iminhi
        regs = [hi.counts] * 4
        for i in range( iminhi ): regs[i] -= 1
      
      if verbose:
        print(f'{float(rnom):.3f}', end='\t')
        print('{},{}'.format(lo.counts, hi.counts), end='\t')
        print('{:.3f}\t{:.3f}'.format(lo.ohms, hi.ohms), end='\t')
        print('{:.3f}\t{:.3f}'.format(dlo, dhi), end='\t')
        if dlo < dhi: print('LO', end='\t')
        else:         print('HI', end='\t')
        print('\n\tErrlo:', end='\t')
        for e in errlo: print( f'{e:.3f}', end='\t' )
        print('\n\tErrhi:', end='\t')
        for e in errhi: print( f'{e:.3f}', end='\t' )
        print('\n\tWinner:', winner, f'{radj:.3f}\t{rerr:.3f}\t{cadj}', end='\t')
        print('\n\tRegisters:',  end='\t')
        for r in regs: print( f'{r}', end='\t' )
        print()
      else:
        settings.append(Settings( rnom, radj, rerr, regs ))
        #print(f'{rnom:.1f}', end='\t')
        #for r in regs: print( f'{r}', end='\t' )
        #print( f'{radj:.3f}', f'{rerr:+.3f}', sep='\t')

  print(f'# There are {nresistances} settings from {rbeg} to {rend}')
  print(f'# plus zero ohms for a grand total of {1+nresistances}')
  print(f'# Rnominal, Registers[1-4], Ractual, Rerror')
  for s in settings:
    print(s)


if __name__ == "__main__":
  main(sys.argv)

