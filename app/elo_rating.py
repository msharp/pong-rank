import math
import datetime
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

