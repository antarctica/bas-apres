# apres

This project enables ApRES .dat files to be read, rewritten, and converted.

## The apres package

The apres package contains a number of classes for working with ApRES .dat files.

* The `ApRESBurst` class manages reading/writing a single burst block (the textual header and the binary data) from/to an opened ApRES .dat file.
* The `ApRESFile` class is a context manager for ApRES .dat files.  The class wraps the `ApRESBurst` class and can read a variable number of burst blocks from a file (i.e. a single burst file or a timeseries file).  It also contains methods for subsetting an ApRES file, and for converting the file to netCDF4.

## Install

The package can be installed from PyPI (note the package distribution name):

```bash
$ pip install bas-apres
```

## Simple utility scripts

The package contains a number of scripts for converting from/to netCDF, plotting the data etc.  When installing the package (e.g., via `pip install`) then these scripts are available as commands and added to the `PATH`.  So for instance, you can just call `apres_to_nc`.  If running the scripts from a `clone` of the source code repository, then they need to be run as modules, e.g. `python -m apres.apres_to_nc`.

### apres_to_nc.py

This script converts an ApRES .dat file to netCDF4.  The default output netCDF filename has the same name as the input .dat file, but with a .nc file suffix.  Optionally an alternative output netCDF filename can be explicitly given.

```bash
python3 -m apres.apres_to_nc filename.dat [outfile.nc]
```

The conversion is a straightforward mapping, in that each burst becomes a netCDF4 group, where the header lines become group attributes, and the data are stored as the group data.  How the data are stored depends on the number of attenuators used when acquiring the data:

* Single-attenuator configuration: The data are stored as a `NSubBursts` x `N_ADC_SAMPLES` 2D data array.
* Multi-attenuator configuration: The data are stored as a `NSubBursts` x `N_ADC_SAMPLES` x `nAttenuators` 3D data array.

### nc_to_apres.py

This script converts a previously converted netCDF4 file back to the original ApRES .dat file.  The default output ApRES .dat filename has the same name as the input netCDF file, but with a .dat file suffix.  Optionally an alternative output ApRES filename can be explicitly given.

```bash
python3 -m apres.nc_to_apres infile.nc [outfile.dat]
```

The conversion is a straightforward reversal of the original conversion.  For the newer ApRES .dat file format version, this should be identical to the original file.  For the older ApRES .dat file format version, there will likely be small differences in the whitespace in the textual header.  Ignoring these insignificant changes in whitespace (e.g. `diff -awB orig.dat reconstructed.dat`), the files will be identical.

### plot_apres.py

This script will plot the `N_ADC_SAMPLES` vs `NSubBursts` as a radargram, for each burst in the file (or group for converted netCDF files).  If the `Average` header item > 0 (and so each subburst has been aggregated), then the script will instead plot the first subburst as a single trace.  If the `nAttenuators` header item > 1, then each attenuator's data are plotted separately.  The file can be either an ApRES .dat file, or a converted netCDF file.

```bash
python3 -m apres.plot_apres [-h] [-r | -t] [-g GRID GRID] [-c CONTRAST] [-m CMAP]
                            filename.{dat,nc}

plot ApRES data, either from a .dat file, or a converted netCDF file

positional arguments:
  filename              filename

optional arguments:
  -h, --help            show this help message and exit
  -r, --radargram       plot a radargram
  -t, --traces          plot individual traces
  -g GRID GRID, --grid GRID GRID
                        plot the first nrows x ncols traces
  -c CONTRAST, --contrast CONTRAST
                        contrast for the radargram
  -m CMAP, --cmap CMAP  colour map for the radargram

Examples

Plot the given ApRES .dat file as a radargram:

python3 -m apres.plot_apres filename.dat

Plot the given converted netCDF file as a radargram:

python3 -m apres.plot_apres filename.nc

Plot the given ApRES file as a radargram, increasing the contrast:

python3 -m apres.plot_apres -c 10 filename.dat

Same as above, but with a blue-white-red colour map:

python3 -m apres.plot_apres -c 10 -m bwr filename.dat

Plot the first trace from the given ApRES file:

python3 -m apres.plot_apres -t filename.dat

Plot the first 6 traces, in a 3x2 grid:

python3 -m apres.plot_apres -t -g 3 2 filename.dat
```

### read_apres.py

This script will read the given ApRES .dat file, and for each burst, print the results of parsing the header, such as the dimensions of the data array, and the parsed header dictionary.  It will also *head* the data section (by default the first 10 samples of the first 10 subbursts), to give an initial simple look at the data.  If the data were acquired using multiple attenuators, then the number of samples shown will be multiplied by the number of attenuators.

The script's primary purpose is as a simple example of how to use the `ApRESFile` class to read an ApRES .dat file.

```bash
python3 -m apres.read_apres filename.dat
```

### write_apres.py

This script will read the given input ApRES .dat file, and for each burst, write the header and data to the given output ApRES .dat file.  Optionally a subset of bursts can be written out, specified as the first `bursts` bursts of the input file.  In addition a subset of each burst can be written out, specified as the first `subbursts` subbursts, and the first `samples` ADC samples of these subbursts.  If `bursts`, `subbursts` and `samples` are not specified, then the output file is identical to the input file.

The script's primary purpose is as a simple example of how to use the `ApRESFile` class to rewrite an ApRES .dat file.

```bash
python3 -m apres.write_apres [-b BURSTS] [-u SUBBURSTS] [-s SAMPLES] infile.dat outfile.dat
```

