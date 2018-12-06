# train_models.py
# This uses the data as generated by featuregen.py to train different models
# Developed by Liam McInroy on 11.30.18

import argparse
import json

import numpy as np

from pomegranate import BayesClassifier, MultivariateGaussianDistribution
from sklearn.metrics import accuracy_score
from sklearn.model_selection import KFold


def get_non_stat_input(X, y):
    """Get the inputs without the statistics identifiers

    Arguments:
        X: The initial features
        y: The initial labels
    """
    # exclude the time series identifying features since we aren't using a
    # temporal model
    _X = X[:, 1:]

    # get the features which don't have unknown values (just examine over the
    # target team's features, then double them over for the opposition's too
    cols = [jj for j in range(int(_X.shape[1] / 2)) if None not in _X[:, j]
            for jj in (j, j + int(_X.shape[1] / 2))]

    # restrict to not have unknown features
    _X = _X[:, cols]

    # get the rows which have valid data throughout
    rows = [i for i in range(_X.shape[0]) if None not in _X[i]]

    # restrict down
    return _X[rows], y[rows]


def get_stat_inputs(X, y):
    """Gets the input with the statistics identifiers, but cleans for learning

    Arguments:
        X: The initial features
        y: The initial labels
    """
    _X = X[:, 1:]

    # get the rows which have valid data throughout
    rows = [i for i in range(_X.shape[0]) if None not in _X[i]]

    return X[rows, 1:], y[rows]


def get_comp_stat_inputs(X, y):
    """Gets the input with the statistics identifiers, but cleans for learning
    and also gives the difference in the statistics for each feature.

    Arguments:
        X: The initial features
        y: The initial labels
    """
    # This one's inputs are only half the size, because the difference in each
    # feature is computed instead of trying to learn over all of them
    num_features = int((X.shape[1] - 1) / 2)

    # get the rows which have valid data throughout
    rows = [i for i in range(X.shape[0]) if None not in X[i]]

    # restrict down
    _X = X[rows, 0:num_features]

    # put if our team is home (1), away (-1), or neutral (0)
    _X[:, 0] = [1 if X[i, 1] else (-1 if X[i, 1 + num_features] else 0)
                for i in rows]

    # now we have to skip to start at n + 2 since we skip whether other team
    # is home or away
    _X[:, 1:] = X[rows, 2:num_features + 1] - X[rows, num_features + 2:]

    return _X, y[rows]


def train_naive_non_stat_bayes(X, y, **kwargs):
    """Train a naive bayesian model on the given features data, which doesn't
    use many of the team statistics since they're unreliably provided.

    Arguments:
        X: The features generated by feature_gen.py to train from
        y: The classes
        kwargs: For verbosity
            verbose: If greater than zero, then outputs basic information
                about the training process during training. Default 0.
            n_splits: The number of folds to use during KFold cross validation
                Default 5.
    """
    def printverbose(*msg):
        if kwargs.get('verbose', 0) > 0:
            print(*msg)

    _X, _y = get_non_stat_input(X, y)

    printverbose('Training with {} features'.format(_X.shape[1]))
    printverbose('Training on {} samples'.format(_X.shape[0]))

    # begin the training routine. We use K-fold to estimate the accuracy and
    # generalization power of the models
    sk_fold = KFold(n_splits=kwargs.get('n_splits', 5))
    cum_acc = 0
    for k, (train_idx, test_idx) in enumerate(sk_fold.split(_X, _y)):
        clf = BayesClassifier.from_samples(MultivariateGaussianDistribution,
                                           _X[train_idx],
                                           _y[train_idx].flatten())

        acc = accuracy_score(_y[test_idx].flatten(),
                             clf.predict(_X[test_idx]))
        printverbose('Fold {} accuracy: {}'.format(k + 1, acc))
        cum_acc = (k * cum_acc + acc) / (k + 1.)
        printverbose('\tCurrent cumulative accuracy:', cum_acc)

    print('Cumulative accuracy after {} folds: {}'.format(k + 1, cum_acc))


def train_naive_stat_bayes(X, y, **kwargs):
    """Train a naive bayesian classifier on the given features data, including
    the season average statistics for each team.

    Arguments:
        X: The features generated by feature_gen.py to train from
        y: The classes
        kwargs: For verbosity
            verbose: If greater than zero, then outputs basic information
                about the training process during training. Default 0.
            n_splits: The number of folds to use during KFold cross validation
                Default 5.
    """
    def printverbose(*msg):
        if kwargs.get('verbose', 0) > 0:
            print(*msg)

    _X, _y = get_stat_inputs(X, y)

    printverbose('Training with {} features'.format(_X.shape[1]))
    printverbose('Training on {} samples'.format(_X.shape[0]))

    # begin the training routine. We use K-fold to estimate the accuracy and
    # generalization power of the models
    sk_fold = KFold(n_splits=kwargs.get('n_splits', 5))
    cum_acc = 0
    for k, (train_idx, test_idx) in enumerate(sk_fold.split(_X, _y)):
        clf = BayesClassifier.from_samples(MultivariateGaussianDistribution,
                                           _X[train_idx],
                                           _y[train_idx].flatten())

        acc = accuracy_score(_y[test_idx].flatten(),
                             clf.predict(_X[test_idx]))
        printverbose('Fold {} accuracy: {}'.format(k + 1, acc))
        cum_acc = (k * cum_acc + acc) / (k + 1.)
        printverbose('\tCurrent cumulative accuracy:', cum_acc)

    print('Cumulative accuracy after {} folds: {}'.format(k + 1, cum_acc))


def train_comp_naive_stat_bayes(X, y, **kwargs):
    """Train a naive bayesian classifier on the given features data, including
    the season average statistics for each team. This is the same as
    naive_stat, EXCEPT this computes the difference in each value so there are
    less variables to learn over.

    Arguments:
        X: The features generated by feature_gen.py to train from
        y: The classes
        kwargs: For verbosity
            verbose: If greater than zero, then outputs basic information
                about the training process during training. Default 0.
            n_splits: The number of folds to use during KFold cross validation
                Default 5.
    """
    def printverbose(*msg):
        if kwargs.get('verbose', 0) > 0:
            print(*msg)

    _X, _y = get_comp_stat_inputs(X, y)

    printverbose('Training with {} features'.format(_X.shape[1]))
    printverbose('Training on {} samples'.format(_X.shape[0]))

    # begin the training routine. We use K-fold to estimate the accuracy and
    # generalization power of the models
    sk_fold = KFold(n_splits=kwargs.get('n_splits', 5))
    cum_acc = 0
    for k, (train_idx, test_idx) in enumerate(sk_fold.split(_X, _y)):
        clf = BayesClassifier.from_samples(MultivariateGaussianDistribution,
                                           _X[train_idx],
                                           _y[train_idx].flatten())

        acc = accuracy_score(_y[test_idx].flatten(),
                             clf.predict(_X[test_idx]))
        printverbose('Fold {} accuracy: {}'.format(k + 1, acc))
        cum_acc = (k * cum_acc + acc) / (k + 1.)
        printverbose('\tCurrent cumulative accuracy:', cum_acc)

    print('Cumulative accuracy after {} folds: {}'.format(k + 1, cum_acc))


def train_temporal_comp_stat_bayes(X, y, **kwargs):
    """Train a bayesian model which incorporates recent game results to
    estimate the momentum the team currently has (also could possibly
    marginalize over the momentum lost by player injuries?). Note that we
    assume that each opponent's prior history is conditionally independent
    of the result of the game given the target team's prior games. Not a great
    assumption but better than assuming that both team's prior performances are
    independent of the result of the game.

    We could also marginalize over of the prediction of the result of the game
    as predicted for the opposing team, but that still wouldn't quite be
    theoretically justified (although also closer).

    This specific model uses the comparative features in comp_naive_stat.

    Sadly, must note that pomegranate doesn't have Kalman filters, it instead
    discretizes the continuous space to make the HMM but it'll do.

    Arguments:
        X: The features generated by feature_gen.py to train from
        y: The classes
        kwargs: For verbosity
            verbose: If greater than zero, then outputs basic information
                about the training process during training. Default 0.
            n_splits: The number of folds to use during KFold cross validation
                Default 5.
    """
    return NotImplementedError()


# The collection of models trainable on. The 'model' command line argument
# must match one of the keys
_MODELS = {'naive_non_stat': train_naive_non_stat_bayes,
           'naive_stat': train_naive_stat_bayes,
           'comp_naive_stat': train_comp_naive_stat_bayes,
           'temporal_comp_stat': train_temporal_comp_stat_bayes,
           }


def parse_args():
    """To get the necessary arguments from the command line
    """
    parser = argparse.ArgumentParser(
        description='Training a model and getting an estimated level of '
                    'accuracy using Leave-One-Out cross validation.')
    parser.add_argument('data', type=str,
                        help='The feature, labels datasets to train on. '
                             'Should have been generated by feature_gen.py')
    parser.add_argument('model', type=str,
                        help='The type of model to train. Can select from: ' +
                             ', '.join(list(_MODELS.keys())))
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Whether to output more training information '
                             'execution and training.')
    return parser.parse_args()


def main():
    """When called from the command line
    """
    args = parse_args()

    X = np.array((0, 0))
    y = np.array((0, 0))
    try:
        with open(args.data, 'r') as f:
            X, y = json.load(f)
        # convert back to numpy since json can't serialize numpy arrays
        X = np.array(X, dtype=None)
        y = np.array(y, dtype=None)

    except:
        print('COULDN\'T OPEN', args.data)
        exit(1)

    if args.model not in _MODELS:
        print('INVALID MODEL')
        exit(1)

    # run the training routine
    _MODELS[args.model](X, y, verbose=args.verbose)


if __name__ == '__main__':
    main()
