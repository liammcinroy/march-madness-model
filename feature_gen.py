# featuregen.py
# This file takes the output of scrape.py and then generates features for
# training predictive models from the games. The output will be a scipy
# valid training and testing dataset
# Developed 11.27.18 by Liam McInroy

import argparse
import datetime
import pickle

import numpy as np


class FeatureGenerators():
    """Namespace for all the generators for features from data
    """

    def atHomeFeature(series, tid):
        """Get whether the target team (which is always the first in the
        returned data) played at home.

        Arguments:
            series: An ordered list of games (in dict form)
            tid: The team which is the targeted for this series
        """
        def _generator():
            """The returned new generator. For each call yield a pair of
            the targeted teams value then the oppositions value
            """
            for game in series:
                homeTeam = game['homeId'] == tid
                yield (homeTeam and not game['neutralSite'],
                       not homeTeam and not game['neutralSite'])
        return _generator()

    # ALL of the possible features and their corresponding calculating functors
    # Calling each functor (given the season games) returns a generator who on
    # calls to returns the next point in the time series.
    ALL = {
            'atHome': atHomeFeature}
    """,
            'record': ,
            'rank': ,
            'seasonBLK': ,
            'seasonSTL': ,
            'seasonDREB': ,
            'seasonOREB': ,
            'seasonPF': ,
            'seasonPA': ,
            'seasonFG': ,
            'season3PT': ,
            'seasonFT': ,
            'seasonTO': ,
            'streak': ,
            }"""


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

        for tid in data['teams']:
            # increment so that a new series (aka team's season) is identified
            series_idx += 1

            # sort all the games this season
            series_gids = sorted(data['teams'][tid][year]['reg'],
                                 key=_json_date)
            series = [data[gid] for gid in series_gids]

            for game in series:
                printveryverbose(game['date'])  # sanity check for sorting

            # the training features for this team FOR this season only
            teamX = np.full((len(data['teams'][tid][year]['reg']),
                             1 + 2 * len(features)), None, dtype=None)  # TODO type
            teamX[:, 0] = series_idx

            features_unproc = [[v for v in fGen(series, tid)]
                               for name, fGen in features.items()]
            for j, (name, fGen) in enumerate(features.items()):  # TODO get in sorted, same order everytime
                # the columns which correspond to this feature for home, away team
                col_idxes = (1 + j, 1 + j + len(features))
                printveryverbose(name, col_idxes)
                for i, v in enumerate(fGen(series, tid)):
                    teamX[i, col_idxes] = v

            teamY = None  # TODO

            X_series.append(teamX)
            y_series.append(teamY)

    # stack all the series so that we can train on individual games instead of just series of games
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
    with open(args.infile, 'rb') as f:
        data = pickle.load(f)

    return NotImplementedError()


if __name__ == '__main__':
    main()
