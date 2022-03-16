## apres

This project enables ApRES .dat files to be read, rewritten, and converted.

### The apres package

The apres package contains a number of classes for working with ApRES .dat files.

* The `ApRESBurst` class manages reading/writing a single burst block (the textual header and the binary data) from/to an opened ApRES .dat file.
* The `ApRESFile` class is a context manager for ApRES .dat files.  The class wraps the `ApRESBurst` class and can read a variable number of burst blocks from a file (i.e. a single burst file or a timeseries file).  It also contains methods for subsetting an ApRES file, and for converting the file to netCDF4.

### Simple utility scripts

#### apres_to_nc.py

This script converts an ApRES .dat file to netCDF4.  The default output netCDF filename has the same name as the input .dat file, but with a .nc file suffix.  Optionally an alternative output netCDF filename can be explicitly given.

```bash
python3 apres_to_nc.py filename.dat [outfile.nc]
```

The conversion is a straightforward mapping, in that each burst becomes a netCDF4 group, where the header lines become group attributes, and the data are stored as a `NSubBursts` x `N_ADC_SAMPLES` 2D data array.

#### nc_to_apres.py

This script converts a previously converted netCDF4 file back to the original ApRES .dat file.  The default output ApRES .dat filename has the same name as the input netCDF file, but with a .dat file suffix.  Optionally an alternative output ApRES filename can be explicitly given.

```bash
python3 nc_to_apres.py infile.nc [outfile.dat]
```

The conversion is a straightforward reversal of the original conversion.  For the newer ApRES .dat file format version, this should be identical to the original file.  For the older ApRES .dat file format version, there will likely be small differences in the whitespace in the textual header.  Ignoring these insignificant changes in whitespace (e.g. `diff -awB orig.dat reconstructed.dat`), the files will be identical.

#### plot_apres.py

This script will plot the `N_ADC_SAMPLES` vs `NSubBursts` as a radargram, for each burst in the file (or group for converted netCDF files).  If the `Average` header item > 0 (and so each sub burst has been aggregated), then the script will instead plot the first sub burst as a single trace.  The file can be either an ApRES .dat file, or a converted netCDF file.

```bash
python3 plot_apres.py [-h] [-r | -t] [-g GRID GRID] [-c CONTRAST] [-m CMAP]
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

python3 plot_apres.py filename.dat

Plot the given converted netCDF file as a radargram:

python3 plot_apres.py filename.nc

Plot the given ApRES file as a radargram, increasing the contrast:

python3 plot_apres.py -c 10 filename.dat

Same as above, but with a blue-white-red colour map:

python3 plot_apres.py -c 10 -m bwr filename.dat

Plot the first trace from the given ApRES file:

python3 plot_apres.py -t filename.dat

Plot the first 6 traces, in a 3x2 grid:

python3 plot_apres.py -t -g 3 2 filename.dat
```

#### read_apres.py

This script will read the given ApRES .dat file, and for each burst, print the results of parsing the header, such as the dimensions of the data array, and the parsed header dictionary.  It will also *head* the data section (by default the first 10 samples of the first 10 sub burts), to give an initial simple look at the data.

The script's primary purpose is as a simple example of how to use the `ApRESFile` class to read an ApRES .dat file.

```bash
python3 read_apres.py filename.dat
```

#### write_apres.py

This script will read the given input ApRES .dat file, and for each burst, write the header and data to the given output ApRES .dat file.  Optionally a subset of each input burst can be written out, specified as the first `records` sub burts, and the first `samples` ADC samples of these records.  If `records` and `samples` are not specified, then the output file is identical to the input file.

The script's primary purpose is as a simple example of how to use the `ApRESFile` class to rewrite an ApRES .dat file.

```bash
python3 write_apres.py [-r RECORDS] [-s SAMPLES] infile.dat outfile.dat
```

