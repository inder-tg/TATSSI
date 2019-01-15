
import numpy as np
import gdal
import pandas as pd
from collections import OrderedDict

class Utils:

    @staticmethod
    def get_array_size(rows, cols, bands, dtype):
        """
        Get array size in human readable units
        :param rows: Number of rows
        :param cols: Number of columns
        :param bands: Number of band/layers
        :param dtype: NumPy data type
        :return: Array size in human readable units and unit
        """
        array_size = rows * cols * bands * np.dtype(dtype).itemsize
        # Return array size in GB or smaller units
        units = ['', 'kB', 'MB', 'GB']
        for unit in units:
            if abs(array_size) < 1024.0 or unit == units[-1]:
                return array_size, unit

            array_size /= 1024.0

class Constants:
    GDAL2NUMPY = {gdal.GDT_Byte: np.uint8,
                  gdal.GDT_UInt16: np.uint16,
                  gdal.GDT_Int16: np.int16,
                  gdal.GDT_UInt32: np.uint32,
                  gdal.GDT_Int32: np.int32,
                  gdal.GDT_Float32: np.float32,
                  gdal.GDT_Float64: np.float64,
                  gdal.GDT_CInt16: np.complex64,
                  gdal.GDT_CInt32: np.complex64,
                  gdal.GDT_CFloat32: np.complex64,
                  gdal.GDT_CFloat64: np.complex128
                  }

    def formats():
        """
        Create a data frame with available GDAL formats
        """
        # Lists to create data frame
        ID = []
        ShortName = []
        LongName = []
        Extension = []

        driver_dict = OrderedDict({})

        for i in range(gdal.GetDriverCount()):
            driver = gdal.GetDriver(i)

            driver_metadata = driver.GetMetadata()
            # Only add the driver to the available DQ supported formats
            # if it has and associated file name extension
            if 'DMD_EXTENSION' in driver_metadata:
                ID.append(i)
                ShortName.append(driver.ShortName)
                LongName.append(driver.LongName)
                Extension.append(driver_metadata['DMD_EXTENSION'])

                # Update dictionary
                driver_dict.update({'ID' : ID,
                                    'short_name' : ShortName,
                                    'long_name' : LongName,
                                    'extension' : Extension})


        df = pd.DataFrame(data = driver_dict)

        return df