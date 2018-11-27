import asyncio
import heapq
import json
import logging
import os
import re
import traceback
from math import log

import aiohttp
import click
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords

from db import MovieModel, Session

stop = stopwords.words("english")


class Movie(object):
    semaphore = None
    loop = None

    def __init__(self, page_id, title):
        self.loop = asyncio.get_event_loop()
        if any(map(lambda el: el is None, [self.semaphore])):
            raise AttributeError("Initialize Class-wide variables!")
        self.title = title
        self.page_id = page_id

    async def start(self, id=None):
        return await self.parse(id)

    async def parse(self, id):
        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.get_movie_url()) as resp:
                    data = await resp.text()
        model = MovieModel(
            title=self.title, page_id=self.page_id, response=json.dumps(data)
        )
        if id:
            model.id = id
        return model

    def get_movie_url(self):
        # 'https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&rvsection=0&titles=Home_Alone&format=json'
        return f"https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&pageids={self.page_id}"


class MovieListing(object):
    semaphore = None
    loop = None
    eicontinue = None

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        if any(map(lambda el: el is None, [self.semaphore])):
            raise AttributeError("Initialize Class-wide variables!")
        self.session = Session()

    async def start(self):
        await self.get_movies()

    def get_movie_listing_url(self):
        # https://en.wikipedia.org/w/api.php?action=query&list=embeddedin&einamespace=0&eilimit=max&eititle=Template:Infobox_film&format=json&eicontinue=0|76349
        return f"https://en.wikipedia.org/w/api.php?action=query&list=embeddedin&einamespace=0&eilimit=max&eititle=Template:Infobox_film&format=json{f'&eicontinue={self.eicontinue}' if self.eicontinue else ''}"

    async def get_movies(self, eicontinue=None):
        self.eicontinue = eicontinue
        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.get_movie_listing_url()) as resp:
                    data = json.loads(await resp.text())
        self.data = data
        self.targets = [
            Movie(entry["pageid"], entry["title"])
            for entry in self.data["query"]["embeddedin"]
        ]
        tasks = [target.start() for target in self.targets]
        movies = await asyncio.gather(*tasks)
        self.session.add_all(movies)
        self.session.commit()
        try:
            if self.data["continue"]["eicontinue"]:
                await self.get_movies(self.data["continue"]["eicontinue"])
        except KeyError as err:
            print(f"Failed to find continue key {err} data: \n {data} ")
        return


class Data_Cleanup(object):
    session = Session()
    movies_that_json_failed = []
    movies_that_revision_failed = []

    async def start(self):
        for movie in self.session.query(MovieModel).all():
            try:
                tmp = json.loads(json.loads(movie.response))
            except:
                self.movies_that_json_failed.append(movie)
                continue
            try:
                movie.response = json.dumps(
                    tmp["query"]["pages"][list(tmp["query"]["pages"])[0]]["revisions"][
                        0
                    ]["*"]
                )
            except KeyError:
                tmp = await Movie(movie.page_id, movie.title).start()
                tmp = json.loads(json.loads(tmp.response))
                movie.response = json.dumps(
                    tmp["query"]["pages"][list(tmp["query"]["pages"])[0]]["revisions"][
                        0
                    ]["*"]
                )
                self.movies_that_revision_failed.append(movie)
        self.session.commit()
        print(self.movies_that_revision_failed)


class Parse_Data(object):
    session = Session()

    async def start(self):
        for movie in self.session.query(MovieModel).all():
            res = movie.response
            tmp = re.search(r"==\s?Plot\s?==.*?[^=]==[^=]", res)
            if tmp:
                tmp = tmp[0]
                tmp = re.sub(r"==\s?Plot\s?==", "", tmp)
                movie.plot = tmp
                text = tmp.lower()
                text = re.sub(r"[^\w\s]", "", text)
                text = " ".join([word for word in text.split() if word not in stop])
                text = re.sub(r"rt\s", "", text)
                text = re.sub(r"rt\t", "", text)
                text = re.sub(r"\d+", "", text)
                movie.tokenized_plot = ",".join(word_tokenize(text))
            else:
                movie.plot = None
                movie.tokenized_plot = None
            tmp = re.search(r"released\s*=\s*.*?\\n", res)
            if tmp:
                tmp = re.search(r"\d{4}", tmp[0])
                if tmp:
                    movie.year = tmp[0]
                else:
                    movie.year = None
            else:
                movie.year = None
            tmp = re.search(r"budget\s*=.*?\\n", res)
            if tmp:
                tmp = tmp[0][tmp[0].find("=") + 1 :]
                index = tmp.find("<ref")
                if index > -1:
                    tmp = tmp[:index]
                index = tmp.find("<!--")
                if index > -1:
                    tmp = tmp[:index]
                index = tmp.find("(est")
                if index > -1:
                    tmp = tmp[:index]
                index = tmp.find('("est')
                if index > -1:
                    tmp = tmp[:index]
                tmp = tmp.replace("\r", "").replace("\n", "")
                movie.budget = tmp.strip()
            else:
                movie.budget = None
        self.session.commit()


class Worker(object):
    def __init__(self, concurrency=None):
        MovieListing.semaphore = asyncio.Semaphore(concurrency)
        Movie.semaphore = asyncio.Semaphore(concurrency)
        self.loop = asyncio.get_event_loop()

    async def start(self):
        # entries = await MovieListing().get_movies()
        # self.targets = [Movie(entry) for entry in entries]
        # tasks = [target.start() for target in self.targets]
        # await MovieListing().get_movies()
        # await Data_Cleanup().start()
        await Parse_Data().start()


@click.command()
@click.option(
    "-c",
    "--concurrency",
    type=click.INT,
    default=15,
    help="Number of concurrent connections.",
)
def main(concurrency):
    w = Worker(concurrency)
    asyncio.get_event_loop().run_until_complete(w.start())


if __name__ == "__main__":
    main()
