javascript:
function give_event(player, index)
{
    /*
    This needs to be a function instead of inlined into the loop because `next`
    needs to be scoped, otherwise all of the players share the same next
    variable and it doesn't work.
    */
    var next = index + 1;
    players[index].addEventListener("ended", function(){ console.log(next); players[next].play(); });
}

players = document.getElementsByTagName("audio");
/*length - 1 because the final player doesn't need an event, only the second-last.*/
for (var index = 0; index < players.length - 1; index += 1)
{
    give_event(players[index], index);
}
players[0].play();
undefined;
