from models import AUGames
from factory import *
import controllers

import asyncio
import json
import websockets


socket_map = dict()

async def broadcast_vote_state(game):
    print('broadcast vote state')
    votes_t = [{'who': p.id, 'whom': p.voted_against} for p in game.players]
    res = dict(
        typ='votes',
        started=int(1000 * game.voting_started.timestamp()),
        votes=votes_t
    )
    s = json.dumps(res)
    sends = [ws.send(s) for ws in socket_map[game.code]]
    asyncio.gather(*sends)

async def broadcast_state(game):
    if len(socket_map[game.code]) < 1:
        return
    g = controllers.full_game_as_dict(game)
    s = json.dumps({'typ':'u', 'data': g})
    for player in game.players:
        player.xs = ''
        player.ys = ''
    sends = [ws.send(s) for ws in socket_map[game.code]]
    asyncio.gather(*sends)


async def game_loop(game):
    print('starting game loop')
    while True:
        old_state = game.state
        controllers.process_game(game)
        await broadcast_state(game)


        if game.state == AUGame.State.GAME and old_state == AUGame.State.VOTING:
            asyncio.ensure_future(broadcast_vote_state(game))  # voting ended, broadcast result
        if game.state == AUGame.State.FINISHED:
            break  # game ended, exit the loop
        await asyncio.sleep(0.1)
    print('terminating game loop')

async def process_message(websocket, player, code, id, msg):
   # print(msg)
    cmd = msg.get('cmd')
    game = AUGames.games.get(code)
    if not game:
        return
    if player not in game.players:
        raise Exception("Player no longer in game") 
    if cmd == 'get-qs':
        #qs = json.dumps(game.questions)
        await websocket.send(json.dumps({'typ':'qs', 'questions': game.questions}))
    elif cmd == 'u':
        player.xs = player.xs.split(',') + msg["xs"].split(',')
        player.ys = player.ys.split(',') + msg["ys"].split(',')
        if len(player.xs) > 20:
            player.xs = player.xs[::2]
        if len(player.ys) > 20:
            player.ys = player.ys[::2]
        player.xs = ','.join(player.xs).strip(',')
        player.ys = ','.join(player.ys).strip(',')
        player.vx = msg["vx"]
        player.vy = msg["vy"]
        player.seq = msg["seq"]
    elif cmd == 'k':
        whom_id = msg['whom']
        for p in game.players:
            if p.id == int(whom_id):
                p.mask = p.mask | AUPlayer.Mask.DEAD
                print('killed')
    elif cmd == 'r':
        controllers.meet_to_vote(game, player)
        asyncio.ensure_future(broadcast_vote_state(game))
    elif cmd == 'p':
        amount = msg.get('amount')
        game.target += amount
    elif cmd == 'v':
        player.voted_against = int(msg.get('whom'))

async def hello(websocket, path):
    try:
        welcome = await websocket.recv()
        welcome = json.loads(welcome)
        intent = welcome.get('intent', None)
        if intent == 'get-games':
            codes = AUGames.games.keys()
            games = []
            for code in codes:
                game = AUGames.games.get(code)
                if game:
                    g = dict(
                        code=game.code,
                        impostor_count=game.impostor_count,
                        player_count=len(game.players),
                        state=game.state
                    )
                    games.append(g)
            await websocket.send(json.dumps({'typ': 'list', 'data': games}))
        elif intent == 'get-game':
            code = welcome.get('code')
            game = AUGames.games.get(code)
            if game:
                g = controllers.full_game_as_dict(game)
                g['impostor_count'] = game.impostor_count
                await websocket.send(json.dumps(g))
        elif intent == 'delete-game':
            code = welcome.get('code')
            game = AUGames.games.get(code)
            if game:
                game.state = AUGame.State.FINISHED
                del AUGames.games[code]
            await websocket.send(json.dumps({'res': 'ok'}))
        elif intent == 'create-game':
            code = welcome.get('code')
            question_set_id = welcome.get('question_set_id')
            impostor_count = int(welcome.get('impostor_count'))
            game_map = welcome.get('game_map')
            factory = AUGameFactory()
            if code in socket_map:
                print('socket map contains code already')
                for ws in socket_map[code]:
                    ws.close()
                game = AUGames.games.get(code)
                if game:
                    print('active game found. Request to terminate')
                    game.state = AUGame.State.FINISHED
            socket_map[code] = []
            game = factory.create_game(code, question_set_id, impostor_count, game_map)
            asyncio.ensure_future(game_loop(game))
            await websocket.send(json.dumps({'res': 'ok'}))
        elif intent == 'start-game':
            code = welcome.get('code')
            game = AUGames.games.get(code)
            if game:
                controllers.start_game(game)
            await websocket.send(json.dumps({'res': 'ok'}))
        elif intent == 'meet-to-vote':
            code = welcome.get('code')
            game = AUGames.games.get(code) 
            if game:
                controllers.meet_to_vote(game)
            await websocket.send(json.dumps({'res': 'ok'}))
        elif intent == 'continue-from-voting':
            code = welcome.get('code')
            game = AUGames.games.get(code) 
            if game:
                controllers.stop_voting(game)
            await websocket.send(json.dumps({'res': 'ok'}))
        elif intent == 'remove-player':
            code = welcome.get('code')
            id = int(welcome.get('id'))     
            print(f'remove-player {code} {id}')
            print(controllers.full_game_as_dict(AUGames.games[code]))
            AUGames.games[code].players[:] = [x for x in AUGames.games[code].players if x.id != id]
            print(controllers.full_game_as_dict(AUGames.games[code]))
            await websocket.send(json.dumps({'res': 'ok'}))
        elif intent == 'kill-player':
            # turn into ghost (remove with voting), but keep in game
            code = welcome.get('code')
            game = AUGames.games.get(code) 
            id = int(welcome.get('id'))
            print(f'kill-player {code} {id}')
            print(controllers.full_game_as_dict(game))
            for p in game.players:
                if p.id == id:
                    p.mask = p.mask | AUPlayer.Mask.VOTED_OUT
            await websocket.send(json.dumps({'res': 'ok'}))
        elif intent == 'join-game':
            code = welcome.get('code')
            id = welcome.get('id')
            try:
                name = welcome.get('name')
                factory = AUPlayerFactory()
                player = factory.create_player(name, id, code)
                if player:
                    print(f'adding socket to {code}')
                    socket_map[code].append(websocket)
                    game = AUGames.games.get(code)
                    async for message in websocket:
                        msg = json.loads(message)
                        await process_message(websocket, player, code, id, msg)
            
            finally:
                print(f'removing socket from {code}')
                if code in socket_map and websocket in socket_map[code]:
                    socket_map[code].remove(websocket)  
                if code is not None and id is not None and code in AUGames.games:
                    AUGames.games[code].players[:] = [x for x in AUGames.games[code].players if x.id != id]
    finally:
        pass


if __name__ == '__main__':
    print('starting server')
    start_server = websockets.serve(hello, "localhost", 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
  