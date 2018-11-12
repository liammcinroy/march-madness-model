# Data Mining

To find the source, go into developer console when polling and filter network resources by XHR returns, then look for links which return the JSON with the data wanted.

## Playing with the JSON in Python

Do something similar to 


    import requests

    requests.get(url).json()


## For NCAAM Season Play data

For getting specific team in date then look at 

`https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/[TEAMID]/schedule?region=us&lang=en&season=[YEAR]&seasontype=2`

Can get the team IDs by iterating through each conference groups id from 

`https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard/conferences?groups=50` and within the `data['conferences']` array then looking them all up via

`https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams?groups=GROUPSID` within `data['sports'][0]['leagues'][0]['teams'][TEAMIDX]`.

Playing with data from the team season schedule you can get the game results via

`data['events'][GAMEIDX]['competitions'][0]['competitors'][0 or 1]['id', 'score['value']', 'winner', 'etc.']`

Also have a bunch of other interesting data like whether home or away or neutral, etc. that could be played with.

This gives 28 games in 2003, up to 34 in 2017 (NOTE TO DISTINGUISH BETWEEN LATE AND EARLY SEASON? Don't know).

There are 347-354 teams (get 354 via query but 347 online?), so then that gives minimally 72k games? However much fewer will apply to the actual tournament qualifiers (maximally 27k, but still a lot)

### Tournament data?

Perhaps [here](https://data.world/michaelaroy/ncaa-tournament-results)?

# Approach

Perhaps chess ranking strategy?

Just straight data science technique over? Bayes net or neural net?

Apply some HPC to this? How is it parallelizable?
