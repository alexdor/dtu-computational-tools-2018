import asyncio
import heapq
import json
import math
import sqlite3

import click
import gensim
import requests
from gensim.models import KeyedVectors, Word2Vec

from db import MovieModel, Session, WordMoviesModel

inputArgs = ["dog", "detective", "volcano"]


class API(object):
    session = Session()

    async def get_synonyms(self, inputArgs):
        synonymList = [list() for i in inputArgs]

        # grab synonyms from API
        for position in range(len(inputArgs)):
            r = requests.get(
                "https://od-api.oxforddictionaries.com:443/api/v1/entries/en/"
                + inputArgs[position]
                + "/synonyms",
                headers={
                    "app_id": "a76c92b5",
                    "app_key": "107c3736bfdc71a084306ecb73aafa26",
                },
            )
            if r.status_code >= 200 and r.status_code <= 299:
                synonyms = json.loads(r.text)
                for i in synonyms["results"]:
                    for j in i["lexicalEntries"]:
                        for k in j["entries"]:
                            for v in k["senses"]:
                                for w in v["synonyms"]:
                                    if len(w["text"].split(" ")) == 1:
                                        synonymList[position].append(w["text"])

        # load the desired model
        cbow = KeyedVectors.load_word2vec_format("skip_grams.bin", binary=False)

        # find synonyms from embedded model
        for i in range(len(synonymList)):
            for word in cbow.wv.most_similar(inputArgs[i]):
                if len(word[0].split(" ")) == 1:
                    synonymList[i].append(word[0])
        word_list = [word for group in synonymList for word in group] + inputArgs
        return await self.scoring(synonymList, set(word_list), inputArgs)

    async def scoring(self, synonymList, word_list, original_args):

        # make dictionary from the sql call
        wordDict = {}
        for entry in (
            self.session.query(WordMoviesModel)
            .filter(WordMoviesModel.word.in_(word_list))
            .all()
        ):
            wordDict[entry.word] = entry.movie_ids.split(",")

        # loop through the dictionary and sum the movies
        movieScores = {}
        for group in range(len(synonymList)):
            for word in synonymList[group]:
                movies = wordDict.get(word, False)
                if not movies:
                    continue
                for movie in movies:
                    if movieScores.get(movie):
                        movieScores[movie][group] += 1
                    else:
                        movieScores[movie] = [0, 0, 0]
                        movieScores[movie][group] = 1
                    movieScores[movie][group] += 1
                else:
                    movieScores[movie] = [0, 0, 0]
                    movieScores[movie][group] = 1

        for movie in movieScores:
            original_syn_count = 0
            for word in original_args:
                if movie in wordDict[word]:
                    original_syn_count += 1
            movieScores[movie] = (
                math.log(movieScores[movie][0] + 0.00001, 1.5)
                + math.log(movieScores[movie][1] + 0.00001, 1.5)
                + math.log(movieScores[movie][2] + 0.00001, 1.5)
                + 5 * original_syn_count
            )

        print("Based on your inputs, we recommend the following:", "\n")
        movies = sorted(movieScores, key=lambda k: movieScores[k], reverse=True)[:10]
        q = self.session.query(MovieModel).filter(MovieModel.id.in_(movies))
        movie_map = {movie.id: movie.title for movie in q}
        [print(movie_map[int(id)]) for id in movies]


@click.command()
@click.option(
    "--words",
    is_flag=False,
    default=",".join(inputArgs),
    show_default=True,
    type=click.STRING,
    metavar="<words>",
    help="Sets the words that you want to search",
)
def main(words):
    words = [arg.strip() for arg in words.split(",")]
    asyncio.get_event_loop().run_until_complete(API().get_synonyms(words))


if __name__ == "__main__":
    main()
