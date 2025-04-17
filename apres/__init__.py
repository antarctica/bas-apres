###############################################################################
# Project: ApRES
# Purpose: Classes to encapsulate an ApRES file
# Author:  Paul M. Breen
# Date:    2018-09-24
###############################################################################

"""
Package for working with BAS ApRES files

The package contains classes for working with ApRES .dat files.  It enables the files to be read, rewritten, and converted.
"""

__version__ = '0.4.1'

import re
import os
import sys
import warnings

import numpy as np
from netCDF4 import Dataset

class ApRESBurst(object):
    """
    Class for reading and writing ApRES bursts
    """

    DEFAULTS = {
        'autodetect_file_format_version': True,
        'forgive': True,
        'header_markers': {
            'start': '\r\n*** Burst Header ***',
            'end': '\r\n*** End Header ***'
        },
        'end_of_header_re': r'\*\*\* End Header',
        'header_line_delim': '=',
        'header_line_eol': '\r\n',
        'data_type_key': 'Average',
        'data_types': ['<u2','<f4','<u4'],
        'data_dim_keys': ['NSubBursts', 'N_ADC_SAMPLES'],
        'data_dim_optional_keys': ['nAttenuators'],
        'data_dim_order': 'C'
    }

    ALTERNATIVES = [{
            'header_line_delim': '=',
            'data_dim_keys': ['NSubBursts', 'N_ADC_SAMPLES']
        }, {
            'header_line_delim': ':',
            'data_dim_keys': ['SubBursts in burst', 'Samples']
        }
    ]

    def __init__(self, fp=None):
        """
        Constructor

        * fp is not None: Then header_start will be set to the file's current
        position.  This allows reading through a file one burst block at a
        time.  This is the normal behaviour.
        * fp is None: Allows the burst object to be populated by other means,
        rather than reading from a file

        :param fp: The open file object of the input file
        :type fp: file object
        """

        self.header_start = 0
        self.data_start = -1
        self.header_lines = []
        self.header = {}
        self.data_dim_keys = []
        self.data_shape = ()
        self.data_type = '<u2'
        self.data = None

        self.fp = fp

        if self.fp:
            self.header_start = self.fp.tell()

    def reset_init_defaults(self):
        """
        Reset the initial DEFAULTS parsing tokens from the ALTERNATIVES list
        """

        for key in self.ALTERNATIVES[0]:
            self.DEFAULTS[key] = self.ALTERNATIVES[0][key]

    def read_header_lines(self):
        """
        Read the raw header lines from the file

        * We require an encoding to ensure that we can decode the text header
          lines.  ApRESFile adds encoding to self.fp.  If encoding isn't set
          in self.fp, we fallback to ApRESFile default encoding

        :returns: The raw header lines
        :rtype: list
        """

        self.data_start = -1
        self.header_lines = []

        if not hasattr(self.fp, 'encoding'):
            self.fp.encoding = ApRESFile.DEFAULTS['file_encoding']

        self.fp.seek(self.header_start, 0)
        line = self.fp.readline()
        line = line.decode(self.fp.encoding)

        self.header_lines.append(line.rstrip())

        while(line):
            # The data section follows the end of header marker
            if re.match(self.DEFAULTS['end_of_header_re'], line):
                self.data_start = self.fp.tell()
                break

            line = self.fp.readline()
            line = line.decode(self.fp.encoding)

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

    def define_data_shape(self, flatten='unity'):
        """
        Parse the data dimensions from the header to define the data shape

        If the Average header item is non-zero, then that indicates that the
        subbursts have been aggregated to a single value, so we rewrite that
        dimension as 1

        In special cases, the data may be stored in additional dimensions.
        We detect and store these optional dimension metadata, to enable
        the data to be reshaped accordingly.  These optional dimensions are
        used according to the value of the `flatten` kwarg:

        * always: An optional dimension is always flattened, so that
          data_shape[1] is the product of itself and any optional dimensions
        * unity: An optional dimension with length == 1 is flattened into
          data_shape[1], otherwise if its length > 1, then it is stored
          as an additional dimension
        * never: An optional dimension is never flattened and is stored as
          an additional dimension

        :param flatten: Controls flattening optional dimensions.  Must be one
        of ['always','unity','never']
        :type flatten: str
        :returns: The data shape
        :rtype: tuple
        """

        self.data_dim_keys = []
        self.data_shape = ()
        data_shape = []
        opts_flatten = ['always','unity','never']

        if flatten.lower() not in opts_flatten:
            raise ValueError(f"Unsupported flatten option {flatten}, must be one of {opts_flatten}")

        for key in self.DEFAULTS['data_dim_keys']:
            self.data_dim_keys.append(key)
            data_shape.append(int(self.header[key]))

        if int(self.header[self.DEFAULTS['data_type_key']]) > 0:
            data_shape[0] = 1

        for key in self.DEFAULTS['data_dim_optional_keys']:
            try:
                m = int(self.header[key])

                if flatten.lower() == 'always':
                    data_shape[1] *= m
                elif flatten.lower() == 'unity':
                    if m > 1:
                        self.data_dim_keys.insert(1, key)
                        data_shape.insert(1, m)
                elif flatten.lower() == 'never':
                    self.data_dim_keys.insert(1, key)
                    data_shape.insert(1, m)
            except KeyError:
                pass
            except ValueError:
                warnings.warn(f"File header optional dimension key {key} has an invalid value so cannot be used as a dimension.")

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
            expected_len = int(np.prod(self.data_shape))

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

        count = int(np.prod(self.data_shape))
        self.fp.seek(self.data_start, 0)
        buf = self.fp.read(count * np.dtype(self.data_type).itemsize)
        self.data = np.frombuffer(buf, dtype=np.dtype(self.data_type), count=count)
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

    def write_header(self, fp, subbursts=None, samples=None):
        """
        Write the header to the given file object

        :param fp: The open file object of the output file
        :type fp: file object
        :param subbursts: A range specifying the subbursts to be written
        :type subbursts: range object
        :param samples: A range specifying the samples to be written
        :type samples: range object
        """

        if self.data_start == -1:
            self.read_header()

        if not hasattr(fp, 'encoding'):
            fp.encoding = ApRESFile.DEFAULTS['file_encoding']

        eol = self.DEFAULTS['header_line_eol']

        for line in self.header_lines:
            # Ensure requested subbursts & samples are reflected in the header
            if subbursts and re.match(self.DEFAULTS['data_dim_keys'][0], line):
                line = self.format_header_line(self.DEFAULTS['data_dim_keys'][0], len(subbursts))
            if samples and re.match(self.DEFAULTS['data_dim_keys'][1], line):
                line = self.format_header_line(self.DEFAULTS['data_dim_keys'][1], len(samples))

            line = line + eol
            line = line.encode(fp.encoding)

            fp.write(line)

    def write_data(self, fp, subbursts=None, samples=None):
        """
        Write the data to the given file object

        :param fp: The open file object of the output file
        :type fp: file object
        :param subbursts: A range specifying the subbursts to be written
        :type subbursts: range object
        :param samples: A range specifying the samples to be written
        :type samples: range object
        """

        if self.data_start == -1:
            self.read_data()

        if not subbursts:
            subbursts = range(self.data_shape[0])
        if not samples:
            samples = range(self.data_shape[1])

        fp.write(np.asarray(self.data[subbursts.start:subbursts.stop:subbursts.step, samples.start:samples.stop:samples.step], order=self.DEFAULTS['data_dim_order']))

class ApRESFile(object):
    """
    Context manager for reading and writing ApRES files
    """

    DEFAULTS = {
        'file_encoding': 'latin-1',
        'apres_suffix': '.dat',
        'netcdf_suffix': '.nc',
        'netcdf_add_history': True,
        'netcdf_group_name': 'burst{:d}',
        'netcdf_var_name': 'data',
        'netcdf_attrs': {
            'units': '1',
            'long_name': 'Sub Burst ADC Samples'
        }
    }

    def __init__(self, path=None, mode='rb', fs_opts={}):
        """
        Constructor

        :param path: Path to the file
        :type path: str
        :param mode: Mode in which to open the file
        :type mode: str
        :param fs_opts: Any kwargs required for opening a url using fsspec
        :type fs_opts: dict
        """

        self.path = path
        self.mode = mode
        self.fs_opts = fs_opts
        self.fp = None
        self.file_size = -1
        self.bursts = []

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

    def open(self, path=None, mode=None, fs_opts=None):
        """
        Open the given file

        * If open mode is not binary, then we force it to be so
        * We store the default encoding in self.fp so that the header can be
          correctly decoded
        * If path is an fsspec URL (e.g. s3://, gs:// etc.) then provide any
          necessary options to open the file (e.g. credentials) in fs_opts

        :param path: Path to the file
        :type path: str
        :param mode: Mode in which to open the file
        :type mode: str
        :param fs_opts: Any kwargs required for opening a url using fsspec
        :type fs_opts: dict
        :returns: This object
        :rtype: ApRESFile
        """

        if path:
            self.path = path

        if mode:
            self.mode = mode

        if fs_opts:
            self.fs_opts = fs_opts

        if 'b' not in self.mode:
            self.mode += 'b'

        # We use fsspec to load remote resources, otherwise we just open as
        # a file on the local filesystem
        if '://' in self.path:
            try:
                import fsspec
            except ImportError:
                raise ImportError("To open files on remote storage the 'remote' optional dependency must be installed: pip install bas-apres[remote]")

            protocol = self.path.split('://')[0]
            fs = fsspec.filesystem(protocol, **self.fs_opts)
            self.fp = fs.open(self.path, mode=self.mode)
            self.file_size = fs.info(self.path)['size']
            self.fp.protocol = protocol
            self.fp.remote = True
        else:
            self.fp = open(self.path, self.mode)
            self.file_size = os.fstat(self.fp.fileno()).st_size
            self.fp.remote = False

        self.fp.encoding = self.DEFAULTS['file_encoding']

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

    def eof(self):
        """
        Report whether the end-of-file has been reached

        :returns: True if EOF has been reached, False otherwise
        :rtype: bool
        """

        return self.fp.tell() >= self.file_size

    def read_burst(self):
        """
        Read a burst block from the file

        :returns: The burst
        :rtype: ApRESBurst
        """

        burst = ApRESBurst(fp=self.fp)
        burst.read_data()

        return burst

    def read(self):
        """
        Reads all burst blocks from the file

        The bursts are available in the bursts list

        :returns: The bursts
        :rtype: list
        """

        while not self.eof():
            burst = self.read_burst()
            self.bursts.append(burst)

        return self.bursts

    def to_apres_dat(self, path, bursts=None, subbursts=None, samples=None):
        """
        Write the bursts to the given file path as an ApRES .dat file

        When rewriting the ApRES data to a new file, the bursts, subbursts,
        and the ADC samples for those selected subbursts, can be subsetted.
        The bursts, subbursts, and samples keyword arguments must specify a
        range object

        :param path: The path of the output file
        :type path: str
        :param bursts: A range specifying the bursts to be written
        :type bursts: range object
        :param subbursts: A range specifying the subbursts to be written
        :type subbursts: range object
        :param samples: A range specifying the samples to be written
        :type samples: range object
        """

        if not self.bursts:
            self.read()

        if not bursts:
            bursts = range(len(self.bursts))

        with open(path, 'wb') as fout:
            for burst in self.bursts[bursts.start:bursts.stop:bursts.step]:
                burst.write_header(fout, subbursts=subbursts, samples=samples)
                burst.write_data(fout, subbursts=subbursts, samples=samples)

    def burst_to_nc_object(self, burst, nco):
        """
        Map the given burst to the given netCDF object

        The netCDF object can either be a Dataset or a Group

        :param burst: The burst
        :type burst: ApRESBurst
        :param nco: A netCDF object (one of Dataset or Group)
        :type nco: netCDF4._netCDF4.Dataset or netCDF4._netCDF4.Group
        :returns: The netCDF object
        :rtype: netCDF4._netCDF4.Dataset or netCDF4._netCDF4.Group
        """

        # Write the burst header items as netCDF object attributes
        for key in burst.header:
            nco.setncattr(key, burst.header[key])

        for key, n in zip(burst.data_dim_keys, burst.data_shape):
            nco.createDimension(key, n)

        data = nco.createVariable(self.DEFAULTS['netcdf_var_name'], burst.data_type, tuple(burst.data_dim_keys))
        data.setncatts(self.DEFAULTS['netcdf_attrs'])
        data[:] = burst.data

        return nco

    def nc_object_to_burst(self, nco):
        """
        Map the given netCDF object to an ApRESBurst object

        The netCDF object can either be a Dataset or a Group

        :param nco: A netCDF object (one of Dataset or Group)
        :type nco: netCDF4._netCDF4.Dataset or netCDF4._netCDF4.Group
        :returns: The burst object
        :rtype: ApRESBurst
        """

        # We make a copy, otherwise data is invalid after file is closed
        data = nco.variables[self.DEFAULTS['netcdf_var_name']][:]
        attrs = vars(nco).copy()

        burst = ApRESBurst()
        burst.data_start = 0              # Stop data being read from file

        # Remove any attributes that weren't part of the original burst's header
        try:
            del attrs['history']
        except KeyError:
            pass

        # Reconstruct the original burst from the parsed header and data.  We
        # initially set the header_lines to be the parsed header which allows us
        # to determine the burst format version, and thus setup the DEFAULTS
        # parsing tokens accordingly.  This then allows us to correctly
        # reconstruct the raw header lines with the appropriate header line
        # delimiter for the burst format version
        burst.data = data
        burst.header = attrs
        burst.header_lines = burst.header
        burst.determine_file_format_version()
        burst.reconstruct_header_lines()
        burst.configure_from_header()

        return burst

    def to_netcdf(self, path=None, mode='w'):
        """
        Write the bursts to the given file path as a netCDF4 file

        The default netCDF file path is the same as the input file, but with
        a .nc suffix

        :param path: The path of the output file
        :type path: str
        :param mode: Mode in which to open the file
        :type mode: str
        """

        if not self.bursts:
            self.read()

        path = path or os.path.splitext(self.path)[0] + self.DEFAULTS['netcdf_suffix']

        ncfile = Dataset(path, mode)

        # Add the command line invocation to global history attribute
        if self.DEFAULTS['netcdf_add_history']:
            ncfile.history = ' '.join(sys.argv)

        # Write each burst as a netCDF4/HDF5 group
        for i, burst in enumerate(self.bursts):
            group = ncfile.createGroup(self.DEFAULTS['netcdf_group_name'].format(i))
            self.burst_to_nc_object(burst, group)

        ncfile.close()

