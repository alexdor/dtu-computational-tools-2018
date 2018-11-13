import urllib
import re

url = 'https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&titles=12_Angry_Men_(1957_film)'

# by providing the rvsection=0 attribute, you get the first paragraph and the Infobox as well which has a clear and constant scheme at least
urlForInfobox = 'https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&rvsection=0&titles=Home_Alone'

with urllib.request.urlopen(url) as response:
    text = str(response.read())
    plot = re.search('==Plot==.*?==',text)[0]
    # We still need:

    # year
    # budget


print(plot)