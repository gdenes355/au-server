from models import AUGame, AUPlayer

import json
import datetime
import time
from collections import Counter
import random



VOTING_TIMEOUT = 20

def full_game_as_dict(game):
    res = dict()
    res["state"] = game.state
    res["target"] = game.target
    res["players"] = list()
    res["map"] = game.game_map
    for player in game.players:
        res["players"].append(dict(
            xs=player.xs,
            ys=player.ys,
            vx=player.vx,
            vy=player.vy,
            seq=player.seq,
            col=player.col,
            id=player.id,
            mask=player.mask,
            name=player.name
        ))
    return res

def start_game(game):
    if game.state != AUGame.State.LOBBY:
        return
    game.state =  AUGame.State.GAME
    game.target = (len(game.players) - 2) * 5
    impostors = random.sample(game.players, game.impostor_count)
    for imp in impostors:
        imp.mask = AUPlayer.Mask.IMPOSTOR

def meet_to_vote(game, player: AUPlayer = None):
    if game.state != AUGame.State.GAME:
        return

    for aplayer in game.players:
        aplayer.mask = aplayer.mask & ~AUPlayer.Mask.CALLED_VOTE
        aplayer.voted_against = AUPlayer.NOT_VOTED

    if player is not None:
        player.mask = player.mask | AUPlayer.Mask.CALLED_VOTE

    game.state = AUGame.State.VOTING
    game.voting_started = datetime.now()

def stop_voting(game):
    print("Voting stopped")
    game.voting_started = datetime.now() - datetime.timedelta(seconds=76)

def process_game(game):
    imp_count = 0
    crew_count = 0
    for player in game.players:
        if not player.is_voted_out() and not player.is_dead():
            if player.is_impostor():
                imp_count += 1
            else:
                crew_count += 1

    if game.state == AUGame.State.GAME:
        if game.target < 1 or imp_count == 0:
            game.state = AUGame.State.FINISHED
            print('class wins', game)
        elif imp_count >= crew_count:
            game.state = AUGame.State.FINISHED
            print('impostors win', game)
    elif game.state == AUGame.State.VOTING:
        finished = all(((p.voted_against > AUPlayer.NOT_VOTED) or (not p.can_vote())) for p in game.players)
        time_in_voting = datetime.now() - game.voting_started
        if finished or time_in_voting.total_seconds() > VOTING_TIMEOUT:
            # accumulate votes
            votes = []
            for p in game.players:
                if p.can_vote():
                    votes.append(p.voted_against if p.voted_against > AUPlayer.NOT_VOTED else AUPlayer.SKIPPED_VOTE)
            votes = dict(Counter(votes))
            vote_values = sorted(votes.values())
            s_to_vote_out = -1

            if len(vote_values) == 0:
                pass
            if len(vote_values) == 1:
                s_to_vote_out = vote_values[0]
            elif vote_values[-1] != vote_values[-2]:
                s_to_vote_out = vote_values[-1]

            if s_to_vote_out != AUPlayer.SKIPPED_VOTE:
                # someone is getting voted out
                for p in game.players:
                    if p.id in votes and votes[p.id] == s_to_vote_out:
                        p.mask = p.mask | AUPlayer.Mask.VOTED_OUT
                        break
            game.state = AUGame.State.GAME
