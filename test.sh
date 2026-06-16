#!/bin/sh
#
# Smoke tests for pcutil.py

set -e

create_test_dirs() {
    rm -rf $1/test $1/test.orig
    mkdir -p $1/test/d1
    mkdir $1/test/d2
    mkdir $1/test/d3
    mkdir $1/test/d2/d4
    echo 'x contents' >$1/test/x
    echo 'y contents' >$1/test/y
    echo 'z contents' >$1/test/z
    cp $1/test/x $1/test/y $1/test/z $1/test/d2
    cp $1/test/x $1/test/y $1/test/z $1/test/d3
    cp $1/test/x $1/test/y $1/test/z $1/test/d2/d4
}

echo "Running smoke test of pcutil.py. Expect no errors."
TMP=$(mktemp -d)
PTMP=$(echo $TMP|sed -e 's!/tmp/tmp.!!')

create_test_dirs ${TMP}

python pcutil.py cp -d pcutil.py p:/${PTMP}/new_pcutil.py
python pcutil.py cp pcutil.py p:/${PTMP}/new_pcutil.py

python pcutil.py cp -d pcutil.py p:/${PTMP}
python pcutil.py cp pcutil.py p:/${PTMP}

python pcutil.py cp -d p:/${PTMP}/new_pcutil.py ${TMP}/test/new1_pcutil.py
python pcutil.py cp p:/${PTMP}/new_pcutil.py ${TMP}/new1_pcutil.py
ls -l ${TMP}/new1_pcutil.py

python pcutil.py cp pcutil.py p:/${PTMP}/nd1/nd2/pcutil.py
python pcutil.py cp p:/${PTMP}/nd1/nd2/pcutil.py ${TMP}
ls -l ${TMP}/pcutil.py

python pcutil.py cp -d p:/${PTMP}/new_pcutil.py ${TMP}/new1_pcutil.py
python pcutil.py cp p:/${PTMP}/new_pcutil.py ${TMP}/new1_pcutil.py
ls -l ${TMP}/new1_pcutil.py

python pcutil.py cp -dr ${TMP}/test p:/${PTMP}
python pcutil.py cp -r ${TMP}/test p:/${PTMP}
mv ${TMP}/test ${TMP}/test.orig

python pcutil.py cp -dr p:/${PTMP}/test ${TMP}
python pcutil.py cp -r p:/${PTMP}/test ${TMP}
diff -r ${TMP}/test ${TMP}/test.orig

python pcutil.py cp -dr p:/${PTMP}/test/ ${TMP}/x/y/test
python pcutil.py cp -r  p:/${PTMP}/test/ ${TMP}/x/y/test
diff -r ${TMP}/test ${TMP}/x/y/test

python pcutil.py cp pcutil.py p:/${PTMP}/new_dir/new_file_name
python pcutil.py cp p:/${PTMP}/new_dir/new_file_name ${TMP}
ls -l ${TMP}/new_file_name

rm -rf ${TMP}

echo "Removing test folders and files from pCloud in five seconds"
sleep 5
python pcutil.py rm ${PTMP}/pcutil.py ${PTMP}/new_pcutil.py ${PTMP}/new_dir/new_file_name
sleep 1
python pcutil.py rm ${PTMP}/new_dir
python pcutil.py rm -r ${PTMP}/test ${PTMP}/nd1
python pcutil.py rm ${PTMP}
