# File: test.sh
# Description: enumerator type: smt or lines, first and last number of the tests to be tested, folder with tests
# Author:       Pedro M Orvalho
# Created on:   03-04-2019 9:10:07
# Usage:        bash test.sh TESTS_Folder NUMBER_FIRST_TEST NUMBER_LAST_TEST TIMEOUT [ENUMERATOR_TYPE]


export PYTHONWARNINGS="ignore"
mkdir results_$1_$4

let first=$(($2))
let last=$(($3))
for ((i=first;i<=last;i++));
do
        timeout $4 python3 squaresEnumerator.py $5 tests/$i.in &> results_$1_$4/$i.res
        # for MacOS use the command gtimeout
        echo "$i.in"
done
