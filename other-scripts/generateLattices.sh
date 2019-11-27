# File:	generateLattices.sh
# Description: generate all lattices from programs with loc_from to loc_to lines of code (loc)
# Author:	Pedro M Orvalho
# Created on:	05-04-2019 18:33:47
# Usage:	bash generateLattices.sh loc_from loc_to

mkdir lattices

let first=$(($1))
let last=$(($2))
for ((i=first;i<=last;i++));
do
	#gtimeout 60m 
	python3 gen_lattices.py $i > lattices/loc-$i
	echo "lattices for $i loc done"
done

