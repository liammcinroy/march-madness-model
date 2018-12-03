# scrape.py
# This file scraps ESPN's website for data for training a model in the form of
# HTTP GET requests and then parsing the returned JSON.
# Developed 11.12.18 by Liam McInroy

import argparse
import pickle
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
            teams[int(team['team']['id'])] = team['team']['location'] + ' ' + \
                                             team['team']['name']

    return teams


def get_team_season_gids(tid, season):
    """Gets all the season game ids for the specified year and team id.
    Specifically returns all the game IDs that can then be looked up by
    get_game(gid)

    Arguments:
        tid: The team id that ESPN uses to refer to the team in its API
        season: The season to fetch from, specifically 2002 refers to the 01/02
            season. Make sure to provide a four digit year 2002-2018
    """
    # the ESPN link that contains all the season schedule information for team
    data = requests.get('https://site.web.api.espn.com/apis/site/v2/sports/'
                        'basketball/mens-college-basketball/teams/{}/schedule?'
                        'region=us&lang=en&seasontype=2&'
                        'season={}'.format(tid, season)).json()

    game_ids = [int(game['id']) for game in data['events']]

    return game_ids


def get_team_post_gids(tid, season):
    """Gets all the postseason game ids for the given season and team id.
    Specifically, returns all the game IDs that can then be looked up by
    get_game(gid)

    Arguments:
        tid: The team id that ESPN uses to refer to the team in its API
        season: The season to fetch from, specifically 2002 refers to the 01/02
            season and postseason. Make sure to provide a four digit year from
            2002-2018
    """
    # the ESPN link that contains all the postseason schedule results for team
    data = requests.get('https://site.web.api.espn.com/apis/site/v2/sports/'
                        'basketball/mens-college-basketball/teams/{}/schedule?'
                        'region=us&lang=en&seasontype=3&'
                        'season={}'.format(tid, season)).json()

    game_ids = [int(game['id']) for game in data['events']]

    return game_ids


def get_game(gid, **kwargs):
    """Gets all the statistics for given game ID. Returns None if fails

    Arguments:
        gid: The game id that ESPN uses to refer to the game
        kwargs: Mostly just for debugging verbosity

            verbose: If positive then prints output on error, otherwise silence
    """

    def printverbose(*args):
        if kwargs.get('verbose', 0):
            print(*args)

    # the ESPN link that contains all the game boxscores
    data = requests.get('http://cdn.espn.com/core/mens-college-basketball/'
                        'boxscore?xhr=1&gameId={}'.format(gid))
    try:
        data = data.json()
    except Exception as e:
        print('ERROR:', gid)
        raise e

    if '__gamepackage__' not in data:
        return None  # didn't successfully pull the game data

    homeTeam = data['__gamepackage__']['homeTeam']
    awayTeam = data['__gamepackage__']['awayTeam']

    # TODO: Choose more statistics to take
    stats = {}

    # score
    try:
        stats['score'] = (int(homeTeam['score']), int(awayTeam['score']))
    except:
        printverbose('ERROR on score: ', gid)
        return None

    # whether the game was played in the regular season or postseason TODO?

    # whether the game was played at a neutral site
    stats['neutralSite'] = \
        data['gamepackageJSON']['header']['competitions'][0]['neutralSite']

    # the date of the game (for temporal feature generation)
    stats['date'] = \
        data['gamepackageJSON']['header']['competitions'][0]['date']

    # team game statistics, first is MIN so skip
    labels = (data['gamepackageJSON']['boxscore']['players']
              [0]['statistics'][0]['labels'])
    for k, val in enumerate(data['gamepackageJSON']['boxscore']['players']
                                [0]['statistics'][0]['totals'][1:]):
        try:
            stats['home' + labels[k]] = val
        except:
            printverbose('ERROR on home', labels[k], ':', gid)
            stats['home' + labels[k]] = -1

    for k, val in enumerate(data['gamepackageJSON']['boxscore']['players']
                            [1]['statistics'][0]['totals'][1:]):
        try:
            stats['away' + labels[k]] = val
        except:
            printverbose('ERROR on away', labels[k], ':', gid)
            stats['away' + labels[k]] = -1

    # general team information about the game/season formally
    # home team first
    try:
        stats['homeId'] = int(homeTeam['id'])
    except:
        printverbose('ERROR on home id: ', gid)
        return None
    try:
        stats['homeRecord'] = homeTeam['record'][0]['summary']
    except:
        printverbose('ERROR on home record: ', gid)
        stats['homeRecord'] = '0-0'  # default if none is known
    try:
        stats['homeRank'] = int(homeTeam['rank']) if 'rank' in homeTeam else -1
    except:
        printverbose('ERROR on home rank: ', gid)
        stats['homeRank'] = -1
    try:
        stats['homeHalfScores'] = homeTeam['linescores'][0]['displayValue']
    except:
        printverbose('ERROR on home half scores: ', gid)
        stats['homeHalfScores'] = '0-0'  # default if none is known TODO

    # away team
    try:
        stats['awayId'] = int(awayTeam['id'])
    except:
        printverbose('ERROR on away id: ', gid)
        return None
    try:
        stats['awayRecord'] = awayTeam['record'][0]['summary']
    except:
        printverbose('ERROR on away record: ', gid)
        stats['awayRecord'] = '0-0'  # default if none is known
    try:
        stats['awayRank'] = int(awayTeam['rank']) if 'rank' in awayTeam else -1
    except:
        printverbose('ERROR on away rank: ', gid)
        stats['awayRank'] = -1
    try:
        stats['awayHalfScores'] = awayTeam['linescores'][0]['displayValue']
    except:
        printverbose('ERROR on away half scores: ', gid)
        stats['awayHalfScores'] = '0-0'  # default if none is known TODO

    return stats


def get_data(**kwargs):
    """Pulls all the data from ESPN and dumps it in a dictionary. Specifically,
    takes all the game data from the 2006-2017 seasons from ESPN and keeps it
    in memory. The data is organized by its individual game id, but there is
    also structure in the returned dictionary (namely within data['teams'])

    Arguments:
        kwargs: Mostly just for verbose, but can also choose a year range
            or specific team ids to consider

            verbose: If positive then prints output otherwise silence
            years: a list of years to consider, if none provided does 2006-2018
            teams: a dict of team ids and names to consider.
                if none provided, does all.
    """
    # the output dictionary. Contains information about when each game happened
    # and also the statistics for that game
    data = {}

    # keep the teams ids. Used later to organize when each game happens
    teams = kwargs.get('teams', get_teams())
    data['teams'] = {tid: {year: {}
                           for year in kwargs.get('years', range(2006, 2018))}
                     for tid in teams.keys()}

    data['years'] = kwargs.get('years', [range(2006, 2018)])

    for year in kwargs.get('years', range(2006, 2018)):
        if kwargs.get('verbose', 0):
            print('\tFetching data from', year)

        for tid in teams:
            # get all the games that this team played this season
            gids = get_team_season_gids(tid, year)
            data['teams'][tid][year]['reg'] = gids

            # add it to the data if it hasn't been already
            for gid in gids:
                if gid not in data:
                    # get the new game and add it if it has valid data,
                    # otherwise remove it
                    game = get_game(gid, **kwargs)
                    if game is not None:
                        data[gid] = game
                    else:
                        data['teams'][tid][year]['reg'].remove(gid)

            # handle the post season separately incase we want to train from it
            pgids = get_team_post_gids(tid, year)
            data['teams'][tid][year]['post'] = pgids

            for gid in pgids:
                if gid not in data:
                    # get the new game and add it if it has valid data,
                    # otherwise remove it
                    game = get_game(gid, **kwargs)
                    if game is not None:
                        data[gid] = game
                    else:
                        data['teams'][tid][year]['post'].remove(gid)

    return data


def parse_args():
    """Get the arguments required for calling from the command line rather
    than from another python script.
    """
    parser = argparse.ArgumentParser(
        description='Scrape ESPN\'s website for all of the NCAA men\'s games'
                    ' regular season games since 2002 and then save them to'
                    ' a file.')
    parser.add_argument('file', type=str,
                        help='The file to save the pickled dictionary to.')
    return parser.parse_args()


def main():
    """The command line interface for the program, the other functions are
    callable via kwargs by importing this into another python file.
    """
    args = parse_args()

    with open(args.file, 'wb') as f:
        pickle.dump(get_data(), f)


if __name__ == '__main__':
    main()
