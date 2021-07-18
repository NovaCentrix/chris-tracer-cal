#!/usr/bin/env python

import sys
import csv

class Registers:
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

class Inverse:
  def __init__(self, fname=None):
    self.regs=[]
    self.serno = None
    self.resno = None
    self.rbeg = None
    self.rend = None
    self.nres = None
    if fname is not None:
      self.load(fname)

  def load(self, fname):
    with open(fname, 'r') as fin:
      reader = csv.reader(fin, delimiter='\t')
      npoints=0
      for row in reader:
        #print(type(row), len(row), row)
        if row[0][0] == '#': continue
        if self.serno is None:
          self.serno = row[0]
        elif self.resno is None:
          self.resno = row[0]
        elif self.rbeg is None:
          self.rbeg = float(row[0])
        elif self.rend is None:
          self.rend = float(row[0])
        elif self.nres is None:
          self.nres = int(row[0])
        else:
          rnom = float(row[0])
          regs=[]
          regs.append( int(row[1]) )
          regs.append( int(row[2]) )
          regs.append( int(row[3]) )
          regs.append( int(row[4]) )
          ract = float(row[5])
          rerr = float(row[6])
          self.regs.append(Registers(rnom, ract, rerr, regs))

  def print_header( self, fp=sys.stdout ):
    print(f'{self.serno}\t# serial number', file=fp)
    print(f'{self.resno}\t# resistor number', file=fp)
    print(f'{self.rbeg}\t# minimum resistance value', file=fp)
    print(f'{self.rend}\t# maximum resistance value', file=fp)
    print(f'{self.nres}\t# number of resistances', file=fp)

  def print_regs( self, fp=sys.stdout ):
    print(f'# Rnominal, Registers[1-4], Ractual, Rerror', file=fp)
    for reg in self.regs:
      print(reg, file=fp)

  def print_all( self, fp=sys.stdout ):
    self.print_header(fp)
    self.print_regs(fp)

  def lookup( self, rnom ):
    irnom = int(rnom+0.5)
    if irnom < int(self.rbeg):
      return self.regs[1]
    if irnom > int(self.rend):
      return self.regs[-1]
    match = False
    for regs in self.regs:
      if irnom == int(regs.rnom):
        match = True
        break
    if match:
      return regs
    else:
      return None
