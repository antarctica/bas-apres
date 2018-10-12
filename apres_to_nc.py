import sys
import os

from apres.apres import ApRESFile

if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except IndexError:
        progname = os.path.basename(sys.argv[0])
        print('Usage: {} filename.dat'.format(progname))
        sys.exit(2)

    with ApRESFile(filename) as f:
        f.to_netcdf()

