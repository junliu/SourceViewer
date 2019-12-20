#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Jun Liu <jliu@mpifr-bonn.mpg.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = 'Jun LIU'
__copyright__ = 'Copyright (c) 2017 Jun Liu <jliu@mpifr-bonn.mpg.de>'
__license__ = 'GPL v3'
__version__ = '1.2'

import wx

import ephem
import numpy as np
from astropy.io import ascii as ac2

def Position(ra, dec, ut):

  observatory = ephem.Observer()
  observatory.long = '06:53:02.000'
  observatory.lat = '50:31:29.000'
  observatory.date = ut

  source = ephem.readdb('NAME,f|M|F7,%s,%s,0,2000' %(ra,dec))
  source.compute(observatory)
  return np.degrees(source.az), np.degrees(source.alt)

def setup_all(coordfile, startT, duration):

  d = ac2.read(coordfile)
  src, ra, dec = d['col1'], d['col4'], d['col5']
  elv_limit = 20.0

  endT = startT + duration/24.0
  uts = np.linspace(startT, endT, 12)
  n1 = len(src)
  n2 = len(uts)
  azs, els = [], []

  all = {}
  ava = {}
  inv = {}

  for i in range(n1):
    all[src[i]] = [[], []]
    for j in range(n2):
      _az, _el = Position(ra[i], dec[i], uts[j])
      all[src[i]][0].append(_az)
      all[src[i]][1].append(_el)

    if all[src[i]][1][0] > elv_limit:
      ava[src[i]] = [all[src[i]][0][0], all[src[i]][1][0]]
    else:
      inv[src[i]] = [all[src[i]][0][0], all[src[i]][1][0]]
  return all, ava, inv

def onout(self):
  print('\nPlease check run.tmp file!')


def onrefresh(self, coordfile, startT, duration):

  with open('./calibrator.list') as f:
    calist = f.readlines()
    calist = [e[:-1] for e in calist]

  self.axes.clear()
  self.axes.set_title('Sky Viewer from UT=%s' %str(startT))
  self.axes.set_xlabel(r'$\mathrm{AZI\ [degree]}$')
  self.axes.set_ylabel(r'$\mathrm{ELV\ [degree]}$')
  self.axes.set_xlim(0, 360)
  self.axes.set_ylim(0, 90)
  self.axes.set_xticks(np.arange(0, 360, 25))
  self.axes.set_yticks(np.arange(0, 100, 15))
  self.axes.grid()

  all, ava, inv = \
  setup_all(coordfile, startT, duration)
  d = ac2.read('Eff.hzn')
  hza, hzb = d['col1'], d['col2']
  src = list(all.keys())
  n = len(src)
  self.axes.plot(hza, hzb, 'r-', lw=1)
  self.axes.plot([34, 34], [0, 90], 'b-', linewidth=1)
  self.axes.plot([146, 146], [0, 90], 'b-', linewidth=1)
  for i in range(n):
    if all[src[i]][0][0] > 0:
      if src[i] in calist:
        self.axes.plot(all[src[i]][0], all[src[i]][1], '#00ff00', linestyle='-', linewidth=1.3, alpha=0.5)
        self.axes.scatter(all[src[i]][0][0], all[src[i]][1][0], color='#00ff00', marker='*', s=200, alpha=0.6)
      else:
        self.axes.plot(all[src[i]][0], all[src[i]][1], 'white', linewidth=1.2, alpha=0.5)
        self.axes.scatter(all[src[i]][0][0], all[src[i]][1][0], color='#00ff00', s=50, alpha=0.5)
      self.axes.scatter(all[src[i]][0][-1], all[src[i]][1][-1], color='r', alpha=0.5)
      self.axes.text(all[src[i]][0][0], all[src[i]][1][0], src[i], fontsize=9)

  return all, ava, inv



def onrefresh_keeprange(self, coordfile, startT, duration):

  with open('./calibrator.list') as f:
    calist = f.readlines()
    calist = [e[:-1] for e in calist]

  self.axes.clear()
  self.axes.set_title('Sky View from UT=%s' %str(startT))
  self.axes.set_xlabel(r'$\mathrm{AZI\ [degree]}$')
  self.axes.set_ylabel(r'$\mathrm{ELV\ [degree]}$')
  xlim, ylim = self.axes.get_xlim(), self.axes.get_ylim()
  if xlim == (0, 1): xlim = [0, 360]
  if ylim == (0, 1): ylim = [0, 90]
  self.axes.set_xlim(xlim)
  self.axes.set_ylim(ylim)

  xlim, ylim = list(xlim), list(ylim)
  xlim0 = xlim[0] > 0 and (int(xlim[0]/(30.0+1E-5))+1)*30.0 or 0
#    xlim1 = xlim[0] < 360 and ((xlim[0]/(30.0+1E-5))+1)*30.0 or 360
  self.axes.set_xticks(np.arange(xlim0, xlim[1]+1E-2, 30.0))
#    self.axes.set_xticks(np.linspace(0, 360, 13))
  self.axes.grid()

  all, ava, inv = \
  setup_all(coordfile, startT, duration)
  d = ac2.read('Eff.hzn')
  hza, hzb = d['col1'], d['col2']
  src = list(all.keys())
  n = len(src)
  self.axes.plot(hza, hzb, 'r-', lw=1)
  self.axes.plot([34, 34], [0, 90], 'b-', linewidth=1)
  self.axes.plot([146, 146], [0, 90], 'b-', linewidth=1)
  for i in range(n):
    if all[src[i]][0][0] > 0:
      if src[i] in calist:
        self.axes.plot(all[src[i]][0], all[src[i]][1], '#00ff00', linestyle='-', linewidth=1.3, alpha=0.5)
        self.axes.scatter(all[src[i]][0][0], all[src[i]][1][0], color='#00ff00', marker='*', s=200, alpha=0.6)
      else:
        self.axes.plot(all[src[i]][0], all[src[i]][1], 'white', linewidth=1.2, alpha=0.5)
        self.axes.scatter(all[src[i]][0][0], all[src[i]][1][0], color='#00ff00', s=50, alpha=0.5)
      self.axes.scatter(all[src[i]][0][-1], all[src[i]][1][-1], color='r', alpha=0.5)
      self.axes.text(all[src[i]][0][0], all[src[i]][1][0], src[i], fontsize=9)


  return all, ava, inv



def onfile(self):
  wildcard = r'Source files files (*.sou)|*.sou|Data files (*.dat)|*.dat|ALL Files (*.*)|*.*'
  open_dlg = wx.FileDialog(self,message='Choose a file containing source coordinates',
              wildcard = wildcard, style=wx.FD_OPEN|wx.FD_CHANGE_DIR)
  if open_dlg.ShowModal() == wx.ID_OK:
    path = open_dlg.GetPath()
  else: path = ''
  open_dlg.Destroy()

  return path


def time_estimate(self, ava):
  pass


