import argparse

from apres import ApRESFile

def main():
    parser = argparse.ArgumentParser(description='read a raw ApRES file and write to another raw ApRES file, optionally subsetting the data ')
    parser.add_argument('infile', help='ApRES raw file')
    parser.add_argument('outfile', help='ApRES raw file')
    parser.add_argument('-r', '--records', help='only write out the first RECORDS sub bursts', dest='records', default=None, type=int)
    parser.add_argument('-s', '--samples', help='only write out the first SAMPLES ADC samples', dest='samples', default=None, type=int)
    args = parser.parse_args()

    # We can optionally select a subset of records and/or samples for output.
    # These have to be range objects
    if args.records:
        args.records = range(args.records)
    if args.samples:
        args.samples = range(args.samples)
 
    with ApRESFile(args.infile) as f:
        f.to_apres_dat(args.outfile, records=args.records, samples=args.samples)

if __name__ == '__main__':
    main()

