
from google.appengine.ext import db

BASE_RANK = 1200.0

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

  def winner_name(self):
    c = Competitor.by_id(self.winner_user_id)
    return c.nickname

  def loser_name(self):
    c = Competitor.by_id(self.loser_user_id)
    return c.nickname

  def points_transacted(self):
    return self.winner_new_rating - self.winner_old_rating

  @staticmethod
  def all_results():
    q = Result.all()
    q.order('-date_played')
    q.get()
    return [c for c in q]
    
  @staticmethod
  def user_result(userid, won=True):
    q = Result.all()
    q.order('-date_played')
    if won:
      q.filter('winner_user_id =', userid)
    else:
      q.filter('loser_user_id =', userid)
    q.get()
    return [c for c in q]
  
  @staticmethod
  def all_for(userid):
    won = Result.user_result(userid, True)
    lost = Result.user_result(userid, False)
    return won + lost

class RatingAdjustment(db.Model):
  userid = db.StringProperty()
  date = db.DateTimeProperty()
  old_rating = db.FloatProperty()
  new_rating = db.FloatProperty()
  reason = db.StringProperty()


