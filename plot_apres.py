import sys
import os
import argparse

from matplotlib import pyplot as plt
import numpy as np
from netCDF4 import Dataset

from apres import ApRESFile

def construct_radargram(plt, mat, xaxis, yaxis, xlim=None, ylim=None, xlabel='NSubBursts', ylabel='N_ADC_SAMPLES', contrast=1.0, cmap='gray', aspect='auto'):
    """
    Plot the given data as a radargram

    :param plt: The plot object
    :type plt: matplotlib.pyplot
    :param mat: The data with each sub burst (trace) as a column of a matrix
    :type mat: numpy.matrix
    :param xaxis: The x-axis values (of length NSubBursts)
    :type xaxis: numpy.ndarray
    :param yaxis: The y-axis values (of length N_ADC_SAMPLES)
    :type yaxis: numpy.ndarray
    :param xlim: The x-axis limits (defaults to [min(xaxis), max(xaxis)])
    :type xlim: list
    :param ylim: The y-axis limits (defaults to [max(yaxis), min(yaxis)])
    :type ylim: list
    :param xlabel: The x-axis label
    :type xlabel: str
    :param ylabel: The y-axis label
    :type ylabel: str
    :param contrast: The plot contrast factor
    :type contrast: float
    :param cmap: The plot colour map name (can be any supported by matplotlib)
    :type cmap: str
    :param aspect: The plot aspect ratio
    :type aspect: str
    """

    dx = xaxis[1] - xaxis[0]
    dy = yaxis[1] - yaxis[0]
    xlim = xlim or [min(xaxis), max(xaxis)]
    ylim = ylim or [max(yaxis), min(yaxis)]
    extent = [min(xaxis) - dx/2.0, max(xaxis) + dx/2.0, max(yaxis) + dy/2.0, min(yaxis) - dy/2.0]
    std_contrast = np.nanmax(np.abs(mat)[:])

    plt.imshow(mat, cmap=cmap, extent=extent, aspect=aspect, vmin=-std_contrast/contrast, vmax=std_contrast/contrast)

    plt.gca().set_xlabel(xlabel)
    plt.gca().set_ylabel(ylabel)
    plt.xlim(xlim)
    plt.ylim(ylim)

def parse_cmdln():
    """
    Parse the command line options and arguments

    :returns: The parsed command line arguments object
    :rtype: argparse.Namespace object
    """

    epilog = """Examples

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
"""

    parser = argparse.ArgumentParser(description='plot ApRES data, either from a .dat file, or a converted netCDF file', epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('filename', help='filename')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-r', '--radargram', help='plot a radargram', action='store_const', dest='type', const='radargram')
    group.add_argument('-t', '--traces', help='plot individual traces', action='store_const', dest='type', const='traces')
    parser.set_defaults(type='radargram')

    parser.add_argument('-g', '--grid', help='plot the first nrows x ncols traces', dest='grid', nargs=2, default=[1, 1], type=int)
    parser.add_argument('-c', '--contrast', help='contrast for the radargram', dest='contrast', default=1.0, type=float)
    parser.add_argument('-m', '--cmap', help='colour map for the radargram', dest='cmap', default='gray')

    args = parser.parse_args()

    return args

if __name__ == '__main__':
    args = parse_cmdln()
    suffix = os.path.splitext(args.filename)[1]

    if suffix.lower() == '.dat':
        with ApRESFile(args.filename) as f:
            data = f.read_data()

            # Can't plot a radargram for aggregated data
            if int(f.header['Average']) > 0:
                args.type = 'traces'
    elif suffix.lower() == '.nc':
        with Dataset(args.filename, 'r') as f:
            # We make a copy, otherwise data is invalid after file is closed
            data = f.variables['data'][:]

            # Can't plot a radargram for aggregated data
            if int(f.getncattr('Average')) > 0:
                args.type = 'traces'
    else:
        raise ValueError('Unknown or unsupported file type: {}'.format(suffix))

    if args.type == 'traces':
        (nrows, ncols) = args.grid
        fig = plt.figure()

        for i in range(nrows * ncols):
            ax = fig.add_subplot(nrows, ncols, i + 1)
            ax.plot(data[i])

        fig.supxlabel('Samples')
        fig.supylabel('Amplitude')
    else:
        ntraces = int(data.shape[0])
        npoints = int(data.shape[1])
        xaxis = np.linspace(1.0, float(ntraces), int(ntraces))
        yaxis = np.linspace(0.0, float(npoints), int(npoints))
        cols = np.zeros((npoints, ntraces))

        for i, trace in enumerate(data):
            cols[:,i] = trace

        mat = np.asmatrix(cols)

        # Plot the vertical traces as a radargram
        construct_radargram(plt, mat, xaxis, yaxis, contrast=args.contrast, cmap=args.cmap)

    plt.suptitle(os.path.basename(args.filename))
    plt.show()

