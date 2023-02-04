import boto3
import datetime
import json
import os
import pytz
import yahoo_fantasy_api as yfa

from dotenv import load_dotenv
from yahoo_oauth import OAuth2

load_dotenv()
OAUTH_FILENAME = os.environ.get("OAUTH_FILENAME")
DB = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME')
TABLE = DB.Table(TABLE_NAME)
PRIMARY_KEY = os.environ.get('DYNAMODB_PRIMARY_KEY')


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
    today = todays_date_in_pst()
    player_stats = league.player_stats(player_ids, 'date', today)
    EXCEPTiONAL_FANTASY_POINTS = int(os.environ.get("EXCEPTIONAL_FANTASY_POINTS"))
    exceptional_free_agents = []
    for stats in player_stats:
        fantasy_points = get_fantasy_points_from_stats(stats)
        if fantasy_points >= EXCEPTiONAL_FANTASY_POINTS:
            exceptional_free_agents.append((stats['name'], fantasy_points))
    return exceptional_free_agents


def get_key(player_id, date):
    return f'{player_id},{date}'


def have_sent_notification_for_current_points(player_id, date, fantasy_points):
    # Returns whether or not any notification has been sent followed by whether a notification for
    # their current fantasy point total has been sent
    key = get_key(player_id, date)
    item = TABLE.get_item(Key={PRIMARY_KEY: key})
    if 'Item' not in item:
        return False, False
    item = item['Item']
    if fantasy_points > item['fantasy_points']:
        return True, False
    return True, True


def todays_date_in_pst():
    PST = pytz.timezone('US/Pacific')
    now_in_pst = datetime.datetime.now(PST)
    return now_in_pst.date()


def update_table(player_id, date, fantasy_points):
    key = get_key(player_id, date)
    Key = {PRIMARY_KEY: key}
    AttributeUpdates = {
        'fantasy_points': {
            'Value': fantasy_points,
            'Action': 'PUT',
        }
    }
    TABLE.update_item(
        Key=Key,
        AttributeUpdates=AttributeUpdates,
    )


def write_to_table(player_id, date, fantasy_points):
    key = get_key(player_id, date)
    Item = {PRIMARY_KEY: key, 'fantasy_points': fantasy_points}
    TABLE.put_item(Item=Item)


def send_twilio_message(name, fantasy_points, update):
    message = (
        f'{name} has scored {fantasy_points} today!' if not update else
        f'{name} has scored again! {fantasy_points} points today!'
    )
    pass


def send_notification(name, player_id, date, fantasy_points, update):
    if update:
        update_table(player_id, date, fantasy_points)
    else:
        write_to_table(player_id, date, fantasy_points)
    send_twilio_message(name, fantasy_points, update)


def send_notifications_for_exceptional_free_agents(exceptional_free_agents):
    for name, id, fantasy_points in exceptional_free_agents:
        today = todays_date_in_pst()
        any, current = have_sent_notification_for_current_points(
            id,
            today,
            fantasy_points
        )
        if current:
            continue
        send_notification(name, id, today, fantasy_points, update=any)


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
    send_notifications_for_exceptional_free_agents()


if __name__ == "__main__":
    main()
