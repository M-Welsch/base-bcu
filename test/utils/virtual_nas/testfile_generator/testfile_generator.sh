#!/bin/bash

echo "Cleaning up after last time"
rm -r "$BACKUP_SOURCE_DIRECTORY"

echo "Creating $AMOUNT_TESTFILES_IN_SOURCE files a $BYTESIZE_OF_EACH_SOURCEFILE into $BACKUP_SOURCE_DIRECTORY"
mkdir -p "$BACKUP_SOURCE_DIRECTORY"
for nr in $(seq 1 $AMOUNT_TESTFILES_IN_SOURCE)
do
  dd if=/dev/urandom of="$BACKUP_SOURCE_DIRECTORY/testfile$nr" bs="$BYTESIZE_OF_EACH_SOURCEFILE" count=1
done
