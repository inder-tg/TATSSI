
import os
import sys

# TATSSI modules
HomeDir = os.path.join(os.path.expanduser('~'))
SrcDir = os.path.join(HomeDir, 'Projects', 'TATSSI')
sys.path.append(SrcDir)

from TATSSI.time_series.generator import Generator
from TATSSI.input_output.translate import Translate
from TATSSI.input_output.utils import *
from TATSSI.qa.EOS.catalogue import Catalogue

from TATSSI.download.modis_downloader import get_modis_data
from TATSSI.download.viirs_downloader import get_viirs_data

# Widgets
import ipywidgets as widgets
from ipywidgets import Layout
from ipywidgets import Button, HBox, VBox
from ipywidgets import interact, interactive, fixed, interact_manual

from beakerx import TableDisplay

from IPython.display import clear_output
from IPython.display import display

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog

import json
import gdal, ogr
import pandas as pd
import xarray as xr
from rasterio import logging as rio_logging
from datetime import datetime

import matplotlib
matplotlib.use('nbagg')
import matplotlib.pyplot as plt

class PlotTimeSeries():
    """
    Class to plot a single time step and per-pixel time series
    """
    def __init__(self):
        self.fig = plt.figure(figsize=(9.0, 9.0))

        # Left plot
        self.left_p = plt.subplot2grid((2, 2), (0, 0), colspan=1)
        # Right plot
        self.right_p = plt.subplot2grid((2, 2), (0, 1), colspan=1,
                                   sharey=self.left_p)
        # Time series plot
        self.ts_p = plt.subplot2grid((2, 2), (1, 0), colspan=2)

        # Disable RasterIO logging, just show ERRORS
        log = rio_logging.getLogger()
        log.setLevel(rio_logging.ERROR)

        self.ds = None

    def plot(self, left_ds, right_ds, is_qa=False):
        """
        Plot a variable and time series
        :param left_ds: xarray to plot on the left panel
        :param right_ds: xarray to plot on the right panel
        """
        self.left_ds = left_ds
        # Create plot
        self.left_ds[0].plot(cmap='Greys_r', ax=self.left_p,
                             add_colorbar=False)

        # Turn off axis
        self.left_p.axis('off')
        self.left_p.set_aspect('equal')

        # Connect the canvas with the event
        cid = self.fig.canvas.mpl_connect('button_press_event',
                                          self.on_click)

        # Plot the centroid
        _layers, _rows, _cols = self.left_ds.shape
        # Get y-axis max and min
        #y_min, y_max = self.ds.data.min(), self.ds.data.max()

        plot_sd = self.left_ds.sel(longitude = int(_cols / 2),
                                   latitude = int(_rows / 2),
                                   method='nearest')

        plot_sd.plot(ax = self.ts_p)

        # Right panel
        self.right_ds = right_ds
        # Create plot
        self.right_ds[0].plot(cmap='Greys_r', ax=self.right_p,
                              add_colorbar=False)

        # Turn off axis
        self.right_p.axis('off')
        self.right_p.set_aspect('equal')

        plt.tight_layout()
        plt.show()

    def on_click(self, event):
        """
        Event handler
        """
        # Clear subplot
        self.ts_p.clear()

        left_plot_sd = self.left_ds.sel(longitude=event.xdata,
                                        latitude=event.ydata,
                                        method='nearest')

        right_plot_sd = self.left_ds.sel(longitude=event.xdata,
                                         latitude=event.ydata,
                                         method='nearest')

        left_plot_sd.plot(ax = self.ts_p, color='blue', linestyle = '--')
        right_plot_sd.plot(ax = self.ts_p, color='black', marker='o')
        # Redraw plot
        plt.draw()