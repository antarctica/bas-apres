import sys
import os

from matplotlib import pyplot as plt
from netCDF4 import Dataset

from apres.apres import ApRESFile

if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except IndexError:
        progname = os.path.basename(sys.argv[0])
        print('Usage: {} filename.{{dat,nc}} [nrows ncols]'.format(progname))
        sys.exit(2)

    (nrows, ncols) = (1, 1)

    # We can optionally plot multiple records, given a number of rows & columns
    if len(sys.argv) > 3:
        (nrows, ncols) = (int(sys.argv[2]), int(sys.argv[3]))
    
    suffix = os.path.splitext(filename)[1]

    if suffix == '.dat':
        with ApRESFile(filename) as f:
            data = f.read_data()
    elif suffix == '.nc':
        with Dataset(filename, 'r') as f:
            # We make a copy, otherwise data is invalid after file is closed
            data = f.variables['data'][:]
    else:
        raise ValueError('Unknown or unsupported file type: {}'.format(suffix))

    fig = plt.figure()

    for i in range(nrows * ncols):
        ax = fig.add_subplot(nrows, ncols, i + 1)
        ax.plot(data[i])

    plt.show()

