# scrape.py
# This file scraps ESPN's website for data for training a model in the form of
# HTTP GET requests and then parsing the returned JSON.
# Developed 11.12.18 by Liam McInroy

import argparse
import json
import requests
import os.path


def get_teams():
    """Get all the team ids and names which ESPN uses to refer to them within
    their API.
    """
    try:
        # the ESPN link to get all the conferences from
        data = requests.get('https://site.web.api.espn.com/apis/site/v2/'
                            'sports/basketball/mens-college-basketball/'
                            'scoreboard/conferences?groups=50').json()
        # specifically pull the each conferences' ids
        conf_ids = [int(conf['groupId']) for conf in data['conferences'][1:]]

        teams = {}
        for conf_id in conf_ids:
            # the ESPN link to get the information for a conference from
            data = requests.get('https://site.web.api.espn.com/apis/site/v2/'
                                'sports/basketball/mens-college-basketball/'
                                'teams?groups={}'.format(conf_id)).json()

            # the JSON data containing all the team data, take only id, name
            for team in data['sports'][0]['leagues'][0]['teams']:
                teams[int(team['team']['id'])] = team['team']['location'] + \
                                                 ' ' + team['team']['name']

        return teams
    except:
        print('COULDN\'T GET TEAMS. ABORTING.')
        exit(1)


def get_team_season_gids(tid, season):
    """Gets all the season game ids for the specified year and team id.
    Specifically returns all the game IDs that can then be looked up by
    get_game(gid)

    Arguments:
        tid: The team id that ESPN uses to refer to the team in its API
        season: The season to fetch from, specifically 2006 refers to the 01/02
            season. Make sure to provide a four digit year 2006-2018
    """
    # the ESPN link that contains all the season schedule information for team
    data = None
    try:
        data = requests.get('https://site.web.api.espn.com/apis/site/v2/'
                            'sports/basketball/mens-college-basketball/'
                            'teams/{}/schedule?lang=en&seasontype=2&'
                            'season={}'.format(tid, season))
    except:
        print('NO TEAM DATA:', tid, season)
        return []

    try:
        data = data.json()
    except:
        print('JSON PROCESSING ERROR TEAM:', tid, season)
        return []

    if 'events' not in data:
        print('NO TEAM DATA:', tid, season)
        return []

    game_ids = [int(game['id']) for game in data['events']]

    return game_ids


def get_team_post_gids(tid, season):
    """Gets all the postseason game ids for the given season and team id.
    Specifically, returns all the game IDs that can then be looked up by
    get_game(gid)

    Arguments:
        tid: The team id that ESPN uses to refer to the team in its API
        season: The season to fetch from, specifically 2006 refers to the 01/02
            season and postseason. Make sure to provide a four digit year from
            2006-2018
    """
    # the ESPN link that contains all the postseason schedule results for team
    data = None
    try:
        data = requests.get('https://site.web.api.espn.com/apis/site/v2/'
                            'sports/basketball/mens-college-basketball/'
                            'teams/{}/schedule?lang=en&seasontype=3&'
                            'season={}'.format(tid, season)).json()
    except:
        print('NO POST TEAM DATA:', tid, season)
        return[]

    try:
        data = data.json()
    except:
        print('JSON PROCESSING ERROR POST TEAM:', tid, season)
        return []

    if 'events' not in data:
        print('NO POST TEAM DATA:', tid, season)
        return []

    game_ids = [int(game['id']) for game in data['events']]

    return game_ids


def get_game(gid, **kwargs):
    """Gets all the statistics for given game ID. Returns None if fails, which
    currently how to process that during training is difficult.

    Arguments:
        gid: The game id that ESPN uses to refer to the game
        kwargs: Mostly just for debugging verbosity

            verbose: If positive then prints output on error, otherwise silence
    """

    def printverbose(*args):
        if kwargs.get('verbose', 0):
            print(*args)

    # the ESPN link that contains all the game boxscores
    data = None

    try:
        data = requests.get('http://cdn.espn.com/core/mens-college-basketball/'
                            'boxscore?xhr=1&gameId={}'.format(gid))
    except:
        print('COULDN\'T CONNECT TO ESPN:', gid)
        return None

    try:
        data = data.json()
    except:
        print('JSON PROCESSING ERROR:', gid)
        return None

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
                           for year in kwargs.get('years', range(2006, 2019))}
                     for tid in teams.keys()}

    data['years'] = kwargs.get('years', [i for i in range(2006, 2019)])

    for year in kwargs.get('years', range(2006, 2019)):
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

            continue  # TODO currently don't care about postseason

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
                    ' regular season games since 2006 and then save them to'
                    ' a folder.')
    parser.add_argument('folder', type=str,
                        help='The folder to save the jsond dictionaries to. '
                             'One per year.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Whether to output the current process')
    return parser.parse_args()


def main():
    """The command line interface for the program, the other functions are
    callable via kwargs by importing this into another python file.
    """
    args = parse_args()

    if not os.path.exists(args.folder):
        print('INVALID FOLDER')
        exit(1)

    # save each year individually
    for year in range(2006, 2019):
        # don't download if we already have it
        if os.path.exists(os.path.join(args.folder, str(year) + '.json')):
            continue
        with open(os.path.join(args.folder, str(year) + '.json'), 'w') as f:
            json.dump(get_data(verbose=args.verbose, years=[year]), f)
        print('DOWNLOADED: ', year)

    print('DONE DOWNLOADING, NOW MERGING RESULTS')

    # once done, merge all the results
    cum_data = {'years': [i for i in range(2006, 2019)], 'teams': {}}
    for year in range(2006, 2019):
        year_data = {}
        with open(os.path.join(args.folder, str(year) + '.json'), 'r') as f:
            year_data = json.load(f)
        # update the catalog of game ids for each team, season
        for tid, seasons in year_data['teams'].items():
            if tid not in cum_data['teams']:
                cum_data['teams'][tid] = seasons
            else:
                for year, games in seasons.items():
                    if year not in cum_data['teams'][tid]:
                        cum_data['teams'][tid][year] = games
        # now add the game information, note that even though 'teams' and
        # 'years' aren't game ids, they are already in cum_data so no
        # overwrites will happen
        for gid in year_data:
            if gid not in cum_data:
                cum_data[gid] = year_data[gid]
        print('MERGED: ', year)

    with open(os.path.join(args.folder, 'all.json'), 'w') as f:
        json.dump(cum_data, f)

    print('FINISHED. DATA WRITTEN TO:', args.folder)

    return


if __name__ == '__main__':
    main()
