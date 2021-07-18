#!/usr/bin/env python

import sys, glob
from operator import itemgetter
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import csv

from inverse import Registers, Inverse

class Sample:
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
  #   0    12.00    0.0079 10    [12.01, 12.01, 12.01, 12.01, 12.0, 12.0, 12.0, 12.0, 11.99, 11.99]
  #   1    13.61    0.0042 10    [13.6, 13.6, 13.61, 13.61, 13.61, 13.61, 13.61, 13.61, 13.61, 13.61]
  #   2    14.57    0.0052 10    [14.56, 14.56, 14.56, 14.56, 14.57, 14.57, 14.57, 14.57, 14.57, 14.57]
  #   3    15.80    0.0000 10    [15.8, 15.8, 15.8, 15.8, 15.8, 15.8, 15.8, 15.8, 15.8, 15.8]

class Calib:
  def __init__(self, fname=None):
    self.samples=[]
    self.fname = fname
    self.fname_parse( fname )
    self.inverse = Inverse()
    self.verbose = False
    if fname is not None:
      self.load(fname)

  def load(self, fname):
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
        self.samples.append( Sample( counts, ohms, stdev, nsamples, data ))
        npoints += 1

  def fname_parse( self, fn ):
    # Filename format for extracting label information
    # tracer-sn0-r1-cal.dat
    # tracer-sn0-r2-cal.dat
    # tracer-sn3-r2-cal.dat
    fields = fn.split('-')
    self.serno = fields[1].upper()
    self.resno = fields[2].upper()

  def fname_output( self ):
    # make output filename
    # invert-sn0-r1-regs.dat
    # invert-sn0-r2-regs.dat
    # invert-sn3-r2-regs.dat
    self.fout =  f'data/invert-{self.serno.lower()}'\
                 f'-{self.resno.lower()}-cal.dat'
    return self.fout

  def linear_fit( self ):
    self.x = [ c.counts for c in self.samples[:-1] ]
    self.y = [ c.ohms   for c in self.samples[:-1] ]
    self.linfit = np.polyfit(self.x,self.y,1)
    self.predict = np.poly1d(self.linfit)
    self.xfit = range(0,256)
    self.yfit = self.predict(self.xfit)
    self.slope = self.linfit[0]
    self.offset = self.linfit[1]

  def invert( self ):
    DELTA = 0.25
    self.inverse.serno = self.serno
    self.inverse.resno = self.resno
    # zero ohms case is special, relay is engaged, 
    # result from calibration stored at 256
    self.inverse.nres = 1
    rnom = 0
    regs = [0,0,0,0]
    radj = self.samples[-1].ohms
    rerr = radj
    self.inverse.regs.append(Registers( rnom, radj, rerr, regs ))
    for rnom in range(1,300):
      lo = None
      hi = None
      c0 = self.samples[0]
      for c in self.samples[1:-1]:
        if rnom > c0.ohms and rnom <= c.ohms:
          lo=c0
          hi=c
          break
        c0 = c

      if lo is not None and hi is not None:
        # save beg and end for summary
        if self.inverse.rbeg is None: self.inverse.rbeg = rnom
        self.inverse.rend = rnom
        self.inverse.nres += 1
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
        if self.verbose:
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
          self.inverse.regs.append(Registers( rnom, radj, rerr, regs ))
          #print(f'{rnom:.1f}', end='\t')
          #for r in regs: print( f'{r}', end='\t' )
          #print( f'{radj:.3f}', f'{rerr:+.3f}', sep='\t')

  def plot_samples( self, ax ):
    major_ticks_x = np.arange(0,257,32)
    minor_ticks_x = np.arange(0,257,8)
    major_ticks_y = np.arange(0,301,50)
    minor_ticks_y = np.arange(0,301,10)

    ax.set_title(f'Digipot {self.serno} {self.resno}')
    ax.set_xlim(0,256)
    ax.set_ylim(0,300)
    ax.scatter(self.x,self.y)
    ax.plot(self.xfit, self.yfit, c= 'r')
    ax.set_xticks(major_ticks_x)
    ax.set_xticks(minor_ticks_x, minor=True)
    ax.set_yticks(major_ticks_y)
    ax.set_yticks(minor_ticks_y, minor=True)
    ax.grid(which='both')
    ax.grid(which='minor', alpha=0.2)
    ax.grid(which='major', alpha=0.5)
    ax.set_xlabel('Digipot Wiper Setting, Counts')
    ax.set_ylabel('Resistance, Ohms')
    ax.text(12,260, ' slope: {:.3f}\noffset: {:.3f}'\
                 .format(self.slope, self.offset), 
                  bbox={'facecolor': 'blue', 'alpha': 0.2, 'pad': 4})

  def plot_registers( self, ax ):
    major_ticks_x = np.arange(0,301,50)
    minor_ticks_x = np.arange(0,301,10)
    major_ticks_y = np.arange(0,257,32)
    minor_ticks_y = np.arange(0,257,8)

    x = [ r.rnom for r in self.inverse.regs ]
    y0 = [ r.regs[0] for r in self.inverse.regs ]
    y1 = [ r.regs[1] for r in self.inverse.regs ]
    y2 = [ r.regs[2] for r in self.inverse.regs ]
    y3 = [ r.regs[3] for r in self.inverse.regs ]

    ax.set_title(f'Registers {self.serno} {self.resno}')
    ax.set_xlim(0,300)
    ax.set_ylim(0,256)
    ax.scatter(x,y0)
    ax.scatter(x,y1)
    ax.scatter(x,y2)
    ax.scatter(x,y3)
    ax.set_xticks(major_ticks_x)
    ax.set_xticks(minor_ticks_x, minor=True)
    ax.set_yticks(major_ticks_y)
    ax.set_yticks(minor_ticks_y, minor=True)
    ax.grid(which='both')
    ax.grid(which='minor', alpha=0.2)
    ax.grid(which='major', alpha=0.5)
    ax.set_xlabel('Nominal Resistance, Ohms')
    ax.set_ylabel('Digipot Register Settings, Counts')

  def plot_errors( self, ax ):
    major_ticks_x = np.arange(0,301,50)
    minor_ticks_x = np.arange(0,301,10)
    major_ticks_y = np.arange(-0.5,+0.5,0.10)
    minor_ticks_y = np.arange(-0.5,+0.5,0.05)

    x = [ r.rnom for r in self.inverse.regs ]
    y = [ r.rerr for r in self.inverse.regs ]

    ax.set_title(f'Errors for {self.serno} {self.resno}')
    ax.set_xlim(0,300)
    ax.set_ylim(-0.5,+0.5)
    ax.scatter(x,y)
    ax.set_xticks(major_ticks_x)
    ax.set_xticks(minor_ticks_x, minor=True)
    ax.set_yticks(major_ticks_y)
    ax.set_yticks(minor_ticks_y, minor=True)
    ax.grid(which='both')
    ax.grid(which='minor', alpha=0.2)
    ax.grid(which='major', alpha=0.5)
    ax.set_ylabel('Resistance Error, Ohms')
    ax.set_xlabel('Commanded Resistance, Ohms')
    ax.text(12,260, ' slope: {:.3f}\noffset: {:.3f}'\
                 .format(self.slope, self.offset), 
                  bbox={'facecolor': 'blue', 'alpha': 0.2, 'pad': 4})


def main( argv ):

  descr = 'TraceR Module Calibration Data Processing Utility'
  epilog = 'add more details here'
  # parse command line args
  parser = argparse.ArgumentParser(description=descr, epilog=epilog)
  parser.add_argument('--stats', action='store_true', help='Summarize calibration(s) statistics')
  parser.add_argument('--invert', action='store_true', help='Calc and save inverse function register values')
  parser.add_argument('--plotcal', action='store_true', help='Plot cal(s) measured data, Ract vs counts')
  parser.add_argument('--plotregs', action='store_true', help='Plot inverse(s) register values, countsx4 vs Rnom')
  parser.add_argument('--ploterrs', action='store_true', help='Plot inverse(s) error values, |Radj-Rnom|')
  parser.add_argument('--itest', action='store_true', help='Read and print inverse function cal file')
  parser.add_argument('calfiles', type=argparse.FileType('r'), nargs='*', help='Cal data file(s)')
  
  args = parser.parse_args()
  nfiles = len(args.calfiles)
  if len(sys.argv)==1 or nfiles==0: # no command line arguments, print help
    parser.print_help(sys.stderr)
    sys.exit(0)

  #### print(type(args.calfiles))
  #### print(args.calfiles)
  #### for f in args.calfiles:
  ####   print(f.name, f.mode)
  #### exit(0)

  verbose = False
  plotsetup = args.plotcal or args.plotregs or args.ploterrs

  if args.stats:
    print( f'# TraceR calibration summary')
    print( f'# S/N\tR#\tSlope\tOffset\tRmin\tRmax\tNres')

  if plotsetup:
    fig, ax = plt.subplots(nrows=1, ncols=nfiles, 
                  figsize=(6*nfiles,5))
    title = 'TraceR Calibration Data'
    fig.suptitle(title, fontsize=14, fontweight='bold')
    if nfiles == 1: ax = [ax]

  for ifile, ftype in enumerate(args.calfiles):
    fname = ftype.name

    if args.itest:
      inverse = Inverse( fname )
    else:
      calib = Calib( fname )
      calib.linear_fit()
      calib.invert()

    if args.plotcal:
      calib.plot_samples( ax[ifile] )

    if args.plotregs:
      calib.plot_registers( ax[ifile] )

    if args.ploterrs:
      calib.plot_errors( ax[ifile] )

    if args.invert:
      fout = calib.fname_output()
      print('Writing reg filename:', fout)
      with open( fout, 'w') as fp:
        calib.inverse.print_all(fp)

    if args.stats:
      print( f'{calib.serno}\t{calib.resno}\t'\
             f'{calib.slope:.3f}\t{calib.offset:.3f}\t'\
             f'{calib.rbeg}\t{calib.rend}\t{calib.nres}')

    if args.itest:
      inverse.print_all()

  if plotsetup:
    #fig.tight_layout()
    plt.show()

if __name__ == "__main__":
  main(sys.argv)



