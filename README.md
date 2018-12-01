# Data Mining

To find the source, go into developer console when polling and filter network resources by XHR returns, then look for links which return the JSON with the data wanted.

## Playing with the JSON in Python

Do something similar to 


    import requests

    requests.get(url).json()


## For NCAAM Season Play data

For getting specific team data from the regular season then look at 

`https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/[TEAMID]/schedule?region=us&lang=en&season=[YEAR]&seasontype=2`

Can get the team IDs by iterating through each conference groups id from 

`https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard/conferences?groups=50` and within the `data['conferences']` array then looking them all up via

`https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams?groups=GROUPSID` within `data['sports'][0]['leagues'][0]['teams'][TEAMIDX]`.

Playing with data from the team season schedule you can get the game results via

`data['events'][GAMEIDX]['competitions'][0]['competitors'][0 or 1]['id', 'score['value']', 'winner', 'etc.']`

The post season games can be found from

`https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/[TEAMID]/schedule?region=us&lang=en&season=[YEAR]&seasontype=3`

HOWEVER, note that the year will be the year the post season was played in, eg. 2008 is the postseason of the 2007-2008 season!

Also have a bunch of other interesting data like whether home or away or neutral, etc. that could be played with.

If you look at `data['events'][GAMEIDX]['id']` under

`http://cdn.espn.com/core/mens-college-basketball/boxscore?xhr=1&gameId=[GAMEID]`

then there is more interesting data such as

`data['gamepackageJSON']['boxscore']`

This gives 28 games in 2003, up to 34 in 2017. Note that the year refers to the year which that season ended, eg. 2007 refers to the 2006-07 season.

There are 347-354 teams (get 354 via query but 347 online?), so then that gives minimally 72k games? However much fewer will apply to the actual tournament qualifiers (maximally 27k, but still a lot)

Digging into each game's boxscore, we can find the general game statistics through `data['__gamepackage__']['homeTeam' or 'awayTeam']`

`data['gamepackageJSON']['boxscore']['players'][0 or 1]['statistics'][0]['totals']` which represent `data['gamepackageJSON']['boxscore']['players'][0 or 1]['statistics'][0]['labels']`. These become tracked starting in the 2006 season, but aren't before then. Also available for every player on the team, so we can generate a lot of data given a subset of starters.

### Tournament data?

Perhaps [here](https://data.world/michaelaroy/ncaa-tournament-results)?

### Vegas Odds

Can get vegas odds from 2007 to 2017 [here](https://www.sportsbookreviewsonline.com/scoresoddsarchives/ncaabasketball/ncaabasketballoddsarchives.htm), but that restricts the data further.

# Approach

Perhaps chess ranking strategy?

Just straight data science technique over? Bayes net or neural net?

Apply some HPC to this? How is it parallelizable?
