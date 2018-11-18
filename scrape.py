# scrape.py
# This file scraps ESPN's website for data for training a model in the form of
# HTTP GET requests and then parsing the returned JSON.
# Developed 11.12.18 by Liam McInroy

import argparse
import requests


def get_teams():
    """Get all the team ids and names which ESPN uses to refer to them within
    their API.
    """
    # the ESPN link to get all the conferences from
    data = requests.get('https://site.web.api.espn.com/apis/site/v2/sports/'
                        'basketball/mens-college-basketball/scoreboard/'
                        'conferences?groups=50').json()

    # specifically pull the each conferences' ids
    conf_ids = [int(conf['groupId']) for conf in data['conferences'][1:]]

    teams = {}
    for conf_id in conf_ids:
        # the ESPN link to get the information for a conference from
        data = requests.get('https://site.web.api.espn.com/apis/site/v2/'
                            'sports/basketball/mens-college-basketball/'
                            'teams?groups={}'.format(conf_id)).json()

        # the JSON data which contains all the team data, take only id and name
        for team in data['sports'][0]['leagues'][0]['teams']:
            teams[int(team['team']['id'])] = team['team']['name']

    return teams


def get_team_season_gids(tid, year):
    """Gets all the season results for the specified year and team id.
    Specifically returns all the game IDs that can then be looked up by
    get_game(gid)

    Arguments:
        tid: The team id that ESPN uses to refer to the team in its API
        year: The year to fetch from, specifically 2002 refers to the 01/02
            season. Make sure to provide a four digit year 2002-2017
    """
    # the ESPN link that contains all the season schedule information for team
    data = requests.get('https://site.web.api.espn.com/apis/site/v2/sports/'
                        'basketball/mens-college-basketball/teams/{}/schedule?'
                        'region=us&lang=en&seasontype=2&'
                        'season={}'.format(tid, year)).json()

    game_ids = [int(game['id']) for game in data['events']]

    return game_ids


def get_game(gid):
    """Gets all the statistics for given game ID.

    Arguments:
        gid: The game id that ESPN uses to refer to the game
    """
    # the ESPN link that contains all the game boxscores
    data = requests.get('http://cdn.espn.com/core/mens-college-basketball/'
                        'boxscore?xhr=1&gameId={}'.format(gid)).json()
    homeTeam = data['__gamepackage__']['homeTeam']
    awayTeam = data['__gamepackage__']['awayTeam']

    # TODO: Implement which statistics to take
    stats = {}

    # score
    stats['score'] = (int(homeTeam['score']), int(awayTeam['score']))

    # general team information about the game/season formally
    stats['homeId'] = homeTeam['id']
    stats['homeRecord'] = (int(homeTeam['record'][0]['summary'].split('-')[0]),
                           int(homeTeam['record'][0]['summary'].split('-')[1]))
    stats['homeHalfScores'] = (int(homeTeam['linescores'][0]['displayValue']),
                               int(homeTeam['linescores'][1]['displayValue']))
    stats['awayId'] = awayTeam['id']
    stats['awayRecord'] = (int(awayTeam['record'][0]['summary'].split('-')[0]),
                           int(awayTeam['record'][0]['summary'].split('-')[1]))
    stats['awayHalfScores'] = (int(awayTeam['linescores'][0]['displayValue']),
                               int(awayTeam['linescores'][1]['displayValue']))

    # team game statistics, first is MIN so skip
    labels = (data['gamepackageJSON']['boxscore']['players']
              [0]['statistics'][0]['labels'])
    for k, val in enumerate(data['gamepackageJSON']['boxscore']['players']
                                [0]['statistics'][0]['totals'][1:]):
        stats['home' + labels[k]] = val

    for k, val in enumerate(data['gamepackageJSON']['boxscore']['players']
                            [1]['statistics'][0]['totals'][1:]):
        stats['away' + labels[k]] = val

    return stats


def parse_args():
    """Get the arguments required for calling from the command line rather
    than from another python script.
    """
    parser = argparse.ArgumentParser(
        description='Scrape ESPN\'s website for all of the NCAA men\'s games'
                    ' regular season games since 2002 and then save them to'
                    ' a file.')
    parser.add_argument('file', type=str,
                        help='The file to save the .csv to.')
    return parser.parse_args()


def main():
    """The command line interface for the program, the other functions are
    callable via kwargs by importing this into another python file.
    """
    args = parse_args()

    return NotImplementedError()


if __name__ == '__main__':
    main()
