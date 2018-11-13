import asyncio
import json
import os
import traceback

import aiohttp
import click

from db import MovieModel, Session


class Movie(object):
    semaphore = None
    loop = None

    def __init__(self, page_id, title):
        assert isinstance(title, str)
        if any(map(lambda el: el is None, [self.semaphore, self.loop])):
            raise AttributeError("Initialize Class-wide variables!")
        self.title = title
        self.page_id = page_id

    async def start(self):
        return await self.parse()

    async def parse(self):
        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.get_movie_url()) as resp:
                    data = await resp.text()
        return MovieModel(
            title=self.title, page_id=self.page_id, response=json.dumps(data)
        )

    def get_movie_url(self):
        # 'https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&rvsection=0&titles=Home_Alone&format=json'
        return f"https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles={self.title}"

    async def parse_wiki_response(self, response):
        text = json.loads(response.text)
        try:
            if text:
                pass
            return text
        except:
            traceback.print_exc()


class MovieListing(object):
    semaphore = None
    loop = None
    eicontinue = None

    def __init__(self):
        if any(map(lambda el: el is None, [self.semaphore, self.loop])):
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
                    data = await resp.text()
        self.data = await self.parse_wiki_response(data)
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
                await MovieListing().get_movies(self.data["continue"]["eicontinue"])
        except:
            traceback.print_exc()
        return

    async def parse_wiki_response(self, response):
        text = json.loads(response)
        try:
            if text:
                pass
            return text
        except:
            traceback.print_exc()


class Worker(object):
    def __init__(self, loop, concurrency=None):
        MovieListing.semaphore = asyncio.Semaphore(concurrency)
        MovieListing.loop = loop
        Movie.semaphore = asyncio.Semaphore(concurrency)
        Movie.loop = loop
        self.loop = loop

    async def start(self):
        # entries = await MovieListing().get_movies()
        # self.targets = [Movie(entry) for entry in entries]
        # tasks = [target.start() for target in self.targets]
        await MovieListing().get_movies()


@click.command()
@click.option(
    "-c",
    "--concurrency",
    type=click.INT,
    default=10,
    help="Number of concurrent connections.",
)
def main(concurrency):
    loop = asyncio.get_event_loop()
    w = Worker(loop, concurrency)
    loop.run_until_complete(w.start())


if __name__ == "__main__":
    main()
