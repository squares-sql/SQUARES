#!/usr/bin/python
# File:	gen_tests.py
# Description:
# Author:	Pedro M Orvalho
# Created on:	29-04-2019 14:01:06
# Usage:	python gen_tests.py
# Python version:	3.6.4

from sys import *
import os

tests = list(range(1,56))

if __name__ == '__main__':
	counter = 1
	os.system("mkdir new_tests")
	os.system("cp -r tests/tables new_tests/.")
	for i in tests:
		file = open("tests/"+str(i)+".in", "r+")
		test = file.readlines()
		for l in range(1,7):
			# loc is always on the 7th lines
			file_out = open("new_tests/"+str(counter)+".in", "w+")
			counter += 1
			for s in range(len(test)):
				if s != 6:
					file_out.write(test[s])
				else:
					file_out.write("loc: "+str(l)+"\n")