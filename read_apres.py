import argparse

from apres import ApRESFile

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='print the header, a sample of the data, and diagnostics, from the given raw ApRES file')
    parser.add_argument('infile', help='ApRES raw file')
    args = parser.parse_args()

    with ApRESFile(args.infile) as f:
        for burst in f.read():
            header = burst.header
            print('header: header_start = {}'.format(burst.header_start))
            print('header: data_start = {}'.format(burst.data_start))
            print('header: data_shape = {}'.format(burst.data_shape))
            print('header: dict = ')
            print(header)

            data = burst.data
            print('data: len(data) = {}'.format(len(data)))
            print('data: data.size = {}'.format(data.size))
            print('data: data.shape = {}'.format(data.shape))

            # Show a small selection of the first records and samples
            if len(data) > 0:
                nrecords = 10 if data.shape[0] > 10 else data.shape[0]
                nsamples = 10 if data.shape[1] > 10 else data.shape[1]
                print('data: head = ')
                print(data[0:nrecords, 0:nsamples])

        print(f'number of bursts = {len(f.bursts)}')

