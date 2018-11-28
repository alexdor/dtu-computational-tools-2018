from KeyWordBloomFilter import KeyWordBloomFilter
import sqlite3

conn = sqlite3.connect("parser.sqlite3")
c = conn.cursor()

c.execute("Select word from word_movies")
wordlist = [word[0] for word in c.fetchall()]
bloomFilter = KeyWordBloomFilter(p=0.0001, n=len(wordlist))
for word in wordlist:
    bloomFilter.train(word)

bloomFilter.write_to_file("BloomFilterBitVector")

