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
