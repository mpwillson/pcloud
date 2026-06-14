#!/bin/sh
#
# Smoke tests for pcutil.py

set -e

create_test_dirs() {
    rm -rf test test.orig
    mkdir -p test/d1
    mkdir test/d2
    mkdir test/d3
    mkdir test/d2/d4
    echo 'x contents' >test/x
    echo 'y contents' >test/y
    echo 'z contents' >test/z
    cp test/x test/y test/z test/d2
    cp test/x test/y test/z test/d3
    cp test/x test/y test/z test/d2/d4
}

echo "Running smoke test of pcutil.py. Expect no errors."

create_test_dirs

python pcutil.py cp -d pcutil.py p:/new_pcutil.py
python pcutil.py cp pcutil.py p:/new_pcutil.py

python pcutil.py cp -d pcutil.py p:/
python pcutil.py cp pcutil.py p:/

python pcutil.py cp -d p:/new_pcutil.py test/new1_pcutil.py
python pcutil.py cp p:/new_pcutil.py test/new1_pcutil.py

python pcutil.py cp -d p:/new_pcutil.py new_dir/new1_pcutil.py
python pcutil.py cp p:/new_pcutil.py new_dir/new1_pcutil.py
ls -l new_dir
rm -r new_dir

python pcutil.py cp -dr test p:/
python pcutil.py cp -r test p:/
mv test test.orig

python pcutil.py cp -dr p:/test .
python pcutil.py cp -r p:/test .
diff -r test test.orig

python pcutil.py cp -dr p:/test/ x/y/test
python pcutil.py cp -r  p:/test/ x/y/test
diff -r test x/y/test

python pcutil.py cp pcutil.py p:/new_dir/x

rm -rf test test.orig x

echo Removing test folders and files from pCloud
python pcutil.py rm /pcutil.py /new_pcutil.py new_dir/x
python pcutil.py rm /new_dir
python pcutil.py rm -r /test
