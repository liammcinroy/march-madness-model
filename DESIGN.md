# Design

This document contains specific implementation details for each of the modules.

## `scrape.py`

By making calls to ESPN's backend server, we are able to obtain the JSON files that they use to generate their webpages. There are several steps to getting all the data needed.

First, ESPN refers to each team by a unique id, which we must first obtain a set of. This is done by examining the teams in each conference. Each conference is found via a request to

`https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard/conferences?groups=50`

and then the team ids can be extracted from

`https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams?groups=[GROUPSID]`

for each `GROUPSID`. Then, we can get a given team's schedule for a particular season and find the unique game ids by a lookup to 

`https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/[TEAMID]/schedule?region=us&lang=en&season=[YEAR]&seasontype=2`

where a `YEAR` of `2006` refers to the season ending in `2006` for example. Note that we then examine the years `2006-2018` since they are the only completed seasons that ESPN began collecting and storing team statistics data for (eg. blocks, steals, etc). After getting the set of all game ids for a season for the team, then we iterate through all the game ids and populate a dataset with information from

`http://cdn.espn.com/core/mens-college-basketball/boxscore?xhr=1&gameId=[GAMEID]`

The information for each game includes the date, who played, whether it was a neutral stadium, the final and halftime scores, the records and ranks of each team, and the total number of blocks, steals, attempted shots, three pointers, and defensive and offensive rebounds for each team.

All of this data is stored in a dictionary and saved to the disk in JSON format. The dictionary contains each game as identified by its id, but also a collection of the different team ids and a list of the game ids they played in for each season.


Finally, note that all the functions implemented in `scrape.py` are designed to be functional when imported as well, and contain specific documentation about their arguments and use in the source.

## `feature_gen.py` 

After all the data is received, then we process it into a format that is convenient for training a predictive model on. Since `sklearn` is the canonical python library to use for similar problems, then we follow their data format. This means we separate the data into two matrices, `X` and `y`. The matrix `X` has each row as an independent data point where each column is a specific feature and the matrix `y` has each row the label for the corresponding data point.

Since we want the functionality to create a temporal model which examines a team's performance over the whole season, then we want each features computation process to have access to the data prior to it in the season. This requires that for each game, we consider each team a different datapoint so that our model can how to track the performance of that team over time. We do this by making each feature computed via a generator, which are defined within `FeatureGenerators`. The dictionary `FeatureGenerators.ALL` contains the name of the feature and a function which when called with a given series of games computes a specific team's values. Then, after all the season values have been computed for every team, the opposition team for each game has its opposite values inputted for each game it participated in which it was not the tracked team during. Finally, the label of the model is simply just whether the current tracked team won each game.

At the conclusion of this computation, then `X` and `y` are returned and saved to a JSON file.

Finally, note that all the functions implemented in `feature_gen.py` are designed to be functional when imported as well, and contain more specific documentation on their exact use in the source.

#### `FeatureGenerators.HiddenSpaceGenerator`

This function takes an already formed feature dataset and trains a Hidden Markov Model over it to attempt to generate more entirely machine learning based features that model the team's performance over time. The HMM then examines a team's performance over time and generates its hidden state for each game, which it then appends to the features that the final classifier will use to predict the outcome of each game. It still is not entirely theoretically justified, as it still creates the assumption that the outcome of each game given the both team's temporal history is conditionally independent of the outcome given just the targeted team's temporal history, but in practice it marginally improves performance. With more time, this could be applied to many of the features and then the final result could be marginalized over them all so that there are no unnecessary assumptions about the conditional independence of the outcome of the game.

## `train_models.py`

There are several different models defined in `train_models.py` and are identified by `_MODELS`. We give a brief description of each model below, but note that each model has a `temporal` counterpart which includes the HMM hidden space feature mentioned above. These in practice perform better than the naive, nontemporal version (but insignificantly so).

#### `naive_non_stat`

This model is a simple Bayesian classifier (implemented using [`pomegranate`](https://github.com/jmschrei/pomegranate/tree/master/pomegranate)) which trains a multivariate gaussian distribution over the all of the non-statistics based features. This means the features which we have for every team, namely `atHome`, `win%`, `streak`, `seasonPF`, `seasonPA`, and `seasonWin%Ranked` since ESPN has always collected the data necessary to compute these features. Then, the model is trained on each game as if they were independent (which they aren't but it's easier to test preliminarily). We choose to exclude certain features so that we can capture as many data points as possible. This nets us over 133,000 training examples, which is nearly `70,000` games. With a fold of `5`, it looks like the model has a successful prediction rate of nearly `70%`.

#### `naive_stat`

This is the exact same as `naive_non_stat`, except for it uses the additional statistics information which ESPN provides. However, since this data is missing for many games, then we must exclude those games so we end up with 86,000 training examples instead (or 43,000 games). This model performs worse than `naive_non_stat`, likely because there are too many variables with no structure defined between them. It achieves `57%` accuracy, which is still better than random guessing.

#### `comp_naive_stat`

Since `naive_stat` seemed to fail at learning any better despite having more data to learn from, then we attempt to simplify the model further. Therefore, `comp_naive_stat` has the exact same dataset, except for it subtracts the opposition's statistical values from this team's statistics, so there are half as many features to learn from. This still isn't a great model and there isn't enough data to find the truly most influential values, but it improves on `naive_stat` to `60%` accuracy, so we're on the right track.
