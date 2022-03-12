import sys
import os

from netCDF4 import Dataset

from apres import ApRESFile

APRES_SUFFIX = '.dat'

if __name__ == '__main__':
    try:
        infile = sys.argv[1]
    except IndexError:
        progname = os.path.basename(sys.argv[0])
        print('Usage: {} infile.nc [outfile.dat]'.format(progname))
        sys.exit(2)

    # We can optionally be given an explicit output filename 
    outfile = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(infile)[0] + APRES_SUFFIX

    with Dataset(infile, 'r') as f:
        # We make a copy, otherwise data is invalid after file is closed
        data = f.variables['data'][:]
        attrs = vars(f).copy()

    f = ApRESFile(path=outfile)
    f.data_start = 0              # Stop data being read from file

    # Remove any attributes that weren't part of the original file's header
    try:
        del attrs['history']
    except KeyError:
        pass

    # Reconstruct the original file from the parsed header and data.  We
    # initially set the header_lines to be the parsed header which allows us
    # to determine the file format version, and thus setup the DEFAULTS
    # parsing tokens accordingly.  This then allows us to correctly
    # reconstruct the raw header lines with the appropriate header line
    # delimiter for the file format version
    f.data = data
    f.header = attrs
    f.header_lines = f.header
    f.determine_file_format_version()
    f.reconstruct_header_lines()
    f.configure_from_header()
    f.to_apres_dat(outfile)

