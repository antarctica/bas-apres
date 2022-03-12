import sys
import os

from apres import ApRESFile

if __name__ == '__main__':
    try:
        infile = sys.argv[1]
        outfile = sys.argv[2]
    except IndexError:
        progname = os.path.basename(sys.argv[0])
        print('Usage: {} infile.dat outfile.dat [records [samples]]'.format(progname))
        sys.exit(2)

    (records, samples) = (None, None)

    # We can optionally select a subset of records and/or samples for output
    if len(sys.argv) > 3:
        records = range(int(sys.argv[3]))
    if len(sys.argv) > 4:
        samples = range(int(sys.argv[4]))
 
    with ApRESFile(infile) as f:
        f.to_apres_dat(outfile, records=records, samples=samples)

