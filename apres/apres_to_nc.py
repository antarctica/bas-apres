import argparse

from apres import ApRESFile

def main():
    parser = argparse.ArgumentParser(description='convert a raw ApRES file to a netCDF4 file')
    parser.add_argument('infile', help='ApRES raw file')
    parser.add_argument('outfile', help='converted netCDF file', default=None, nargs='?')
    args = parser.parse_args()
 
    with ApRESFile(args.infile) as f:
        f.to_netcdf(args.outfile)

if __name__ == '__main__':
    main()

