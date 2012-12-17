import webapp2
import math
import datetime
import jinja2
import os
import logging

from app.models import *
from google.appengine.api import users

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class ActiveUser():
  def __init__(self):
    # initialize with a appengine user object
    self.loaded = False
    if self.load():
      self.loaded = True
    
  def load(self):
    user = users.get_current_user()
    if user:
      u = self.find_or_add_user(user)
      self.userid = u.userid
      self.nickname = u.nickname
      self.rating = u.rating
      self.is_scorekeeper = u.is_scorekeeper
      self.include_in_rankings = u.include_in_rankings
      self.signout_url = users.create_logout_url("/")
      return True

  def find_or_add_user(self,user):
    if user:
      u = Competitor.by_id(user.user_id())
      if u is None:
        u = Competitor(
            userid = user.user_id(),
            nickname = user.nickname()
            )
        u.put()
        logging.info("added competitor " + u.userid)
      else:
        logging.info("recognised competitor " + u.userid)
      return u

################

class MainHandler(webapp2.RequestHandler):
  def get(self):
    user = ActiveUser()
    if user.loaded:
      template_values = {
          "rankings": Competitor.ordered(),
          "user": user
          }
      template = jinja_environment.get_template('templates/index.html')
      self.response.out.write(template.render(template_values)) 

    else:
      greeting = ("You are not signed in. <a href=\"%s\">Join the competition</a>." %
           users.create_login_url("/"))
      self.response.out.write("<html><body>%s</body></html>" % greeting)

class ResultsHandler(webapp2.RequestHandler):
  def get(self):
    user = ActiveUser()
    if self.request.get("userid"):
      competitor = Competitor.by_id(self.request.get("userid"))
      logging.info("get results for %s " % (competitor.nickname))
      results = Result.all_for(competitor.userid)
    else:
      competitor = None
      results = Result.all_results()

    template_values = {
        'results': results, 
        'competitor': competitor,
        'user': user
        }
    template = jinja_environment.get_template('templates/results.html')
    self.response.out.write(template.render(template_values)) 

class AddResultHandler(webapp2.RequestHandler):
  def get(self):
    user = ActiveUser()
    if user.is_scorekeeper:

      winner_id = self.request.get("W")
      loser_id = self.request.get("L")
      if self.request.get("result_submit") == "submit" and winner_id != loser_id:
          
        winner = Competitor.by_id(winner_id)
        loser = Competitor.by_id(loser_id)
        
        self.process_match_result(winner,loser)
             
        self.redirect("/")
      else:  
        template_values = {
            'competitors': Competitor.ordered(),
            'user': user
          }
        template = jinja_environment.get_template('templates/result.html')
        self.response.out.write(template.render(template_values)) 

    else:
      self.redirect("/")

  
  def process_match_result(self, winner, loser):
    logging.info("result: %s(%s) defeated %s(%s)" % (winner.nickname, winner.rating, loser.nickname, loser.rating))
        
    new_ratings = EloRating.calculate_elo_rank(winner.rating,loser.rating)

    logging.info("new ratings are:")
    logging.info("  %s - %s" % (winner.nickname, new_ratings[0]))
    logging.info("  %s - %s" % (loser.nickname, new_ratings[1]))

    res = Result(
        date_played = datetime.datetime.now(),
        winner_user_id = winner.userid,
        loser_user_id = loser.userid,
        winner_old_rating = winner.rating,
        loser_old_rating = loser.rating,
        winner_new_rating = new_ratings[0],
        loser_new_rating = new_ratings[1] 
        )
    res.put()
    
    winner.rating = new_ratings[0]
    winner.put()
    loser.rating = new_ratings[1]
    loser.put()

class EloRating():

  # cribbed from http://forrst.com/raw_code/621864f2a579e520cc5c29159d233a2185d8d5bb
  @staticmethod
  def calculate_elo_rank(winner_rank, loser_rank):
    k = EloRating.get_k_factor(winner_rank)
    rank_diff = winner_rank - loser_rank
    exp = (rank_diff * -1) / 400
    odds = 1 / (1 + math.pow(10, exp))
    new_winner_rank = round(winner_rank + (k * (1 - odds)))
    new_rank_diff = new_winner_rank - winner_rank
    new_loser_rank = loser_rank - new_rank_diff
    if new_loser_rank < 1:
      new_loser_rank = 0.0
    return (new_winner_rank, new_loser_rank)

  @staticmethod
  def get_k_factor(winner_rank):
    if winner_rank < 2100:
      return 32
    if winner_rank >= 2100 and winner_rank < 2400:
      return 24
    return 16


