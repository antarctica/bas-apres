###############################################################################
# Project: ApRES
# Purpose: Class to encapsulate an ApRES file
# Author:  Paul M. Breen
# Date:    2018-09-24
###############################################################################

import re
import os
import sys
import warnings

import numpy as np
from netCDF4 import Dataset

class ApRESFile(object):
    """
    Context manager for reading and writing ApRES files
    """

    DEFAULTS = {
        'autodetect_file_format_version': True,
        'forgive': True,
        'file_encoding': 'latin-1',
        'header_markers': {
            'start': '\r\n*** Burst Header ***',
            'end': '\r\n*** End Header ***'
        },
        'end_of_header_re': '\*\*\* End Header',
        'header_line_delim': '=',
        'header_line_eol': '\r\n',
        'data_type_key': 'Average',
        'data_types': ['<u2','<u2','<u4'],
        'data_dim_keys': ['NSubBursts', 'N_ADC_SAMPLES'],
        'data_dim_order': 'C',
        'netcdf_suffix': '.nc',
        'netcdf_add_history': True,
        'netcdf_attrs': {
            'units': '1',
            'long_name': 'Sub Burst ADC Samples'
        }
    }

    ALTERNATIVES = [{
            'header_line_delim': '=',
            'data_dim_keys': ['NSubBursts', 'N_ADC_SAMPLES']
        }, {
            'header_line_delim': ':',
            'data_dim_keys': ['SubBursts in burst', 'Samples']
        }
    ]

    def __init__(self, path=None):
        """
        Constructor

        :param path: Path to the file
        :type path: str
        """

        self.path = path
        self.fp = None
        self.header_start = 0
        self.data_start = -1
        self.header_lines = []
        self.header = {}
        self.data_shape = ()
        self.data_type = '<u2'
        self.data = None

    def __enter__(self):
        """
        Enter the runtime context for this object

        The file is opened

        :returns: This object
        :rtype: ApRESFile
        """

        return self.open(self.path)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """
        Exit the runtime context for this object

        The file is closed

        :returns: False
        :rtype: bool
        """

        self.close()

        return False         # This ensures any exception is re-raised

    def open(self, path=None, mode='r'):
        """
        Open the given file

        :param path: Path to the file
        :type path: str
        :param mode: Mode in which to open the file
        :type mode: str
        :returns: This object
        :rtype: ApRESFile
        """

        if path:
            self.path = path

        self.fp = open(self.path, mode, encoding=self.DEFAULTS['file_encoding'])

        return self

    def close(self):
        """
        Close the file

        :returns: This object
        :rtype: ApRESFile
        """

        self.fp.close()
        self.fp = None

        return self

    def reset_init_defaults(self):
        """
        Reset the initial DEFAULTS parsing tokens from the ALTERNATIVES list
        """

        for key in self.ALTERNATIVES[0]:
            self.DEFAULTS[key] = self.ALTERNATIVES[0][key]

    def read_header_lines(self):
        """
        Read the raw header lines from the file

        :returns: The raw header lines
        :rtype: list
        """

        self.data_start = -1
        self.header_lines = []

        self.fp.seek(self.header_start, 0)
        line = self.fp.readline()
        self.header_lines.append(line.rstrip())

        while(line):
            # The data section follows the end of header marker
            if re.match(self.DEFAULTS['end_of_header_re'], line):
                self.data_start = self.fp.tell()
                break

            line = self.fp.readline()
            self.header_lines.append(line.rstrip())

        return self.header_lines

    def determine_file_format_version(self):
        """
        Determine the file format version from the read header lines

        The header lines are inspected to determine the file format version,
        and the DEFAULTS parsing tokens are setup accordingly
        """

        # Create a list of the first data dimension key from the alternative
        # file formats
        dim_keys = [item['data_dim_keys'][0] for item in self.ALTERNATIVES]

        # Search the header lines for one of the keys, to determine version
        for line in self.header_lines:
            for i, key in enumerate(dim_keys):
                if re.match(key, line):
                    for key in self.ALTERNATIVES[i]:
                        self.DEFAULTS[key] = self.ALTERNATIVES[i][key]
                    return

    def store_header(self):
        """
        Store the read header lines as parsed key/value pairs

        :returns: The parsed header
        :rtype: dict
        """

        self.header = {}

        for line in self.header_lines:
            item = line.split(self.DEFAULTS['header_line_delim'], maxsplit=1)

            if len(item) > 1 and item[0]:
                self.header[item[0].strip()] = item[1].strip()

        return self.header

    def define_data_shape(self):
        """
        Parse the data dimensions from the header to define the data shape

        If the Average header item is non-zero, then that indicates that the
        subbursts have been aggregated to a single value, so we rewrite that
        dimension as 1

        :returns: The data shape
        :rtype: tuple
        """

        self.data_shape = ()
        data_shape = []

        for key in self.DEFAULTS['data_dim_keys']:
            data_shape.append(int(self.header[key]))

        if int(self.header[self.DEFAULTS['data_type_key']]) > 0:
            data_shape[0] = 1

        self.data_shape = tuple(data_shape)

        return self.data_shape

    def define_data_type(self):
        """
        The Average item from the header is used to define the data type

        Average = 0: Record contains all subbursts as 16-bit ints
        Average = 1: Record contains the averaged subbursts as a 16-bit int
        Average = 2: Record contains the stacked subbursts as a 32-bit int

        :returns: The data type
        :rtype: str
        """

        try:
            self.data_type = self.DEFAULTS['data_types'][int(self.header[self.DEFAULTS['data_type_key']])]
        except IndexError as e:
            raise IndexError('Unsupported Averaging/Stacking configuration option found in header: {}'.format(int(self.header[self.DEFAULTS['data_type_key']])))

        return self.data_type

    def configure_from_header(self):
        """
        Configure the object from the raw header lines

        :returns: The parsed header
        :rtype: dict
        """

        if self.DEFAULTS['autodetect_file_format_version']:
            self.determine_file_format_version()

        self.store_header()
        self.define_data_shape()
        self.define_data_type()

        return self.header

    def read_header(self):
        """
        Read the header from the file

        * The raw header lines are available in the header_lines list
        * The parsed header is available in the header dict
        * The file offset to the start of the data is available in data_start
        * The data shape is available in the data_shape tuple
        * The data type is available in data_type

        :returns: The parsed header
        :rtype: dict
        """

        # The header lines are used to configure this object
        self.read_header_lines()
        self.configure_from_header()

        return self.header

    def reshape_data(self):
        """
        Reshape the data according to the data_shape tuple

        If the data read from the file don't conform to the expected
        data_shape as determined from the header, then when reshaping the data,
        an exception will occur:

        * If the reshaping fails because the data array is shorter than
        expected, then we will reraise the exception.
        * If forgive mode is True, then we will emit a warning and then
        truncate the data to conform to the data_shape, otherwise we will
        reraise the exception.

        :returns: The data
        :rtype: numpy.array
        """

        try:
            self.data = np.reshape(self.data, self.data_shape, order=self.DEFAULTS['data_dim_order'])
        except ValueError as e:
            expected_len = self.data_shape[0] * self.data_shape[1]

            if self.data.size < expected_len:
                warnings.warn("Data array read from file doesn't match data_shape as read from the file header: {}. It is shorter than expected. Cannot continue.")
                raise
            elif self.data.size > expected_len:
                warnings.warn("Data array read from file doesn't match data_shape as read from the file header. It is longer than expected.")

                if self.DEFAULTS['forgive']:
                    warnings.warn("{}. Will truncate data to fit to data_shape.".format(e))
                    self.data = np.reshape(self.data[:expected_len], self.data_shape, order=self.DEFAULTS['data_dim_order'])
                else:
                    raise

        return self.data

    def read_data(self):
        """
        Read the data from the file

        The data are available in the data array, shaped according to the
        data_shape tuple

        :returns: The data
        :rtype: numpy.array
        """

        if self.data_start == -1:
            self.read_header()

        self.fp.seek(self.data_start, 0)
        self.data = np.fromfile(self.fp, dtype=np.dtype(self.data_type))
        self.reshape_data()

        return self.data

    def format_header_line(self, key, value):
        """
        Format a raw header line from the given key and value

        :param key: The header item key
        :type key: str
        :param value: The header item value
        :type value: str
        :returns: The formatted raw header line
        :rtype: str
        """

        return '{}{}{}'.format(key, self.DEFAULTS['header_line_delim'], value)

    def reconstruct_header_lines(self):
        """
        Reconstruct the raw header lines from the parsed header

        :returns: The reconstructed raw header lines
        :rtype: list
        """

        self.header_lines = [self.format_header_line(k,v) for k,v in self.header.items()]
        self.header_lines.insert(0, self.DEFAULTS['header_markers']['start'])
        self.header_lines.append(self.DEFAULTS['header_markers']['end'])

        return self.header_lines

    def write_header(self, fp, records=None, samples=None):
        """
        Write the header to the given file object

        :param fp: The open file object of the output file
        :type fp: file object
        :param records: A range specifying the records to be written
        :type records: range object
        :param samples: A range specifying the samples to be written
        :type samples: range object
        """

        if self.data_start == -1:
            self.read_header()

        eol = self.DEFAULTS['header_line_eol']

        for line in self.header_lines:
            # Ensure requested records & samples are reflected in the header
            if records and re.match(self.DEFAULTS['data_dim_keys'][0], line):
                line = self.format_header_line(self.DEFAULTS['data_dim_keys'][0], len(records))
            if samples and re.match(self.DEFAULTS['data_dim_keys'][1], line):
                line = self.format_header_line(self.DEFAULTS['data_dim_keys'][1], len(samples))

            fp.write(line + eol)

    def write_data(self, fp, records=None, samples=None):
        """
        Write the data to the given file object

        :param fp: The open file object of the output file
        :type fp: file object
        :param records: A range specifying the records to be written
        :type records: range object
        :param samples: A range specifying the samples to be written
        :type samples: range object
        """

        if self.data_start == -1:
            self.read_data()

        if not records:
            records = range(self.data_shape[0])
        if not samples:
            samples = range(self.data_shape[1])

        fp.write(np.asarray(self.data[records.start:records.stop:records.step, samples.start:samples.stop:samples.step], order=self.DEFAULTS['data_dim_order']))

    def to_apres_dat(self, path, records=None, samples=None):
        """
        Write the header and data to the given file path as an ApRES .dat file

        When rewriting the ApRES data to a new file, the sub bursts (records),
        and the ADC samples for those selected records, can be subsetted.  The
        records and samples keyword arguments must specify a range object

        :param path: The path of the output file
        :type path: str
        :param records: A range specifying the records to be written
        :type records: range object
        :param samples: A range specifying the samples to be written
        :type samples: range object
        """

        if self.data_start == -1:
            self.read_data()

        # The ApRES .dat file format is a mixed mode file.  The header is
        # text, and the data section is binary
        with open(path, 'w') as fout:
            self.write_header(fout, records=records, samples=samples)

        with open(path, 'ab') as fout:
            self.write_data(fout, records=records, samples=samples)

    def to_netcdf(self, path=None, mode='w'):
        """
        Write the header and data to the given file path as a netCDF4 file

        The default netCDF file path is the same as the input file, but with
        a .nc suffix

        :param path: The path of the output file
        :type path: str
        :param mode: Mode in which to open the file
        :type mode: str
        """

        if self.data_start == -1:
            self.read_data()

        path = path or os.path.splitext(self.path)[0] + self.DEFAULTS['netcdf_suffix']
        i = 0

        ncfile = Dataset(path, mode)

        # Write the file header items as global attributes
        for key in self.header:
            ncfile.setncattr(key, self.header[key])

        # Add the command line invocation to global history attribute
        if self.DEFAULTS['netcdf_add_history']:
            ncfile.history = ' '.join(sys.argv)

        for key in self.DEFAULTS['data_dim_keys']:
            ncfile.createDimension(key, self.data_shape[i])
            i += 1

        data = ncfile.createVariable('data', self.data_type, tuple(self.DEFAULTS['data_dim_keys']))
        data.setncatts(self.DEFAULTS['netcdf_attrs'])
        data[:] = self.data

        ncfile.close()

