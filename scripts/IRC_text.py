import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tvcore.tvdatabase import TVDatabase

tv_db = TVDatabase()

series = tv_db.get_scheduled_series()

text = """
Velkommen!

Nyttige kommandoer:
/join <kanal> - Brukes til å bli med i en kanal. Eksempel: /join #baren
/nick <kallenavn> - Endrer visningsnavn. Eksempel: /nick no1smallvillefan
/msg <kallenavn> <melding> - Sender privat melding til bruker. Eksempel: /msg Stalldyr asl?
/list - Lister alle kanaler og antall brukere i hver av dem. 

Generelle kanaler:
#generelt - Generell diskusjon.
#innspill - Her kan du rapportere eventuelle feil eller manglene funksjoner
#film - Her kan du diskutere og stemme på hvilken filmer som vises hver uke

Navn til diskusjonskanaler:
"""

for entry in series:
    text += f'{entry["name"]}: #{entry["directory"]}\n'

print(text)