import requests
from pathlib import Path

URLS = [
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_atl.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_bos.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_bkn.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_cha.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_chi.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_cle.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_dal.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_den.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_det.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_gs.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_hou.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_ind.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_lac.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_lal.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_mem.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_mia.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_mil.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_min.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_no.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_ny.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_okc.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_orl.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_phi.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_pho.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_por.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_sac.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_sa.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_tor.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_uta.txt",
"https://cdn.nba.com/static/json/staticData/EliasGameStats/00/t_players_gamehigh_was.txt"
]

output = Path("data/nba_elias_gamehigh_master.txt")

combined = []

for url in URLS:
    r = requests.get(url)
    combined.append(r.text)

output.write_text("\n\n".join(combined))

print("File updated")
