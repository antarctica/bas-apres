import argparse

from apres import ApRESFile

def main():
    parser = argparse.ArgumentParser(description='print the header, a sample of the data, and diagnostics, from the given raw ApRES file')
    parser.add_argument('infile', help='ApRES raw file')
    args = parser.parse_args()

    with ApRESFile(args.infile) as f:
        for burst in f.read():
            header = burst.header
            print(f'header: header_start = {burst.header_start}')
            print(f'header: data_start = {burst.data_start}')
            print(f'header: data_dim_keys = {burst.data_dim_keys}')
            print(f'header: data_shape = {burst.data_shape}')
            print(f'header: dict = ')
            print(header)


            data = burst.data
            print(f'data: len(data) = {len(data)}')
            print(f'data: data.size = {data.size}')
            print(f'data: data.shape = {data.shape}')

            # Show a small selection of the first subbursts and samples
            if len(data) > 0:
                nsubbursts = 10 if data.shape[0] > 10 else data.shape[0]
                nsamples = 10 if data.shape[1] > 10 else data.shape[1]
                print('data: head = ')
                print(data[0:nsubbursts, 0:nsamples])

        print(f'number of bursts = {len(f.bursts)}')

if __name__ == '__main__':
    main()

