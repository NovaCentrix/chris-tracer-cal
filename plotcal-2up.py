#!/usr/bin/env python

import sys
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

def main( argv ):
  if len(argv) < 2:
    show_help()
    exit(0)

  calib1 = calibration_read( argv[1] )
  calib2 = calibration_read( argv[2] )


  fig,ax = plt.subplots(nrows=1, ncols=2, figsize=(12,5))

  fig.suptitle('TraceR SN:0 Calibration Data', 
                fontsize=14, fontweight='bold')

  major_ticks_x = np.arange(0,257,32)
  minor_ticks_x = np.arange(0,257,8)
  major_ticks_y = np.arange(0,301,50)
  minor_ticks_y = np.arange(0,301,10)

# resistor 1
  x = [ c.counts for c in calib1[:-1] ]
  y = [ c.ohms   for c in calib1[:-1] ]
  linfit = np.polyfit(x,y,1)
  predict = np.poly1d(linfit)
  xfit = range(0,256)
  yfit = predict(xfit)
  slope = linfit[0]
  offset = linfit[1]


  ax[0].set_title('Digipot TR1')
  ax[0].set_xlim(0,256)
  ax[0].set_ylim(0,300)
  ax[0].scatter(x,y)
  ax[0].plot(xfit, yfit, c= 'r')
  ax[0].set_xticks(major_ticks_x)
  ax[0].set_xticks(minor_ticks_x, minor=True)
  ax[0].set_yticks(major_ticks_y)
  ax[0].set_yticks(minor_ticks_y, minor=True)
  ax[0].grid(which='both')
  ax[0].grid(which='minor', alpha=0.2)
  ax[0].grid(which='major', alpha=0.5)
  ax[0].set_xlabel('Digipot Wiper Setting, Counts')
  ax[0].set_ylabel('Resistance, Ohms')
  ax[0].text(12,260, ' slope: {:.3f}\noffset: {:.3f}'.format(slope, offset), 
             bbox={'facecolor': 'blue', 'alpha': 0.2, 'pad': 4})

# resistor 2
  x = [ c.counts for c in calib2[:-1] ]
  y = [ c.ohms   for c in calib2[:-1] ]
  linfit = np.polyfit(x,y,1)
  predict = np.poly1d(linfit)
  xfit = range(0,256)
  yfit = predict(xfit)
  slope = linfit[0]
  offset = linfit[1]

  ax[1].set_title('Digipot TR2')
  ax[1].set_xlim(0,256)
  ax[1].set_ylim(0,300)
  ax[1].scatter(x,y)
  ax[1].plot(xfit, yfit, c= 'r')
  ax[1].set_xticks(major_ticks_x)
  ax[1].set_xticks(minor_ticks_x, minor=True)
  ax[1].set_yticks(major_ticks_y)
  ax[1].set_yticks(minor_ticks_y, minor=True)
  ax[1].grid(which='both')
  ax[1].grid(which='minor', alpha=0.2)
  ax[1].grid(which='major', alpha=0.5)
  ax[1].set_xlabel('Digipot Wiper Setting, Counts')
  ax[1].set_ylabel('Resistance, Ohms')
  ax[1].text(10,260, ' slope: {:.3f}\noffset: {:.3f}'.format(slope, offset), 
             bbox={'facecolor': 'blue', 'alpha': 0.2, 'pad': 4})

  fig.tight_layout()
  plt.show()

if __name__ == "__main__":
  main(sys.argv)

