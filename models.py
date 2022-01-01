from datetime import datetime, timedelta


class AUGame(object):

    class State(object):
        LOBBY = 'Lobby'
        VOTING = 'Voting'
        GAME = 'Game'
        FINISHED = 'Finished'

    PLAYER_COLS = set(['c51111', '132ed1', '117f2d', 'ed54ba', 'ef7d0d', 'f5f557', '3f474e', 'd6e0f0', '6b2fbb', '71491e', '38fedc', '50ef39'])

    def __init__(self, *args, **kwargs):
        super(AUGame, self).__init__()
        self.state = AUGame.State.LOBBY
        self.code = kwargs['code']
        self.target = 0
        self.voting_started = datetime.now()
        self.questions = kwargs['questions']
        self.impostor_count = kwargs['impostor_count']
        self.game_map = kwargs.get('game_map', 'Game')
        self.players = []


class AUPlayer(object):
    NOT_VOTED = -2
    SKIPPED_VOTE = -1

    class Mask(object):
        DEAD = 1
        IMPOSTOR = 2
        VOTED_OUT = 4
        CALLED_VOTE = 8

    def __init__(self, *args, **kwargs):
        super(AUPlayer, self).__init__()
        self.name = kwargs.get('name', '')
        self.vx = 0.0
        self.vy = 0.0
        self.xs = ''
        self.ys = ''
        self.seq = 0
        self.col = kwargs.get('col', 'ff0000')
        self.mask = 0  # 1:DEAD, 2:IMPOSTOR, 4:VOTED_OUT, 8:CALLED_VOTE
        self.id =  int(kwargs.get('id', 0))
        self.voted_against = AUPlayer.NOT_VOTED

    def is_impostor(self):
        return (self.mask & AUPlayer.Mask.IMPOSTOR) == AUPlayer.Mask.IMPOSTOR

    def is_dead(self):
        return (self.mask & AUPlayer.Mask.DEAD) == AUPlayer.Mask.DEAD

    def is_voted_out(self):
        return (self.mask & AUPlayer.Mask.VOTED_OUT) == AUPlayer.Mask.VOTED_OUT

    def can_vote(self):
        return (self.mask & 5) == 0

class AUGames(object):

    games = dict()
