#!/bin/bash

###############################################################################
# Project: ApRES
# Purpose: Test script to drive the two-way conversion scripts from
#          ApRES .dat -> netCDF .nc -> recovered ApRES .dat
# Author:  Paul M. Breen
# Date:    2022-03-14
###############################################################################

PROGNAME=`basename "$0"`

DEF_TMP_DIR="/tmp"
NC_FILE="converted.nc"
RECOVERED_FILE="recovered.dat"

###############################################################################
# Function to create a temporary working directory
###############################################################################
function create_tmp_dir
{
  local retval

  # Attempt to create a temp. directory in which to process output
  tmp_dir=`mktemp -d ${DEF_TMP_DIR}/${PROGNAME}.XXXXXXXX`
  retval=$?

  if [ $retval -ne 0 ]
  then
    echo "$PROGNAME: Failed to create temp. directory" 1>&2
    exit $retval
  fi

  return $retval
}



###############################################################################
# Main function
###############################################################################

test $# -lt 1 && echo "Usage: $PROGNAME in_file.dat" && exit 2
in_file="$1"

create_tmp_dir
trap "test -d \"$tmp_dir\" && rm -rf \"$tmp_dir\"" EXIT

nc_file="$tmp_dir/$NC_FILE"
recovered_file="$tmp_dir/$RECOVERED_FILE"

python -m apres.apres_to_nc "$in_file" "$nc_file"
python -m apres.nc_to_apres "$nc_file" "$recovered_file"

# * For V1 ApRES format files, we can recover the original .dat from
#   a converted .nc file, except for a trivial difference in whitespace in the
#   header between the header key and value
# * For V2 ApRES format files, we can recover the original .dat exactly from
#   a converted .nc file
# Hence the two different comparisons.  For V1, diff will show the trivial
# differences
sha1sum "$in_file" "$recovered_file"
diff -a "$in_file" "$recovered_file"

exit $?

