import sqlite3

from KeyWordBloomFilter import KeyWordBloomFilter

conn = sqlite3.connect("parser_prod.sqlite3")
c = conn.cursor()

c.execute("Select word from word_movies")
wordlist = [word[0] for word in c.fetchall()]
bloomFilter = KeyWordBloomFilter(p=0.0001, n=len(wordlist))
for word in wordlist:
    bloomFilter.train(word)

bloomFilter.write_to_file("BloomFilterBitVector")
