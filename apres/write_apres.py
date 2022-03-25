import argparse

from apres import ApRESFile

def main():
    parser = argparse.ArgumentParser(description='read a raw ApRES file and write to another raw ApRES file, optionally subsetting the data ')
    parser.add_argument('infile', help='ApRES raw file')
    parser.add_argument('outfile', help='ApRES raw file')
    parser.add_argument('-b', '--bursts', help='only write out the first BURSTS bursts', dest='bursts', default=None, type=int)
    parser.add_argument('-u', '--subbursts', help='only write out the first SUBBURSTS subbursts', dest='subbursts', default=None, type=int)
    parser.add_argument('-s', '--samples', help='only write out the first SAMPLES ADC samples', dest='samples', default=None, type=int)
    args = parser.parse_args()

    # We can optionally select a subset of bursts, subbursts and/or samples
    # for output.  These have to be range objects
    if args.bursts:
        args.bursts = range(args.bursts)
    if args.subbursts:
        args.subbursts = range(args.subbursts)
    if args.samples:
        args.samples = range(args.samples)
 
    with ApRESFile(args.infile) as f:
        f.to_apres_dat(args.outfile, bursts=args.bursts, subbursts=args.subbursts, samples=args.samples)

if __name__ == '__main__':
    main()

