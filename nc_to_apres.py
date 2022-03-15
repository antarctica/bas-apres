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
    fout = ApRESFile(path=outfile)

    with Dataset(infile, 'r') as fin:
        # Convert each netCDF group to an ApRESBurst object
        for key in fin.groups:
            burst = fout.nc_object_to_burst(fin.groups[key])
            fout.bursts.append(burst)

    fout.to_apres_dat(outfile)

