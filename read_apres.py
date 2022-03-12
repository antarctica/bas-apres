import sys
import os

from apres import ApRESFile

if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except IndexError:
        progname = os.path.basename(sys.argv[0])
        print('Usage: {} filename.dat'.format(progname))
        sys.exit(2)

    with ApRESFile(filename) as f:
        header = f.read_header()
        print('header: data_start = {}'.format(f.data_start))
        print('header: data_shape = {}'.format(f.data_shape))
        print('header: dict = ')
        print(header)

        data = f.read_data()
        print('data: len(data) = {}'.format(len(data)))
        print('data: data.size = {}'.format(data.size))
        print('data: data.shape = {}'.format(data.shape))

        # Show a small selection of the first records and samples
        if len(data) > 0:
            nrecords = 10 if data.shape[0] > 10 else data.shape[0]
            nsamples = 10 if data.shape[1] > 10 else data.shape[1]
            print('data: head = ')
            print(data[0:nrecords, 0:nsamples])

