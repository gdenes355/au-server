# Manual testing

The behaviour of the localhost server can be verified using a handful of html files against `localhost:8765`.


The Python server uses websockets to communicate with the clients. In the manual testing framework, these websocket requests are issued from JavaScript, mostly automatically when the HTML file is opened (except for `test-local-e2e.html` where there are buttons to trigger the actions).

The output of the websocket communiation is logged in the console, so it's worth opening the inspect tool -> console (using `Ctrl` `Shift` `I` or `F12`).


**When testing, make sure you launch the localhost server first (instructions in the root)**

## Getting started

In a typical game setup, the following steps are performed first:
1. game is created
2. players join
3. game starts

To mimic this, follow the steps below, while keeping the browser tabs open. Remember that websocket responses are logged in the console:
1. open  `test-create123.html`; this will create a game with code `123`, single impostor
2. open `test-create-p-1.html` which will add player 1
3. open `test-create-p-2.html` which will add player 2
4. open `test-create-p-3.html` which will add player 3
6. open `test-start.html` to start the game.
7. close the tabs where player 1 was created. This should result in the game ending.

After any step, you can open `test-details.html` to verify the game state


## End to end
`test-local-e2e.html` simulates a plausible game sequence with 3 players, where the players meet to vote (emergency meeting), then decide to vote player 2 out. This should end the game. After any step, you can open `test-details.html` to verify the game state.

## Other commands
* `test-kill-p-1.html`: kills player 1
* `test-remove-p-1.html`: removes player 1 (does not turn into ghost, kicked out of game)
* `test-vote.html`: meet to vote
* `test-continue.html`: continue the game from voting, without anyone being voted out




