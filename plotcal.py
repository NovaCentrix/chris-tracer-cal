#!/usr/bin/env python

import sys, glob
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import csv

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
  print('plotcal [calibration-data-file]')
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


# Filename format for extracting label information
# tracer-sn0-r1-cal.dat
# tracer-sn0-r2-cal.dat
# tracer-sn1-r1-cal.dat
# tracer-sn1-r2-cal.dat
# tracer-sn2-r1-cal.dat
# tracer-sn2-r2-cal.dat
# tracer-sn3-r1-cal.dat
# tracer-sn3-r2-cal.dat

def filename_parse( fn ):
  fields = fn.split('-')
  serno = fields[1]
  resno = fields[2]
  return serno.upper(), resno.upper()

def main( argv ):

  if len(argv) < 2:
    show_help()
    exit(0)

  plotme = False
  statistics = True

  if statistics:
    print( f'# TraceR calibration summary')
    print( f'# S/N\tR#\tSlope\tOffset')

  for fname in sys.argv[1:]:

    serno, resno = filename_parse( fname )
    calib = calibration_read( fname )

    x = [ c.counts for c in calib[:-1] ]
    y = [ c.ohms   for c in calib[:-1] ]
    linfit = np.polyfit(x,y,1)
    predict = np.poly1d(linfit)
    xfit = range(0,256)
    yfit = predict(xfit)
    slope = linfit[0]
    offset = linfit[1]
    
    if plotme:
      fig,ax = plt.subplots(nrows=1, ncols=1, figsize=(6,5))
      fig.suptitle('TraceR Calibration Data '+serno, 
                    fontsize=14, fontweight='bold')
    
      major_ticks_x = np.arange(0,257,32)
      minor_ticks_x = np.arange(0,257,8)
      major_ticks_y = np.arange(0,301,50)
      minor_ticks_y = np.arange(0,301,10)

      ax.set_title('Digipot '+resno)
      ax.set_xlim(0,256)
      ax.set_ylim(0,300)
      ax.scatter(x,y)
      ax.plot(xfit, yfit, c= 'r')
      ax.set_xticks(major_ticks_x)
      ax.set_xticks(minor_ticks_x, minor=True)
      ax.set_yticks(major_ticks_y)
      ax.set_yticks(minor_ticks_y, minor=True)
      ax.grid(which='both')
      ax.grid(which='minor', alpha=0.2)
      ax.grid(which='major', alpha=0.5)
      ax.set_xlabel('Digipot Wiper Setting, Counts')
      ax.set_ylabel('Resistance, Ohms')
      ax.text(12,260, ' slope: {:.3f}\noffset: {:.3f}'.format(slope, offset), 
                 bbox={'facecolor': 'blue', 'alpha': 0.2, 'pad': 4})
    
      fig.tight_layout()
      plt.show()

    if statistics:
      print( f'{serno}\t{resno}\t{slope:.3f}\t{offset:.3f}' )


  

if __name__ == "__main__":

  #print(sys.argv[1])
  #for fname in glob.glob(sys.argv[1]):
  #  print(fname)

  main(sys.argv)

