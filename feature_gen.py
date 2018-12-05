# featuregen.py
# This file takes the output of scrape.py and then generates features for
# training predictive models from the games. The output will be a scipy
# valid training and testing dataset
# Developed 11.27.18 by Liam McInroy

import argparse
import datetime
import json

import numpy as np


def _teamWon(game, tid):
    """Determines if the targeted team won the game.

    Arguments:
        game: The game data object.
        tid: The target team to test if they won.
    """
    homeWin = game['score'][0] > game['score'][1]
    return not (game['homeId'] == tid ^ homeWin)


class FeatureGenerators():
    """Namespace for all the generators for features from data
    """
    def _atHomeFeature(series, tid):
        """Get whether the target team.

        Arguments:
            series: An ordered list of games (in dict form).
            tid: The team which is the targeted for this series.
        """
        def _generator():
            """The returned new generator. For each call yields the targeted
            team's value ONLY.
            """
            for game in series:
                homeTeam = game['homeId'] == tid
                yield homeTeam and not game['neutralSite']
        return _generator()

    def _streakFeature(series, tid):
        """Gets the current win/loss streak for the target team.

        Arguments:
            series: An ordered list of games (in dict form).
            tid: The team which is targeted for this series.
        """

        def _generator():
            """The returned new generator. For each call yields the targeted
            team's value ONLY.
            """
            streak = 0
            yield streak
            for i, game in enumerate(series):
                win = _teamWon(game, tid)
                if win and streak > 0:
                    streak += 1
                elif not win and streak < 0:
                    streak -= 1
                elif not win and streak > 0:
                    streak = -1
                else:
                    streak = 1

                # only return for data for games played prior to this one
                if i + 1 < len(series):
                    yield streak
        return _generator()

    def _winPctFeature(series, tid):
        """Gets the current win/loss percentage for the target team.

        Arguments:
            series: An ordered list of games (in dict form).
            tid: The team which is targeted for this series.
        """

        def _generator():
            """The returned new generator. For each call yields the targeted
            team's value ONLY.
            """
            wins = 0
            yield wins
            for i, game in enumerate(series):
                wins += 1 if _teamWon(game, tid) else 0

                # only return for games played prior to this one
                if i + 1 < len(series):
                    yield wins / (1. + i)
        return _generator()

    def _winPctRankedFeature(series, tid):
        """Gets the current win/loss percentage for the target team AGAINST
        ranked teams only.

        Arguments:
            series: An ordered list of games (in dict form).
            tid: The team which is targeted for this series.
        """

        def _generator():
            """The returned new generator. For each call yields the targeted
            team's value ONLY.
            """
            wins = 0
            rankedGames = 0
            yield wins
            for i, game in enumerate(series):
                if game['homeId'] == tid and game['awayRank'] > 0:
                    rankedGames += 1.
                    wins += 1 if _teamWon(game, tid) else 0
                elif game['homeId'] != tid and game['homeRank'] > 0:
                    rankedGames += 1.
                    wins += 1 if _teamWon(game, tid) else 0

                # only return for games played prior to this one
                if i + 1 < len(series):
                    yield wins / rankedGames if rankedGames > 0 else 0
        return _generator()

    def getAverageFeature(func):
        """Analyzes the average value of the func applied to each game

        Arguments:
            func: A function mapping a game data point and a target tid
                to a value which the average is calculated over
        """
        def _func(series, tid):
            """Analyzes a statistic and gives the average of it

            Arguments:
                series: An ordered list of games (in dict form)
                tid: The team which is the targeted for this series
            """
            def _generator():
                """The returned new generator. For each call yields the
                targeted team's value ONLY.
                """
                # begin with zero since there are no priors for the first
                # game of the season. If predicting on post-season, then
                # possibly manually insert?
                yield 0
                avg = 0
                for i, game in enumerate(series):
                    avg = (i * avg + func(game, tid)) / (i + 1.)
                    if len(series) > i + 1:
                        yield avg
            return _generator()
        return _func

    def getStatisticFunc(label):
        """Returns a function which gives the statistics from the game for the
        given label.

        Arguments:
            label: The label used to refer to the statistic. For instance
                blocks has label 'BLK' in ESPN.
        """

        def _func(game, tid):
            """Does the actual extracting. Returns as a float

            Arguments:
                game: The game data object.
                tid: The target team to calculate for..
            """
            if game['homeId'] == tid:
                return float(game['home' + label])
            else:
                return float(game['away' + label])

        return _func

    def _getPF(game, tid):
        """Gets the points for the team for this game.

        Arguments:
            game: The game data object.
            tid: The target team to calculate for.
        """
        if game['homeId'] == tid:
            return float(game['score'][0])
        else:
            return float(game['score'][1])

    def _getPA(game, tid):
        """Gets the points against the team for this game.

        Arguments:
            game: The game data object.
            tid: The target team to calculate for.
        """
        if game['homeId'] == tid:
            return float(game['score'][1])
        else:
            return float(game['score'][0])

    def _getFGPct(game, tid):
        """Gets the FG percentage for the team for this game.

        Arguments:
            game: The game data object.
            tid: The target team to calculate for.
        """
        if game['homeId'] == tid:
            made, miss = game['homeFG'].split('-')
            return float(made) / (int(made) + int(miss))
        else:
            made, miss = game['awayFG'].split('-')
            return float(made) / (int(made) + int(miss))

    def _get3PTPct(game, tid):
        """Gets the 3PT percentage for the team for this game.

        Arguments:
            game: The game data object.
            tid: The target team to calculate for.
        """
        if game['homeId'] == tid:
            made, miss = game['home3PT'].split('-')
            return float(made) / (int(made) + int(miss))
        else:
            made, miss = game['away3PT'].split('-')
            return float(made) / (int(made) + int(miss))

    # ALL of the possible features and their corresponding calculating functors
    # Calling each functor (given the season games) returns a generator who on
    # calls to returns the next point in the time series.
    ALL = {
            'atHome': _atHomeFeature,
            'streak': _streakFeature,
            'win%': _winPctFeature,
            'seasonWin%Ranked': _winPctRankedFeature,
            'seasonBLK': getAverageFeature(getStatisticFunc('BLK')),
            'seasonSTL': getAverageFeature(getStatisticFunc('STL')),
            'seasonDREB': getAverageFeature(getStatisticFunc('DREB')),
            'seasonOREB': getAverageFeature(getStatisticFunc('OREB')),
            'seasonAST': getAverageFeature(getStatisticFunc('AST')),
            'seasonFT': getAverageFeature(getStatisticFunc('FT')),
            'seasonTO': getAverageFeature(getStatisticFunc('TO')),
            'seasonPF': getAverageFeature(_getPF),
            'seasonPA': getAverageFeature(_getPA),
            'seasonFG%': getAverageFeature(_getFGPct),
            'season3PT%': getAverageFeature(_get3PTPct),
            }


def generate_features(data, **kwargs):
    """Generate the features from the raw data as downloaded from scrape.py
    Returns two tables: X and y for features and labels

    Arguments:
        data: The raw data dictionary as given by scrape.py
        kwargs: Which features to include/exclude and verbosity
            verbose: If positive gives error messages
                     If greater than 1 gives other useful debug messages
            exclude_features: A list of features to exclude (must match a key
                from the POSSIBLE_FEATURES dictionary)
    """
    def printveryverbose(*msg):
        if kwargs.get('verbose', 0) > 1:
            print(*msg)

    def printverbose(*msg):
        if kwargs.get('verbose', 0) > 0:
            print(*msg)

    def _json_date(gid):
        """returns the datetime of the given gid
        """
        # json compatibility. If just read from a file then the keys to dicts
        # get converted to strings
        if gid not in data:
            gid = str(gid)
        if gid not in data:
            gid = int(gid)
        return datetime.datetime.strptime(data[gid]['date'],
                                          '%Y-%m-%dT%H:%MZ')

    # get the features to generate for this dataset
    features = {name: func for name, func in FeatureGenerators.ALL.items()
                if name not in kwargs.get('exclude_features', [])}

    printveryverbose(features)

    # The X, y consisting of the series, not individual datapoints
    X_series = []
    y_series = []

    # the time-series unique id discussed below
    series_idx = 0

    for year in data['years']:
        # we generate quite a few different features. While we borrow some from
        # ESPN directly, we also create some of our own (as well as sort them
        # for convenience when training temporal models).

        # we also organize each teams' data for the season into its own
        # time-series so its easier to train a temporal model without having to
        # do a ton of reordering. Therefore, we give a separate unique
        # "series ID" that can be ignored by a non-temporal model but can also
        # be used by a temporal model to distinguish beginnning/end of series

        # Since each team's season has its own unique identifier, then we will
        # end up with many duplicate games (exactly two duplicates) so that the
        # model can learn which features to treat as the "current team" and
        # which are just considered the opposition of that game

        # Therefore, we also order the data by all current team's info then
        # all of the opposition's info (with duplicates for points that apply
        # to both, for instance if it is a neutral site) in case we ever train
        # some translation invariant model on the data (for example a
        # convolutional neural network) So there will be distinct inputs, but
        # in a nontemporal model then the two representations are equal.
        # (This also prevents the model from biasing towards the "home" when
        # there is a neutral site, which is very important in college. Then
        # we can also average between the two different representations if
        # at a neutral site during the tournament)

        # a dictionary mapping each game id to a dict with each of the opposing
        # teams' ids with their calculated features. After this is filled, it
        # is distilled into the final matrix
        features_unmatched = {}

        for tid in data['teams']:
            # json compatibility
            if year not in data['teams'][tid]:
                year = str(year)

            # preprocess the list we have, make sure they exist in the table
            gids = data['teams'][tid][year]['reg']
            for gid in gids:
                if str(gid) not in data and int(gid) not in data:
                    data['teams'][tid][year]['reg'].remove(gid)

            # sort all the games this season
            series_gids = sorted(data['teams'][tid][year]['reg'],
                                 key=_json_date)
            # for json compatibility since keys turn to ints
            tid = int(tid)

            series = [data[str(gid)] if gid not in data else data[gid]
                      for gid in series_gids]

            for game in series:
                printveryverbose(game['date'])  # sanity check for sorting

            # the training features for this team FOR this season only
            # go through all the features, but sort by name so that get the
            # same order on every datapoint
            for j, (name, fGen) in enumerate(sorted(features.items())):
                try:
                    for i, v in enumerate(fGen(series, tid)):
                        # if the game has no values, then create its entry
                        if series_gids[i] not in features_unmatched:
                            features_unmatched[series_gids[i]] = \
                                {series[i]['homeId']: [None] * len(features),
                                 series[i]['awayId']: [None] * len(features)}
                        # insert the value
                        features_unmatched[series_gids[i]][tid][j] = v
                except:
                    # it failed for that generator, so we just continue on the
                    # rest of them and don't bother setting any values for
                    # this specific generator for that series. The rest will
                    # fill in if they succeed in generating
                    printveryverbose('ERROR generating:', tid, name)

        # now that we have all the features for every team for every game,
        # we can generate the final tables
        for tid in data['teams']:
            # increment so that a new series (aka team's season) is identified
            series_idx += 1

            # since each season is so short, it is better to just recompute
            # the sorting of the games since otherwise the memory becomes too
            # large when we have 350 teams with 27-29 games
            series_gids = sorted(data['teams'][tid][year]['reg'],
                                 key=_json_date)  # already checked existance

            # no more calls to data, so can change to int because
            # features_unmatched always uses integers on internal
            tid = int(tid)

            # make the table for the team, number of features for each team
            # and also the unique series identification
            teamX = np.full((len(series_gids), 1 + 2 * len(features)),
                            None, dtype=None)

            # for now, we only consider the outcome as a binary variable rather
            # than a range of possible scores.
            teamY = np.full((teamX.shape[0], 1), 0, dtype=int)
            for i, gid in enumerate(series_gids):
                game = data[str(gid)] if gid not in data else data[gid]

                # get the result of the game and the opposing team's id
                opp_tid = -1
                if game['homeId'] == tid:
                    opp_tid = game['awayId']
                    teamY[i, 0] = game['score'][0] > game['score'][1]
                else:
                    opp_tid = game['homeId']
                    teamY[i, 0] = game['score'][1] > game['score'][0]

                # set the features. series_idx followed by target team's
                # features followed by the opposing team's features
                teamX[i, 0] = series_idx
                mid = len(features) + 1
                teamX[i, 1:mid] = features_unmatched[gid][tid]
                teamX[i, mid:] = features_unmatched[gid][opp_tid]

            X_series.append(teamX)
            y_series.append(teamY)

    # stack all the series so that we can train on individual games instead
    # of just series of games
    return (np.vstack(X_series), np.vstack(y_series))


def parse_args():
    """Get the necessary arguments when called from the command line instead
    of when loaded from another script
    """
    parser = argparse.ArgumentParser(
        description='Take the raw data as downloaded from scrape.py and '
                    'process it into features for training a model on.')
    parser.add_argument('infile', type=str,
                        help='The file which the raw downloaded data is in.')
    parser.add_argument('outfile', type=str,
                        help='The file to save the generated features to.')
    return parser.parse_args()


def main():
    """Called when using from the command line
    """
    args = parse_args()

    data = {}
    with open(args.infile, 'r') as f:
        data = json.load(f)

    X, y = generate_features(data)
    with open(args.outfile, 'w') as f:
        json.dump((X, y))


if __name__ == '__main__':
    main()
