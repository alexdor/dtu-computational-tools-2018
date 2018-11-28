import io
import math
import sqlite3

from BitVector import BitVector


class KeyWordBloomFilter:
	# Setup useful variables in here
	def __init__(self,p,n,read_from_path=None):
		#k = nr of hash functions
		#m = bitvector's length

		#calculation is based on:
		#https://www.geeksforgeeks.org/bloom-filters-introduction-and-python-implementation/
		self.m = round(-((n*math.log10(p))/math.log10(2)**2)/8)*8
		self.k = round(self.m/n*math.log10(2))
		# round(1494868/8)*8
		print(read_from_path)
		if not read_from_path:
			self.bitvector = BitVector(size= self.m)
		else:
			tmp =  BitVector(filename = read_from_path)
			self.bitvector = tmp.read_bits_from_file(self.m)

	def train(self, word):
		for i in range(1,self.k+1):
			j = hash(word + chr(i)) % self.m
			self.bitvector[j] = True

	# Should return true if the Keyword is in the list, otherwise false.
	def classify(self, word):
		for i in range(1,self.k+1):
			j = hash(word + chr(i)) % self.m
			if self.bitvector[j] == 0:
				return False

		return True

	def write_to_file(self, path='bitvector'):
		fileout = io.open(path, 'wb')
		self.bitvector.write_to_file(fileout)
		fileout.close()
