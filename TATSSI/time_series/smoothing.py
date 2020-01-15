
import os
import gdal
import xarray as xr
from dask.distributed import Client
from dask.diagnostics import ProgressBar
import rasterio as rio
import logging
from rasterio import logging as rio_logging

from TATSSI.input_output.utils import save_dask_array

from .ts_utils import *
from .smoothn import *

class Smoothing():
    """
    Class to perform a time series analysis
    """
    def __init__(self, data=None, fname=None,
                 output_fname=None,
                 smoothing_methods=['smoothn']):
        """
        TATSSI smoother. Can receive either:
        - an xarray with dimensions time, latitude and longitude
        - a file name full path with a valid TATSSI file that includes
          metadata to set the dates/time steps
        The results of smoother will be saved in output_fname for all
        valid smoothing methods
        :param data: xarray with dimensions time, latitude and longitude
        :param fname: Input filename full path
        :param output_fname: Output filename full path
        :param smoothing_methods: A valid TATSSI smoothing method
        """
        # Set self.data
        if data is not None:
            if self.__check_is_xarray(data) is True:
                self.data = data
        elif fname is not None:
            self.fname = fname
            self.dataset_name = None # set in self.__get_dataset
            self.__get_dataset()

        # Output filename
        self.output_fname = output_fname

        if type(smoothing_methods) == list:
            self.smoothing_methods = smoothing_methods

    def smooth(self):
        """
        Method to perform a smoothing on a time series
        """
        def __smoothn(_data):
            # Create output array
            _smoothed_data = smoothn(_data, isrobust=True, s=0.75,
                     TolZ=1e-6, axis=0)[0].astype(_data.dtype)

            return _smoothed_data

        # Create output array
        # Smooth data like a porco!
        y = getattr(self.data, self.dataset_name)
        smoothed_data = xr.apply_ufunc(__smoothn, y,
                dask='parallelized', output_dtypes=[y.data.dtype])

        # Copy attributes
        smoothed_data.attrs = getattr(self.data, self.dataset_name).attrs

        with ProgressBar():
            smoothed_data = smoothed_data.compute()

        save_dask_array(fname=self.output_fname, data=smoothed_data,
                        data_var=self.dataset_name, method='smoothn',
                        dask=False)
                        #tile_size=256, n_workers=3,
                        #threads_per_worker=1, memory_limit='7GB')

    def __get_dataset(self):
        """
        Load all layers from a GDAL compatible file into an xarray
        """
        # Disable RasterIO logging, just show ERRORS
        log = rio_logging.getLogger()
        log.setLevel(rio_logging.ERROR)

        try:
            # Get dataset
            tmp_ds = xr.open_rasterio(self.fname)
            tmp_ds = None ; del tmp_ds
        except rio.errors.RasterioIOError as e:
            raise e

        chunks = get_chunk_size(self.fname)
        data_array = xr.open_rasterio(self.fname, chunks=chunks)

        data_array = data_array.rename(
                {'x': 'longitude',
                 'y': 'latitude',
                 'band': 'time'})

        # Check if file is a VRT
        name, extension = os.path.splitext(self.fname)
        if extension.lower() == '.vrt':
            times = get_times(self.fname)
        else:
            times = get_times_from_file_band(self.fname)
        data_array['time'] = times

        # Create new dataset
        self.dataset_name = self.__get_dataset_name()
        dataset = data_array.to_dataset(name=self.dataset_name)

        # Back to default logging settings
        logging.basicConfig(level=logging.INFO)

        # Set self.data
        self.data = dataset

    def __get_dataset_name(self):
        """
        Gets dataset name from band metadata if exists
        """
        d = gdal.Open(self.fname)
        # Get band metadata
        b = d.GetRasterBand(1)
        md = b.GetMetadata()

        if 'data_var' in md:
            return md['data_var']
        else:
            return 'data'
 
    def __check_is_xarray(self, data):
        """
        Check that data is either an xarray DataArray/Dataset
        :param data: Variable to be assessed
        :return: True if it is an xarray DataArray/Dataset
                 False if it is not
        """
        if type(data) is xr.core.dataarray.DataArray or \
           type(data) is xr.core.dataarray.Dataset:

            return True
        else:
            msg = "Variable {data} is not an xarray DataArray/Dataset"
            raise Exception(msg)