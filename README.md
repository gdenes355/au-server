# au-server
This is a public clone of the Among Us server code running on https://gdenes.com/.

## Structure of the repository
The following Python files all live in the root folder:
* `au_server.py`: entry point; **run this to start the server**
* `controllers.py`: some common game control logic for the server
* `factory.py`: factories for games and player objects
* `models.py`: model definition for the game and the player

The question set used by the server is normally fetched from a database through Django. In this repository (for simplicity), the questions are instead fetched from the questions folder(currently `y9mich.json`, but could be customised in `factory.py`).

There are some manual tests available to verify that the server behaves correctly. These are all in the `manual-tests` folder, with a readme file to explain the testing process.

## Getting started
Make sure you have the correct packages from `requirements.txt` installed. If you have Pip, you can just run 
```
pip install -r requirements.txt
```
To start the server, just run 
```
python au_server.py
```



## Game state
A game goes through a number of states in its lifecycle
* All games (when created) start with state `Lobby`, waiting for enough players to join
* When a game starts, it transitions into `Game`
* In the course of the game, it can transition between `Voting` and `Game` a number of times, based on reported bodies and voting.
* Once a game finishes, its state changes to `Finished`

## Server overview
This server uses [WebSocket](https://en.wikipedia.org/wiki/WebSocket) to communicate with the players and the admin site.
The server listens to websocket requets on port `8765`.
The initial command should always contain a JSON with an `intent` field. E.g.
```json
{"intent": "create-game", "code": "123", "question_set_id": 1, "impostor_count": 1, "game_map": "Game"}
```

### Admin intents
There are a number of admin-related intents:

* Request a list of current games: `{intent: "get-games"}`
* Request details of a game using its join code. E.g. 123 `{"intent":"get-game","code":"123"}`
* Delete a game using its join code. E.g. 123
`{"intent":"delete-game","code":"123"}`
* Create a game with a code (e.g. 123) and impostor count (e.g. 1)
`{intent: "create-game", code: "123", question_set_id: 1, impostor_count: 1, game_map: "Game"}`. Keep `question_set_id` and `game_map` as in the example.
* Start a game (move from lobby to game) using its join code. E.g. 123 `{"intent":"start-game","code":"123"}`
* Call an emergency meeting in a game using its join code. E.g. 123 `{"intent":"meet-to-vote","code":"123"}`
* Move on from voting in a game using its join code. E.g. 123 `{"intent":"continue-from-voting","code":"123"}`
* Kick a player by id (e.g. 1) out from a game (e.g. 123) `{"intent":"remove-player","code":"123","id":1}`
* Turn a player by id (e.g. 1) into a ghost in a game (e.g. 123) `{"intent":"kill-player","code":"123","id":1}`

*note that these are currently not protected by auth*

### Client intents
The Unity Player always uses a `join-game` intent which specifies the game to join (code), the player's name, as well as an integer id which should be the unique identifier of this player for all future communication.

```json
{ 
    "intent": "join-game", 
    "code": "<code e.g. 123>", 
    "name": "<player name; string>", 
    "id": <integer player id, e.g. 1> 
}
```


Once a player joins, it automatically receives the updated game state approx. 10 times a second. This is done by `broadcast_state` in `au_server.py`.

While a player is in the game, it can also push through commands to the server. For these messages, there is no `intent` field (as the connection is still active, the client does not need to open a new channel). However, each command should be a well-formatted json with a required `cmd` field.
E.g. a vote command might look like:
```json
{"cmd":"v","whom":2}
```
Note that the message does not need to identify who casts the vote (as the same WebSocket channel is used, this is already known).

Here is a list of all the available commands:
* Get the question set for the game: `{"cmd": "get-qs"}`
* Kill another player by id. E.g. kill player id 2: `{"cmd":"k","whom":2}`
* Report a body which triggers a voting state: `{"cmd":"r"}`
* Vote against a player. E.g. player id 2: `{"cmd":"v","whom":2}`. 
This can be also used to skip a vote by setting the player id to `-1`:  `{"cmd":"v","whom":-1}`
* Score points from solving tasks: `{"cmd":"p","amount":-1}`. 

And finally, the following command is issued multiple times a second to update the server with the latest player locations. E.g.
```json
{
    "cmd":"u",
    "xs":"-0.41,-0.51,-0.61,-0.71,-0.81",
    "ys":"0.30,0.30,0.30,0.30,0.30",
    "vx":-5.0,
    "vy":0.0,
    "seq":246
}
```
In this message, the `xs` and `ys` list the coordinates of the player since the last update message (allowing other clients to play these back smoothly). Normally there are 5 locations for each update. `vx` and `vy` show the final speed vector of the player so other clients can show the correct orientation of the player's avatar. `seq` is the sequence number to avoid out-of-order messages (obsolete with websockets).


*note that the server does little to no validation on these commands; the assumption is an honest client program which doesn't try to violate the rules of the game*



