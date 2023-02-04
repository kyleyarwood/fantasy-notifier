import datetime
import json
import os
import yahoo_fantasy_api as yfa

from dotenv import load_dotenv
from yahoo_oauth import OAuth2

load_dotenv()
OAUTH_FILENAME = os.environ.get("OAUTH_FILENAME")


def create_oauth_file():
    CONSUMER_KEY = os.environ.get('YAHOO_FANTASY_CONSUMER_KEY')
    CONSUMER_SECRET = os.environ.get('YAHOO_FANTASY_CONSUMER_SECRET')
    creds = {'consumer_key': CONSUMER_KEY, 'consumer_secret': CONSUMER_SECRET}
    with open(OAUTH_FILENAME, 'w') as f:
        f.write(json.dumps(creds))


def does_oauth_file_exist():
    return os.path.isfile(OAUTH_FILENAME)


def get_league_of_interest():
    NAME_OF_LEAGUE_OF_INTEREST = os.environ.get('NAME_OF_LEAGUE_OF_INTEREST')
    oauth = OAuth2(None, None, from_file=OAUTH_FILENAME)
    gm = yfa.game.Game(oauth, 'nhl')
    league_ids = gm.league_ids(year=2022)
    leagues = [gm.to_league(league_id) for league_id in league_ids]
    league = None
    for lg in leagues:
        if lg.settings()['name'] == NAME_OF_LEAGUE_OF_INTEREST:
            league = lg
            break
    return league


def get_fantasy_points_from_stats(stats):  
    if stats['GP'] == '-':
        return 0
    weights = {
        'G': 3,
        'A': 2,
        'PPP': 1,
        'SHP': 1,
    }
    return sum(y*stats[x] for x,y in weights.items())


def get_free_agent_player_ids(league):
    free_agents = league.free_agents('Util')
    return [player['player_id'] for player in free_agents]


def get_exceptional_free_agents(league, player_ids):
    player_stats = league.player_stats(player_ids, 'date', datetime.date(2023, 1, 28))
    EXCEPTiONAL_FANTASY_POINTS = int(os.environ.get("EXCEPTIONAL_FANTASY_POINTS"))
    exceptional_free_agents = []
    for stats in player_stats:
        fantasy_points = get_fantasy_points_from_stats(stats)
        if fantasy_points >= EXCEPTiONAL_FANTASY_POINTS:
            exceptional_free_agents.append((stats['name'], fantasy_points))
    return exceptional_free_agents


def main():
    load_dotenv()
    if not does_oauth_file_exist:
        create_oauth_file()
    league = get_league_of_interest()
    if league is None:
        return
    player_ids = get_free_agent_player_ids(league)
    exceptional_free_agents = get_exceptional_free_agents(league, player_ids)
    print(exceptional_free_agents)


if __name__ == "__main__":
    main()
