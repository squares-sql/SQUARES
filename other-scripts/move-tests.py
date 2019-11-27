#!/usr/bin/env python
# File:	move_tests.py
# Description:	move tests from a folder (old_name) to another (new_name)
# Author:	Pedro M Orvalho
# Created on:	06-08-2019 10:30:37
# Usage:	python3 move-tests.py old_name new_name number_of_tests
# Python version:	3.6.4

from sys import argv
import os

if "-h" in argv:
    exit("USAGE: python3 move-tests.py old_name new_name number_of_tests")
os.system("mv "+argv[1]+" "+argv[2])
for i in range(1, int(argv[3])+1):
     f = open(argv[2]+"/"+str(i)+".in","r+").readlines()
     g = ""
     for l in f:
             g += l.replace(argv[1],argv[2])
     w = open(argv[2]+"/"+str(i)+".in","w+")
     w.write(g)
     w.close()
