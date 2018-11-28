from BitVector import BitVector
import math
import io
import sqlite3

class KeyWordBloomFilter:
	# Setup useful variables in here
	def __init__(self,p,n,read_from_path=''):
		#k = nr of hash functions
		#m = bitvector's length
		
		#calculation is based on:
		#https://www.geeksforgeeks.org/bloom-filters-introduction-and-python-implementation/
		self.m = round(-((n*math.log10(p))/math.log10(2)**2)/8)*8
		self.k = round(self.m/n*math.log10(2))
		# round(1494868/8)*8
		self.bitvector = BitVector(size= self.m) if not read_from_path else BitVector(filename = read_from_path) 
	
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

