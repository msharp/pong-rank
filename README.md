# Pong Ranker

Uses the [Elo rating system](http://en.wikipedia.org/wiki/Elo_rating_system) to maintain a ranking of competitors. In my case, used to rank table tennis players at my workplace.

## Users

This is a GAE app. The user system is piggy backed off the Google authentication API provided. To register, a competitor needs a google account.

## Todo

  - _undo_ a result by winding back all adjustments and replaying the subsequent results to readjust ranking
  - feature which estimates the probable ranking changes if a player defeats another player 
  - docking of points if no matches played in set time period (+ points awarded for playing high number of matches ?? top 20% of playing frequency)

