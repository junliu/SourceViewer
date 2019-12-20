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
import os
import ephem
import numpy as np
import matplotlib
import core_func as funcs
import datetime
import paramiko
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.ticker import MultipleLocator, FuncFormatter

import pylab
from matplotlib import pyplot

matplotlib.rcParams["axes.facecolor"] = "#545352"
matplotlib.rcParams["axes.edgecolor"] = "white"
matplotlib.rcParams["figure.facecolor"] = "#424140"
matplotlib.rcParams["figure.edgecolor"] = "white"
matplotlib.rcParams["grid.color"] = "white"
matplotlib.rcParams["text.color"] = "white"
matplotlib.rcParams["axes.labelcolor"] = "white"
matplotlib.rcParams["xtick.color"] = "white"
matplotlib.rcParams["ytick.color"] = "white"
matplotlib.rcParams["lines.color"] = "white"

class MainFrame(wx.Frame):
  def __init__(self, *args, **kwds):
    kwds['style'] = kwds.get('style', 0) | wx.DEFAULT_FRAME_STYLE
    wx.Frame.__init__(self, *args, **kwds)
    self.SetSize((1080, 640))
    self.mpl_panel = MPL_Panel(self)
    self.bt_load = wx.Button(self, wx.ID_ANY, 'Load Source')
    self.bt_output = wx.Button(self, wx.ID_ANY, 'Output')
    self.bt_upload = wx.Button(self, wx.ID_ANY, 'Upload')
    self.bt_refresh = wx.Button(self, wx.ID_ANY, 'Refresh')
    self.bt_moveup = wx.Button(self, wx.ID_ANY, 'Move Up')
    self.bt_movedown = wx.Button(self, wx.ID_ANY, 'Move Down')
    self.entry_addr = wx.TextCtrl(self, wx.ID_ANY, 'xxx@xxx.mpifr-bonn.mpg.de:/home/obseff/xxx/Scripts/')
    self.entry_passwd = wx.TextCtrl(self, wx.ID_ANY, '123456', style=wx.TE_PASSWORD)
    self.entry_startut = wx.TextCtrl(self, -1, str(ephem.Date(str(datetime.datetime.utcnow()))))
    self.entry_duration = wx.TextCtrl(self, wx.ID_ANY, '2.0')
    self.entry_slist1 = wx.ListBox(self, -1, choices=[], style=wx.LB_MULTIPLE)
    self.entry_slist0 = wx.ListBox(self, -1, choices=[], style=wx.LB_MULTIPLE)
    self.filler_p0 = wx.Panel(self, wx.ID_ANY)
    self.bt_movein = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap('in.gif', wx.BITMAP_TYPE_ANY))
    self.filler_p1 = wx.Panel(self, wx.ID_ANY)
    self.bt_moveout = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap('out.gif', wx.BITMAP_TYPE_ANY))
    self.filler_p2 = wx.Panel(self, wx.ID_ANY)
    self.entry_queue = wx.ListBox(self, -1, choices=[], style=wx.LB_MULTIPLE)

    self.__set_properties()
    self.__do_layout()

    self.Bind(wx.EVT_BUTTON, self.onfile, self.bt_load)
    self.Bind(wx.EVT_BUTTON, self.onout, self.bt_output)
    self.Bind(wx.EVT_BUTTON, self.onupload, self.bt_upload)
    self.Bind(wx.EVT_BUTTON, self.onrefresh, self.bt_refresh)
    self.Bind(wx.EVT_BUTTON, self.moveup, self.bt_moveup)
    self.Bind(wx.EVT_BUTTON, self.movedown, self.bt_movedown)
    self.Bind(wx.EVT_BUTTON, self.movein, self.bt_movein)
    self.Bind(wx.EVT_BUTTON, self.moveout, self.bt_moveout)
    self.Bind(wx.EVT_LISTBOX_DCLICK, self.double0, self.entry_slist1)
    self.Bind(wx.EVT_LISTBOX_DCLICK, self.double1, self.entry_slist0)

    self.coordfile = 'catalog.sou'
    self.onrefresh(self)
    self.list = {}

  def __set_properties(self):
    self.SetTitle('Source Viewer for Effelsberg')
    self.bt_movein.SetSize(self.bt_movein.GetBestSize())
    self.bt_moveout.SetSize(self.bt_moveout.GetBestSize())

  def __do_layout(self):
    loc_main = wx.BoxSizer(wx.HORIZONTAL)
    loc_ctrl = wx.BoxSizer(wx.VERTICAL)
    loc_srclist = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, ''), wx.HORIZONTAL)
    loc_queue = wx.BoxSizer(wx.VERTICAL)
    loc_move = wx.BoxSizer(wx.VERTICAL)
    loc_src = wx.BoxSizer(wx.VERTICAL)
    loc_ctrl0 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, ''), wx.HORIZONTAL)
    loc_ctrl00 = wx.BoxSizer(wx.VERTICAL)
    loc_setup = wx.FlexGridSizer(4, 2, 3, 3)
    loc_bt = wx.GridSizer(2, 3, 5, 3)
    loc_main.Add(self.mpl_panel, 1, wx.EXPAND, 0)
    loc_bt.Add(self.bt_load, 0, 0, 0)
    loc_bt.Add(self.bt_output, 0, 0, 0)
    loc_bt.Add(self.bt_upload, 0, 0, 0)
    loc_bt.Add(self.bt_refresh, 0, 0, 0)
    loc_bt.Add(self.bt_moveup, 0, 0, 0)
    loc_bt.Add(self.bt_movedown, 0, 0, 0)
    loc_ctrl00.Add(loc_bt, 1, wx.EXPAND, 0)
    tx_addr = wx.StaticText(self, wx.ID_ANY, 'Addr.')
    loc_setup.Add(tx_addr, 0, wx.ALIGN_CENTER_VERTICAL, 0)
    loc_setup.Add(self.entry_addr, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
    tx_passwd = wx.StaticText(self, wx.ID_ANY, 'Passwd')
    loc_setup.Add(tx_passwd, 0, wx.ALIGN_CENTER_VERTICAL, 0)
    loc_setup.Add(self.entry_passwd, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
    tx_startut = wx.StaticText(self, wx.ID_ANY, 'Start UT')
    loc_setup.Add(tx_startut, 0, wx.ALIGN_CENTER_VERTICAL, 0)
    loc_setup.Add(self.entry_startut, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
    tx_duration = wx.StaticText(self, wx.ID_ANY, 'Duration')
    loc_setup.Add(tx_duration, 0, wx.ALIGN_CENTER_VERTICAL, 0)
    loc_setup.Add(self.entry_duration, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
    loc_setup.AddGrowableCol(1)
    loc_ctrl00.Add(loc_setup, 2, wx.EXPAND | wx.TOP, 5)
    loc_ctrl0.Add(loc_ctrl00, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 6)
    loc_ctrl.Add(loc_ctrl0, 0, wx.EXPAND, 0)
    tx_available = wx.StaticText(self, wx.ID_ANY, 'Available', style=wx.ALIGN_CENTER)
    loc_src.Add(tx_available, 0, wx.ALIGN_CENTER | wx.BOTTOM, 2)
    loc_src.Add(self.entry_slist1, 2, wx.ALIGN_CENTER | wx.EXPAND, 0)
    tx_invisible = wx.StaticText(self, wx.ID_ANY, 'Invisible', style=wx.ALIGN_CENTER)
    loc_src.Add(tx_invisible, 0, wx.ALIGN_CENTER | wx.BOTTOM, 2)
    loc_src.Add(self.entry_slist0, 1, wx.ALIGN_CENTER | wx.EXPAND, 0)
    loc_srclist.Add(loc_src, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 6)
    loc_move.Add(self.filler_p0, 2, wx.EXPAND, 0)
    loc_move.Add(self.bt_movein, 0, 0, 0)
    loc_move.Add(self.filler_p1, 1, wx.EXPAND, 0)
    loc_move.Add(self.bt_moveout, 0, 0, 0)
    loc_move.Add(self.filler_p2, 5, wx.EXPAND, 0)
    loc_srclist.Add(loc_move, 0, wx.EXPAND, 0)
    tx_queue = wx.StaticText(self, wx.ID_ANY, 'Queue', style=wx.ALIGN_CENTER)
    loc_queue.Add(tx_queue, 0, wx.ALIGN_CENTER | wx.BOTTOM, 2)
    loc_queue.Add(self.entry_queue, 1, wx.ALIGN_CENTER | wx.EXPAND, 0)
    loc_srclist.Add(loc_queue, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 6)
    loc_ctrl.Add(loc_srclist, 1, wx.EXPAND, 0)
    loc_main.Add(loc_ctrl, 0, wx.ALL | wx.EXPAND, 3)
    self.SetSizer(loc_main)
    self.Layout()

  def onfile(self, event):
    path  = funcs.onfile(self)
    if path != '':
      self.coordfile = path
      print(self.coordfile + ' is chosen.')
      self.onrefresh_keeprange(self)

  def onout(self, event):
    srclist = self.entry_queue.Items

    outf = open('run.tmp', 'w')
#        outf.write('# 6cm Continuum broad band (BW 500 MHz) + Polarimeter, beam switch\n')
#        outf.write('#\nFE:S60mm\n')
#        outf.write(' ; POINTcorr 1 ; SCANLength 600'  ; SCANRepeats 2 ; SCANTime 20\n')
#        outf.write('#\n#\n')

    for src in srclist:
      if src == srclist[0]:
        outf.write('%s ; POINTcorr 1; SCANLength 600"; SCANRepeats 2; SCANTime 22; Catalog cat\n' %src)
      else:
        outf.write('%s\n' %src)

    outf.close()

    print('\nPlease check run.tmp file!')


  def onrefresh(self, event):
    coordfile = self.coordfile
    startT = ephem.Date(str(self.entry_startut.GetValue()))
    duration = float(self.entry_duration.GetValue())

    srcpos = self.guide_eye()

    all, ava, inv = \
    funcs.onrefresh(self.mpl_panel, coordfile, startT, duration)
    if srcpos:
      self.mpl_panel.axes.plot(srcpos[0], srcpos[1], color='yellow', lw=1)
      self.mpl_panel.axes.scatter(srcpos[0][0], srcpos[1][0], s=400, color='yellow', alpha=0.8)

    ava_srcs = list(ava.keys())
    inv_srcs = list(inv.keys())
    ava_srcs.sort()
    inv_srcs.sort()
    self.entry_slist1.SetItems(ava_srcs)
    self.entry_slist0.SetItems(inv_srcs)
    self.mpl_panel.UpdatePlot()

    self.all, self.ava, self.inv = all, ava, inv

    # estimate the observing time
    oh0 = 1.25
    oh1 = 1.682
    subtime = 22.0
    nsub = 4
    vaz = 25.0
    vel = 15.0

    if srcpos and len(srcpos[0]) > 1:
      posx = np.array(srcpos[0])
      posy = np.array(srcpos[1])
      sdx = np.fabs(posx[1:] - posx[:-1])
      sdx = np.array([s if s<180 else 360-s for s in sdx])
      sdy = np.fabs(posy[1:] - posy[:-1])
      tdx = sdx/vaz
      tdy = sdy/vel
      tslew = np.sum([max(a, b) for (a, b) in zip(tdx, tdy)])
      ttrack = subtime*nsub/60.0*len(posx)

      print('#'*20)
      print('on source time: %0.1f min' %(ttrack*oh0))
      print('slewing time:   %0.1f min' %(tslew*oh1))
      print('total:          %0.1f min' %(ttrack*oh0+tslew*oh1))

  def onrefresh_keeprange(self, event):
    coordfile = self.coordfile
    startT = ephem.Date(str(self.entry_startut.GetValue()))
    duration = float(self.entry_duration.GetValue())

    srcpos = self.guide_eye()

    all, ava, inv = \
    funcs.onrefresh_keeprange(self.mpl_panel, coordfile, startT, duration)
    if srcpos:
      self.mpl_panel.axes.plot(srcpos[0], srcpos[1], color='yellow', lw=1)
      self.mpl_panel.axes.scatter(srcpos[0][0], srcpos[1][0], s=400, color='yellow', alpha=0.8)

    ava_srcs = list(ava.keys())
    inv_srcs = list(inv.keys())
    ava_srcs.sort()
    inv_srcs.sort()
    self.entry_slist1.SetItems(ava_srcs)
    self.entry_slist0.SetItems(inv_srcs)
    self.mpl_panel.UpdatePlot()

    self.all, self.ava, self.inv = all, ava, inv

    return all, ava, inv


  def onupload(self, event):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    addr = self.entry_addr.GetValue()
    username, addr = addr.split('@')
    addr, remote_dir =addr.split(':')
    ssh.connect(addr, username = username, password=self.entry_passwd.GetValue())
    sftp = ssh.open_sftp()
    sftp.put('run.tmp', remote_dir+'/run.tmp')
    ssh.close()

  def double0(self, event):
    idx = self.entry_slist1.Selections[0]
    src = list(self.ava.keys())
    src.sort()
    self.mpl_panel.axes.scatter(self.ava[src[idx]][0], self.ava[src[idx]][1], s=300, color='red', alpha=0.5)
    self.mpl_panel.UpdatePlot()

  def double1(self, event):
    idx = self.entry_slist0.Selections[0]
    src = list(self.inv.keys())
    src.sort()
    self.mpl_panel.axes.scatter(self.inv[src[idx]][0], self.inv[src[idx]][1], s=300, color='red', alpha=0.5)
    self.mpl_panel.UpdatePlot()

  def movein(self, event):
    srclist = self.entry_queue.Items

    if self.entry_slist1.Selections:
      idx = self.entry_slist1.Selections
      for i in idx:
        src = self.entry_slist1.Items[i]
        self.list[src] = self.ava[src]
        if src not in srclist: srclist.append(src)
      self.entry_queue.SetItems(srclist)
      self.onrefresh(self)

    if self.entry_slist0.Selections:
      idx = self.entry_slist0.Selections
      for i in idx:
        src = self.entry_slist0.Items[i]
        self.list[src] = self.inv[src]
        if src not in srclist: srclist.append(src)
      self.entry_queue.SetItems(srclist)
      self.onrefresh(self)

  def moveout(self, event):
    if self.entry_queue.Selections:
      idx = self.entry_queue.Selections
      for i in idx:
        src = self.entry_queue.Items[i]
        del self.list[src]

      remain_list = [e for e in self.entry_queue.Items if e in self.list.keys()]
      self.entry_queue.SetItems(remain_list)

      self.onrefresh(self)

  def moveup(self, event):
    srclist = self.entry_queue.Items

    if self.entry_queue.Selections:
      idx = self.entry_queue.Selections
      if len(idx) >= 1:
        n = len(srclist)
        ns = len(idx)
        order = list(range(idx[0]-1))
        order += idx
        order += [idx[0]-1]
        order += list(range(idx[0]+ns, n))
        srclist = [srclist[o] for o in order]
        self.entry_queue.SetItems(srclist)
        for i in idx:
          self.entry_queue.Select(i-1)
        self.onrefresh(self)

  def movedown(self, event):
    srclist = self.entry_queue.Items

    if self.entry_queue.Selections:
      idx = self.entry_queue.Selections
      if len(idx) >= 1:
        n = len(srclist)
        ns = len(idx)
        order = list(range(idx[0]))
        order += [idx[-1]+1]
        order += idx
        if ns == 1:
          ns += 1
        order += list(range(idx[-1]+ns, n))
        srclist = [srclist[o] for o in order]
        self.entry_queue.SetItems(srclist)
        for i in idx:
          self.entry_queue.Select(i+1)
        self.onrefresh(self)

  def guide_eye(self):
    startT = ephem.Date(str(self.entry_startut.GetValue()))
    duration = float(self.entry_duration.GetValue())
    all, ava, inv = funcs.setup_all(self.coordfile, startT, duration)
    del ava, inv
    srcs = self.entry_queue.Items
    if not len(srcs): return

    gdx, gdy = [], []
    for src in srcs:
      gdx.append(all[src][0][0])
      gdy.append(all[src][1][0])

    return gdx, gdy


class SourceView(wx.App):
  def OnInit(self):
    self.SourceViewer = MainFrame(None, wx.ID_ANY, '')
    self.SetTopWindow(self.SourceViewer)
    self.SourceViewer.Show()
    return True

class MPL_Panel_base(wx.Panel):

  def __init__(self,parent):
    wx.Panel.__init__(self,parent=parent, id=-1)

    self.Figure = matplotlib.figure.Figure(figsize=(4,3))
    self.axes = self.Figure.add_axes([0.05,0.1,0.9,0.85])
    self.FigureCanvas = FigureCanvas(self,-1,self.Figure)

    self.NavigationToolbar = NavigationToolbar(self.FigureCanvas)

    self.SubBoxSizer = wx.BoxSizer(wx.HORIZONTAL)
    self.SubBoxSizer.Add(self.NavigationToolbar,proportion =0, border = 2,flag = wx.ALL | wx.EXPAND)

    self.TopBoxSizer = wx.BoxSizer(wx.VERTICAL)
    self.TopBoxSizer.Add(self.SubBoxSizer,proportion =-1, border = 2,flag = wx.ALL | wx.EXPAND)
    self.TopBoxSizer.Add(self.FigureCanvas,proportion =-10, border = 2,flag = wx.ALL | wx.EXPAND)

    self.SetSizer(self.TopBoxSizer)

    self.pylab=pylab
    self.pl=pylab
    self.pyplot=pyplot
    self.numpy=np
    self.np=np
    self.plt=pyplot

  def UpdatePlot(self):
    # this function should be called after any modification to the plot
    self.FigureCanvas.draw()

  def subplot1(self ,*args,**kwargs):
    pass

  def plot(self,*args,**kwargs):
    self.axes.plot(*args,**kwargs)
    self.UpdatePlot()


  def semilogx(self,*args,**kwargs):
    self.axes.semilogx(*args,**kwargs)
    self.UpdatePlot()

  def semilogy(self,*args,**kwargs):
    self.axes.semilogy(*args,**kwargs)
    self.UpdatePlot()

  def loglog(self,*args,**kwargs):
    self.axes.loglog(*args,**kwargs)
    self.UpdatePlot()


  def grid(self,flag=True):
    if flag:
      self.axes.grid()
    else:
      self.axes.grid(False)


  def title_MPL(self,TitleString):
    self.axes.set_title(TitleString)


  def xlabel(self,XabelString='X'):
    self.axes.set_xlabel(XabelString)


  def ylabel(self,YabelString='Y'):
    self.axes.set_ylabel(YabelString)


  def xticker(self,major_ticker=1.0,minor_ticker=0.1):
    self.axes.xaxis.set_major_locator( MultipleLocator(major_ticker) )
    self.axes.xaxis.set_minor_locator( MultipleLocator(minor_ticker) )


  def yticker(self,major_ticker=1.0,minor_ticker=0.1):
    self.axes.yaxis.set_major_locator( MultipleLocator(major_ticker) )
    self.axes.yaxis.set_minor_locator( MultipleLocator(minor_ticker) )


  def legend(self,*args,**kwargs):
    self.axes.legend(*args,**kwargs)


  def xlim(self,x_min,x_max):
    self.axes.set_xlim(x_min,x_max)


  def ylim(self,y_min,y_max):
    self.axes.set_ylim(y_min,y_max)


  def savefig(self,*args,**kwargs):
    self.Figure.savefig(*args,**kwargs)


  def cla(self):
    self.axes.clear()
    self.Figure.set_canvas(self.FigureCanvas)
    self.UpdatePlot()

  def ShowHelpString(self,HelpString='Show Help String'):
    self.StaticText.SetLabel(HelpString)


class MPL_Panel(MPL_Panel_base):
  def __init__(self,parent):
    MPL_Panel_base.__init__(self,parent=parent)


if __name__ == '__main__':
  SourceViewApps = SourceView(0)
  SourceViewApps.MainLoop()
