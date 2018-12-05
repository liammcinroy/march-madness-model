# 

## Installation

This was developed using Python 3.5.2, but should work with any more recent release as well. To get the required python packages, simply execute

`python3 -m pip install -r requirements.txt`.

## Use

There are several steps to creating a model for predicting games. 

### Scraping

First, the data used to train the models must be scrapped from ESPN's online statistics database. This is implemented in the `scrape` module, but can also be executed from the commandline with

`python3 scrape.py [-v] file`

where `file` is the file which the obtained ESPN data will be written to (using JSON serialization). The `-v` option allows for further command line output about the operations and progress of the program.

Further details about how the data is scraped and what other options may be specified by importing the file can be found in [`DESIGN.md`](DESIGN.md)

### Feature Generation

After the raw data from ESPN is obtained, then it must be converted into a format which is easily trainable and conforms to `sklearn`'s standard. This is done in the `feature_gen` module, which also implements some nontrivial features which are obtained from the data. This can be done from the command line via

`python3 feature_gen.py infile outfile`

where `infile` is the ESPN datafile from `scrape` and `outfile` is the file which will contain all of the training features and labels.

Further details about which features are generated and how to exclude certain ones can be found in [`DESIGN.md`](DESIGN.md).

### Model training and evaluation

The final step in creating a model is training and evaluating its performance. This is done in `train_models`, and can be called from the command line by

`python3 train_models.py datafile modeltype`

where `datafile` points to the generated features file from `feature_gen` and `modeltype` is one of `TODO`. The output of `train_models.py` is the model's accuracy according to [K-fold cross validation](https://www.cs.cmu.edu/~schneide/tut5/node42.html), which estimates the generalization power of the models while still being able to train on the entire dataset. This allows us to choose the most accurate model.