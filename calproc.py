#!/usr/bin/env python

import sys, glob
from operator import itemgetter
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import csv

from inverse import Registers, Inverse
from calibration import Sample, Calib

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
  parser.add_argument('--plotchk', action='store_true', help='Plot check measurements, Rmeas vs Rcmd')
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
  plotsetup = args.plotcal or args.plotregs or args.ploterrs or args.plotchk

  if args.stats:
    print( f'# TraceR calibration summary')
    print( f'# S/N\tR#\tSlope\tOffset\tRmin\tRmax\tNres')

  if plotsetup:
    if nfiles <= 2:
      nprows = 1
      npcols = nfiles
    else:
      npcols = 2
      nprows = int(0.5+(nfiles/2))
    fig, ax = plt.subplots(nrows=nprows, ncols=npcols, 
                  figsize=(6*npcols,5*nprows))
    title = 'TraceR Calibration Data'
    fig.canvas.manager.set_window_title('tracer-calibration')
    fig.suptitle(title, fontsize=10, fontweight='bold')
    if nfiles == 1: ax = [[ax],[]]
    # print(len(ax))
    # print('nfiles:', nfiles)
    # print('nprows:', nprows)
    # print('npcols:', npcols)
    # breakpoint()

  iprow=0
  ipcol=0
  for ifile, ftype in enumerate(args.calfiles):
    fname = ftype.name

    if args.itest:
      inverse = Inverse( fname )
    elif args.plotchk:
      #this isn't really calibration data
      # the "counts" of the rcheck file 
      # contains the commanded resistance value
      calib = Calib( fname )
    else:
      calib = Calib( fname )
      calib.linear_fit()
      calib.invert()

    if args.plotcal:
      calib.plot_samples( ax[iprow][ipcol] )

    if args.plotregs:
      calib.plot_registers( ax[iprow][ipcol] )

    if args.ploterrs:
      calib.plot_errors( ax[iprow][ipcol] )

    if args.plotchk:
      calib.plot_check( ax[iprow][ipcol] )

    ipcol += 1
    if ipcol >= 2:
      ipcol = 0
      iprow += 1

    if args.invert:
      fout = calib.fname_output()
      print('Writing reg filename:', fout)
      with open( fout, 'w') as fp:
        calib.inverse.print_all(fp)

    if args.stats:
      print( f'{calib.serno}\t{calib.resno}\t'\
             f'{calib.slope:.3f}\t{calib.offset:.3f}\t'\
             f'{calib.inverse.rbeg}\t{calib.inverse.rend}\t{calib.inverse.nres}')

    if args.itest:
      inverse.print_all()

  if plotsetup:
    fig.tight_layout(pad=0.5, w_pad = 0.5, h_pad = 1.0)
    plt.show()

if __name__ == "__main__":
  main(sys.argv)



