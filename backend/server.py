import asyncio
import heapq
import json
import math
import os
import sqlite3
import sys
from timeit import default_timer as timer

import click
import gensim
import requests
from aiohttp import web
from gensim.models import KeyedVectors, Word2Vec
from sqlalchemy import func

from db import MovieModel, Session, WordMoviesModel
from KeyWordBloomFilter import KeyWordBloomFilter

inputArgs = ["gun", "explosion", "drugs"]

p = 0.0001


class API(object):
    session = Session()
    word_count = int(Session().query(WordMoviesModel).count())

    def __init__(self):
        try:
            self.APP_ID = os.environ["APP_ID"]
        except KeyError:
            print("Please set the environment variable APP_ID")
            sys.exit(1)
        try:
            self.APP_KEY = os.environ["APP_KEY"]
        except KeyError:
            print("Please set the environment variable APP_KEY")
            sys.exit(1)
        self.bloom_filter = KeyWordBloomFilter(p, self.word_count)
        # bloomFilter = KeyWordBloomFilter(p=p, n=self.word_count)
        [
            self.bloom_filter.train(word.word)
            for word in self.session.query(WordMoviesModel).all()
        ]

    async def get_synonyms(self, input_args):
        synonym_list = [list() for i in input_args]

        # grab synonyms from API
        for position in range(len(input_args)):
            r = requests.get(
                f"https://od-api.oxforddictionaries.com:443/api/v1/entries/en/{input_args[position]}/synonyms",
                headers={"app_id": self.APP_ID, "app_key": self.APP_KEY},
            )
            if r.ok:
                synonyms = json.loads(r.text)
                for i in synonyms["results"]:
                    for j in i["lexicalEntries"]:
                        for k in j["entries"]:
                            for v in k["senses"]:
                                for w in v["synonyms"]:
                                    if len(w["text"].split(" ")) == 1:
                                        synonym_list[position].append(w["text"])

        # load the desired model
        cbow = KeyedVectors.load_word2vec_format("cbow.bin", binary=False)

        # find synonyms from embedded model
        for i in range(len(synonym_list)):
            for word in cbow.most_similar(input_args[i]):
                if len(word[0].split(" ")) == 1:
                    synonym_list[i].append(word[0])
        word_list = [word for group in synonym_list for word in group]
        word_list = set(
            [
                word
                for word in word_list + input_args
                if self.bloom_filter.classify(word)
            ]
        )

        word_dict = {}
        for entry in (
            self.session.query(WordMoviesModel)
            .filter(WordMoviesModel.word.in_(word_list))
            .all()
        ):
            word_dict[entry.word] = entry.movie_ids.split(",")

        # loop through the dictionary and sum the movies
        movie_scores = {}
        for group in range(len(synonym_list)):
            for word in synonym_list[group]:
                movies = word_dict.get(word, False)
                if not movies:
                    continue
                for movie in movies:
                    if not movie_scores.get(movie):
                        movie_scores[movie] = [0, 0, 0]
                    movie_scores[movie][group] += 1

        for movie in movie_scores:
            original_syn_count = 0
            for word in input_args:
                if movie in word_dict[word]:
                    original_syn_count += 1
            movie_scores[movie] = (
                math.log(movie_scores[movie][0] + 0.00001, 1.5)
                + math.log(movie_scores[movie][1] + 0.00001, 1.5)
                + math.log(movie_scores[movie][2] + 0.00001, 1.5)
                + 5 * original_syn_count
            )

        movies = sorted(movie_scores, key=lambda k: movie_scores[k], reverse=True)[:10]
        q = self.session.query(MovieModel).filter(MovieModel.id.in_(movies))
        movie_map = {movie.id: movie.title for movie in q}
        return [movie_map[int(id)] for id in movies]

    async def handle_command_line_execution(self, words):
        res = await self.get_synonyms(words)
        print("Based on your inputs, we recommend the following:", "\n")
        [print(movie) for movie in res]

    async def handle_request(self, request):
        try:
            words = request.rel_url.query["words"]
            return web.json_response(
                {"results": await self.get_synonyms(words.split(","))}
            )
        except KeyError:
            return web.json_response(
                {"error": "Please provide some tags to be used in the movie selection"},
                status=400,
            )


@click.command()
@click.option(
    "--words",
    is_flag=False,
    show_default=True,
    type=click.STRING,
    metavar="<words>",
    help="Sets the words that you want to search",
)
def main(words):
    api = API()
    if words:
        words = [arg.strip() for arg in words.split(",")]
        # start = timer()
        asyncio.get_event_loop().run_until_complete(
            api.handle_command_line_execution(words)
        )
        # end = timer()
        # print(end - start)
    else:
        app = web.Application()
        app.add_routes([web.get("/", api.handle_request)])

        web.run_app(app)


if __name__ == "__main__":
    main()
