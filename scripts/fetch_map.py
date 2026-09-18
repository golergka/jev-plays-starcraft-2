"""Fetch Blizzard's small reference scenario; keep game assets out of Git."""
from pathlib import Path
from urllib.request import urlretrieve

destination=Path('maps/MarineMicro.SC2Map')
destination.parent.mkdir(exist_ok=True)
urlretrieve('https://raw.githubusercontent.com/Blizzard/s2client-api/master/maps/Example/MarineMicro.SC2Map',destination)
print(destination.resolve())
