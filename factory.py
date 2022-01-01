from models import AUGame, AUPlayer, AUGames

import json
import random
import re

QUESTION_PATH = "questions/y9mich.json"

class AUGameFactory(object):

    def create_game(self, code, question_set_id, impostor_count, game_map = 'Game') -> AUGame:
        #if code in AUGames.games:
        #    return None
        questions = self._fetch_questions(question_set_id)
        new_game = AUGame(code=code, questions=questions, impostor_count=impostor_count, game_map=game_map)
        AUGames.games[code] = new_game
        return new_game

    def _fetch_questions(self, question_set_id):
        """
        # normally questions are fetched from the database through Django.
        # here, for simplicity, they are fetched from a Json file instead
        question_items = QuestionItem.objects.filter(question_set__id=question_set_id).order_by('order').select_related('question').all()
        questions = []
        for qi in question_items:
            dbquestion = qi.question
            question = dict(
                type=dbquestion.typ,
                Question=self._textify(dbquestion.question),
            )
            if dbquestion.typ == 'mc':
                question['Options'] = json.loads(dbquestion.options)
                question['CorrectOption'] = dbquestion.correct_option
            elif dbquestion.typ == 'bf':
                question['Answer'] = json.loads(dbquestion.options)[0]
                question['Answers'] = json.loads(dbquestion.options)

            questions.append(question)
        """
        with open(QUESTION_PATH, "r") as f:
            questions = json.loads(f.read())
        return questions

    """
    def _textify(self, html):
        # Remove html tags and continuous whitespaces 
        text_only = re.sub('[ \t]+', ' ', strip_tags(html))
        text_only = text_only.replace("&nbsp;", " ")
        # Strip single spaces in the beginning of each line
        return text_only.replace('\n ', '\n').strip()
    """

class AUPlayerFactory(object):

    def create_player(self, name, id, game_id):
        if game_id not in AUGames.games:
            return None
        game = AUGames.games[game_id]
        pids = [p.id for p in game.players]
        print(pids)
        if id in pids:
            return None

        cols = set([p.col for p in game.players])
        available_cols = AUGame.PLAYER_COLS - cols
        if len(available_cols) < 1:
            return None

        col = random.sample(list(available_cols), 1)[0]

        if len(name) > 16:
            name = name[0:16]

        player = AUPlayer(name=name, col=col, id=id)
        game.players.append(player)
        return player
