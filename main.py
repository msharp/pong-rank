#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import math
import datetime
import jinja2
import os
import logging

from google.appengine.api import users
from google.appengine.ext import db

BASE_RANK = 1200.0

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Competitor(db.Model):
  userid = db.StringProperty()
  nickname = db.StringProperty()
  rating = db.FloatProperty(default=BASE_RANK)
  include_in_rankings = db.BooleanProperty(default=True)
  is_scorekeeper = db.BooleanProperty(default=False)

  @staticmethod
  def ordered():
    r = Competitor.all()
    r.filter("include_in_rankings =", True)
    r.order("-rating")
    return [c for c in r] 

  @staticmethod
  def by_id(id):
    r = Competitor.all()
    r.filter("userid =", id)
    return r.get()


class Result(db.Model):
  date_played = db.DateTimeProperty()
  winner_user_id = db.StringProperty()
  loser_user_id = db.StringProperty()
  winner_old_rating = db.FloatProperty()
  loser_old_rating = db.FloatProperty()
  winner_new_rating = db.FloatProperty()
  loser_new_rating = db.FloatProperty()


class MainHandler(webapp2.RequestHandler):
  def get(self):
    u = users.get_current_user()
    if u:
      user = self.find_or_add_user(u)
      
      template_values = {
          "rankings": Competitor.ordered(),
          "user": user,
          "signout_url": users.create_logout_url("/")
          }
    
      template = jinja_environment.get_template('templates/index.html')
      self.response.out.write(template.render(template_values)) 

    else:
      greeting = ("You are not yet a member of the competition. <a href=\"%s\">Join the competition</a>." %
           users.create_login_url("/"))
      self.response.out.write("<html><body>%s</body></html>" % greeting)

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


class ResultHandler(webapp2.RequestHandler):
  def get(self):
    u = users.get_current_user()
    user = Competitor.by_id(u.user_id())
    logging.info("got %s (%s)" % (user.nickname, user.is_scorekeeper))
    if user.is_scorekeeper:

      winner_id = self.request.get("W")
      loser_id = self.request.get("L")
      if self.request.get("result_submit") == "submit" and winner_id != loser_id:
          
        winner = Competitor.by_id(winner_id)
        loser = Competitor.by_id(loser_id)
        
        logging.info("result: %s(%s) defeated %s(%s)" % (winner.nickname, winner.rating, loser.nickname, loser.rating))
        
        new_ratings = self.calculate_elo_rank(winner.rating,loser.rating)

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
      
        self.redirect("/")
      else:  
        template_values = {"competitors": Competitor.ordered()}
        template = jinja_environment.get_template('templates/result.html')
        self.response.out.write(template.render(template_values)) 

    else:
      self.redirect("/")

  # cribbed from http://forrst.com/raw_code/621864f2a579e520cc5c29159d233a2185d8d5bb
  def calculate_elo_rank(self, winner_rank, loser_rank):
    k = self.get_k_factor(winner_rank)
    rank_diff = winner_rank - loser_rank
    exp = (rank_diff * -1) / 400
    odds = 1 / (1 + math.pow(10, exp))
    new_winner_rank = round(winner_rank + (k * (1 - odds)))
    new_rank_diff = new_winner_rank - winner_rank
    new_loser_rank = loser_rank - new_rank_diff
    if new_loser_rank < 1:
      new_loser_rank = 0.0
    return (new_winner_rank, new_loser_rank)

  def get_k_factor(self,winner_rank):
    if winner_rank < 2100:
      return 32
    if winner_rank >= 2100 and winner_rank < 2400:
      return 24
    return 16

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/result', ResultHandler)
], debug=True)

