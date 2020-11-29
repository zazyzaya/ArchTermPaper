#!/bin/bash
OUT_DIR=ArchPaper/thicc/

if [ -f $OUT_DIR$2 ]; then
        echo "File $OUT_DIR$2 already exists"
        exit
fi

./dineroIV \
-l1-dsize 32k -l1-dbsize 256 -l1-dassoc 16 -l1-drepl l \
-l1-isize 32k -l1-ibsize 64 -l1-iassoc 8 -l1-irepl l \
-l2-usize 256k -l2-ubsize 256 -l2-uassoc 8 -l2-urepl l \
-informat d < ArchPaper/dinfiles/$1 > $OUT_DIR$2