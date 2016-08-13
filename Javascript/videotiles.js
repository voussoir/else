javascript:

CSS = ""
+ "* {margin: 0; padding: 0}"
+ "html {height: 95%}"
+ "body {height: 100%; background-color: #000}"
+ "div { display:inline-block; }"
+ "video {"
+ "  min-width: 100%;"
+ "  min-height: 100%;"
+ "  max-width: 100%;"
+ "  max-height: 100%;"
+ "  overflow: hidden;"
+ "}"
;

var VIDEO_TYPES = ["\\.mp4", "\\.m4v", "\\.webm", "\\.ogv"].join("|");

function apply_css()
{
    console.log("applying CSS");
    var css = document.createElement("style");
    css.innerHTML = CSS;
    document.head.appendChild(css);
}

function get_media_links()
{
    var anchors = document.getElementsByTagName("a");
    var media_links = [];
    for (var index = 0; index < anchors.length; index += 1)
    {
        var anchor = anchors[index];
        if (anchor.href.match(VIDEO_TYPES))
        {
            media_links.push(anchor.href);
        }
    }
    return media_links;
}

function clear_page()
{
    /* Remove EVERYTHING */
    console.log("clearing page");
    document.removeChild(document.documentElement);

    var html = document.createElement("html");
    document.appendChild(html);

    var head = document.createElement("head");
    html.appendChild(head);

    var body = document.createElement("body");
    html.appendChild(body);

    document.documentElement = html;
    return true;
}

function create_video_players(width, height)
{
    var css_width = (100 / width).toString() + "%";
    var css_height = (100 / height).toString() + "%";
    console.log(css_width);

    var players = [];
    for (var index = 0; index < width * height; index += 1)
    {
        var player_holder = document.createElement("div");
        var player = document.createElement("video");
        player_holder.style.width = css_width;
        player_holder.style.height = css_height;
        player.holder = player_holder;
        players.push(player);
        player_holder.appendChild(player);
        document.body.appendChild(player_holder);
    }
    return players;
}

function swap_source(player, source_list)
{
    var index = Math.floor(Math.random() * source_list.length);
    var href = source_list[index];
    player.pause();
    player.src = href;
    player.load();
    player.play();
}

function main()
{
    var WIDTH = 3;
    var HEIGHT = 3;
    var MEDIAS = get_media_links();

    clear_page();
    apply_css();

    var PLAYERS = create_video_players(WIDTH, HEIGHT);
    function ended_callback()
    {
        swap_source(this, MEDIAS);
    }
    for (var index = 0; index < PLAYERS.length; index += 1)
    {
        var player = PLAYERS[index];
        player.addEventListener("ended", ended_callback);
        swap_source(player, MEDIAS);
    }
}

main();