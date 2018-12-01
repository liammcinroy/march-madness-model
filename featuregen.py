# featuregen.py
# This file takes the output of scrape.py and then generates features for
# training predictive models from the games. The output will be a scipy
# valid training and testing dataset
# Developed 11.27.18 by Liam McInroy

import argparse
import pickle


def generate_features(data):
    """Generate the features from the raw data as downloaded from scrape.py

    Arguments:
        data: The raw data dictionary as given by scrape.py
    """

    # 

    return NotImplementedError()


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
