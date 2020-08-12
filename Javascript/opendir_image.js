javascript:
/*
This javascript bookmarklet takes anchors, images, and media elements from
the page, and displays them in a nice gallery. Designed for use on open
directory listings, but works in many places.
*/
var seen_urls = new Set();
var image_height = 200;
var video_height = 300;
var audio_width = 1000;
var IMAGE_TYPES = ["\\.jpg", "\\.jpeg", "\\.jpg", "\\.bmp", "\\.tiff", "\\.tif", "\\.bmp", "\\.gif", "\\.png", "reddituploads\.com", "\\.webp", "drscdn\\.500px\\.org\\/photo"].join("|");
var AUDIO_TYPES = ["\\.aac", "\\.flac", "\\.mp3", "\\.m4a", "\\.ogg", "\\.opus", "\\.wav"].join("|");
var VIDEO_TYPES = ["\\.mp4", "\\.m4v", "\\.mkv", "\\.webm", "\\.ogv"].join("|");
IMAGE_TYPES = new RegExp(IMAGE_TYPES, "i");
AUDIO_TYPES = new RegExp(AUDIO_TYPES, "i");
VIDEO_TYPES = new RegExp(VIDEO_TYPES, "i");

var has_started = false;

var CSS = `
body { background-color: #fff; }
audio, video { display: block; }
audio { width: ${audio_width}px; }
video { height: ${video_height}px; }
img { display: block; height: ${image_height}px; max-width: 100%; }
a { color: #000 !important; }
.control_panel { position: relative; background-color: #aaa; min-height: 10px; width: 100%; }
.workspace { background-color: #ddd; min-height: 10px; float: left; }
.arealabel { position:absolute; right: 0; bottom: 0; opacity: 0.8; background-color: #000; color: #fff; }
.delete_button { color: #d00; font-family: Arial; font-size: 11px; left: 0; position: absolute; top: 0; width: 25px; }
.ingest { position:absolute; right: 5px; top: 5px; height: 100%; width: 30% }
.ingestbox { position:relative; height: 75%; width:100%; box-sizing: border-box; }
.urldumpbox { overflow-y: scroll; height: 300px; width: 90% }
.load_button { position: absolute; top: 10%; width: 100%; height: 80%; word-wrap: break-word; }
.odi_anchor { display: block; }
.odi_image_div, .odi_media_div { display: inline-block; margin: 5px; float: left; position: relative; background-color: #aaa; }
.odi_image_div { min-width: ${image_height}px; }
`;

function apply_css()
{
    console.log("applying CSS");
    var css = document.createElement("style");
    css.innerHTML = CSS;
    document.head.appendChild(css);
}

function array_extend(a, b)
{
    /* Append all elements of b onto a */
    for (var i = 0; i < b.length; i += 1)
    {
        a.push(b[i]);
    }
}

function array_remove(a, item)
{
    /* Thanks peter olson http://stackoverflow.com/a/5767335 */
    for(var i = a.length - 1; i >= 0; i -= 1)
    {
        if(a[i].id === item.id)
        {
           a.splice(i, 1);
        }
    }
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

function clear_workspace()
{
    console.log("clearing workspace");
    workspace = document.getElementById("WORKSPACE");
    while (workspace.children.length > 0)
    {
        workspace.removeChild(workspace.children[0]);
    }
    return true;
}

function create_command_box(boxname, operation)
{
    var box = document.createElement("input");
    box.type = "text";
    box.id = boxname;
    box.onkeydown=function()
    {
        if (event.keyCode == 13)
        {
            operation(this.value);
        }
    };
    return box;
}

function create_command_button(label, operation)
{
    var button = document.createElement("button");
    button.innerHTML = label;
    button.onclick = operation;
    return button;
}

function create_command_box_button(boxname, label, operation)
{
    var box = create_command_box(boxname, operation);
    var button = create_command_button(label, function(){operation(box.value)});
    var div = document.createElement("div");
    div.appendChild(box);
    div.appendChild(button);
    div.box = box;
    div.button = button;
    return div;
}

function create_odi_div(url)
{

    var div = null;

    var mediatype;
    if (url["mediatype"] !== undefined)
    {
        mediatype = url["mediatype"];
        url = url["url"];
    }

    try
    {
        var basename = decodeURI(get_basename(url));
    }
    catch (exc)
    {
        console.error(exc);
        return;
    }

    var paramless_url = url.split("?")[0];
    if (!paramless_url)
    {
        return;
    }

    if (mediatype)
    {
        ;
    }
    else if (paramless_url.match(IMAGE_TYPES))
    {
        mediatype = "image";
    }
    else if (paramless_url.match(AUDIO_TYPES))
    {
        mediatype = "audio";
    }
    else if (paramless_url.match(VIDEO_TYPES))
    {
        mediatype = "video";
    }

    if (mediatype == null)
    {
        return;
    }
    if (mediatype === "image")
    {
        console.log("Creating image div for " + paramless_url);
        var div = document.createElement("div");
        div.id = generate_id(32);
        div.className = "odi_image_div";
        div.odi_type = "image";

        var a = document.createElement("a");
        a.className = "odi_anchor";
        a.odi_div = div;
        a.href = url;
        a.target = "_blank";

        var img = document.createElement("img");
        img.odi_div = div;
        img.anchor = a;
        img.border = 0;

        img.lazy_src = url;
        img.src = "";

        var arealabel = document.createElement("span");
        arealabel.className = "arealabel";
        arealabel.odi_div = div;
        arealabel.innerHTML = "0x0";
        img.arealabel = arealabel;

        var load_button = document.createElement("button");
        load_button.className = "load_button";
        load_button.odi_div = div;
        load_button.innerText = basename;
        load_button.onclick = function()
        {
            this.parentElement.removeChild(this);
            lazy_load_one(this.odi_div);
        };

        div.image = img;
        div.anchor = a;
        a.appendChild(img);
        a.appendChild(arealabel);
        div.appendChild(a);
        div.appendChild(load_button);
    }
    else
    {
        console.log("Creating " + mediatype + " div for " + paramless_url);

        var div = document.createElement("div");
        div.id = generate_id(32);
        div.className = "odi_media_div";
        div.odi_type = "media";
        div.mediatype = mediatype;

        var center = document.createElement("center");
        center.odi_div = div;

        var a = document.createElement("a");
        a.odi_div = div;
        a.innerText = basename;
        a.target = "_blank";
        a.style.display = "block";
        a.href = url;

        var media = document.createElement(mediatype);
        media.odi_div = div;
        media.controls = true;
        media.preload = "none";

        sources = get_alternate_sources(url);
        for (var sourceindex = 0; sourceindex < sources.length; sourceindex += 1)
        {
            source = document.createElement("source");
            source.src = sources[sourceindex];
            source.odi_div = div;
            media.appendChild(source);
        }

        div.media = media;
        div.anchor = a;
        center.appendChild(a);
        div.appendChild(center);
        div.appendChild(media);
    }

    if (div == null)
    {
        return null;
    }

    div.url = url;
    div.basename = basename;

    button = document.createElement("button");
    button.className = "delete_button";
    button.odi_div = div;
    button.innerHTML = "X";
    button.onclick = function()
    {
        delete_odi_div(this);
    };
    div.appendChild(button);
    return div;
}
function create_odi_divs(urls)
{
    console.log("Creating odi divs");
    image_divs = [];
    media_divs = [];
    odi_divs = [];
    for (var index = 0; index < urls.length; index += 1)
    {
        url = urls[index];
        if (!url)
        {
            continue;
        }
        var odi_div = create_odi_div(url);
        if (odi_div == null)
        {
            continue;
        }
        if (odi_div.odi_type == "image")
        {
            image_divs.push(odi_div);
        }
        else
        {
            media_divs.push(odi_div);
        }
    }
    array_extend(odi_divs, image_divs);
    array_extend(odi_divs, media_divs);
    return odi_divs;
}

function create_workspace()
{
    clear_page();
    apply_css();
    console.log("creating workspace");

    var control_panel = document.createElement("div");
    var workspace = document.createElement("div");

    var resizer = create_command_box_button("resizer", "resize", resize_images);
    var refilter = create_command_box_button("refilter", "remove regex", function(x){filter_re(x, true)});
    var rekeeper = create_command_box_button("rekeeper", "keep regex", function(x){filter_re(x, false)});
    var heightfilter = create_command_box_button("heightfilter", "min height", filter_height);
    var widthfilter = create_command_box_button("widthfilter", "min width", filter_width);
    var sorter = create_command_button("sort size", sort_size);
    var dumper = create_command_button("dump urls", dump_urls);
    var ingest_box = document.createElement("textarea");
    var ingest_button = create_command_button("ingest", ingest);
    var start_button = create_command_button("load all", function(){start();});

    start_button.style.display = "block";

    control_panel.id = "CONTROL_PANEL";
    control_panel.className = "control_panel";

    workspace.id = "WORKSPACE";
    workspace.className = "workspace";

    var ingest_div = document.createElement("div");
    ingest_div.id = "INGEST";
    ingest_div.className = "ingest";
    ingest_box.id = "ingestbox";
    ingest_box.className = "ingestbox";
    ingest_div.appendChild(ingest_box);
    ingest_div.appendChild(ingest_button);
    ingest_div.appendChild(ingest_box);
    ingest_div.appendChild(ingest_button);

    document.body.appendChild(control_panel);
    control_panel.appendChild(resizer);
    control_panel.appendChild(refilter);
    control_panel.appendChild(rekeeper);
    control_panel.appendChild(heightfilter);
    control_panel.appendChild(widthfilter);
    control_panel.appendChild(sorter);
    control_panel.appendChild(dumper);
    control_panel.appendChild(ingest_div);
    control_panel.appendChild(start_button);
    document.body.appendChild(workspace);
    console.log("finished workspace");
}

function delete_odi_div(element)
{
    if (element.odi_div != undefined)
    {
        element = element.odi_div;
    }
    if (element.media != undefined)
    {
        /* http://stackoverflow.com/questions/3258587/how-to-properly-unload-destroy-a-video-element */
        element.media.pause();
        element.media.src = "";
        element.media.load();
    }
    var parent = element.parentElement;
    parent.removeChild(element);
}

function dump_urls()
{
    var divs = get_odi_divs();
    var textbox = document.getElementById("url_dump_box");
    if (textbox == null)
    {
        textbox = document.createElement("textarea");
        textbox.className = "urldumpbox";
        textbox.id = "url_dump_box";
        workspace = document.getElementById("WORKSPACE");
        workspace.appendChild(textbox);
    }
    textbox.innerHTML = "";
    for (var index = 0; index < divs.length; index += 1)
    {
        textbox.innerHTML += divs[index].url + "\n";
    }
}

function fill_workspace(divs)
{
    console.log("filling workspace");

    workspace = document.getElementById("WORKSPACE");
    for (var index = 0; index < divs.length; index += 1)
    {
        workspace.appendChild(divs[index]);
    }
}

function filter_dimension(dimension, minimum)
{
    minimum = parseInt(minimum);
    images = Array.from(document.images);
    for (var i = 0; i < images.length; i += 1)
    {
        image = images[i];
        if (image[dimension] == 0)
            {continue;}
        if (image[dimension] < minimum)
        {
            delete_odi_div(image);
            continue;
        }
    }
}

function filter_height(minimum)
{
    filter_dimension('naturalHeight', minimum);
}

function filter_width(minimum)
{
    filter_dimension('naturalWidth', minimum);
}

function filter_re(pattern, do_delete)
{
    if (!pattern)
    {
        return;
    }
    pattern = new RegExp(pattern, "i");
    do_keep = !do_delete;
    console.log(pattern + " " + do_delete);
    odi_divs = get_odi_divs();
    for (var index = 0; index < odi_divs.length; index += 1)
    {
        div = odi_divs[index];
        match = div.url.match(pattern);
        if ((match && do_delete) || (!match && do_keep))
        {
            delete_odi_div(div);
        }
    }
}

function get_all_urls()
{
    console.log("Collecting urls");
    var urls = [];
    function include(source, attr, force_mediatype)
    {
        for (var index = 0; index < source.length; index += 1)
        {
            url = source[index][attr];
            if (url === undefined)
                {continue;}

            if (seen_urls.has(url))
                {continue;}
            console.log(url);
            if (url.indexOf("thumbs.redditmedia") != -1)
                {console.log("Rejecting reddit thumb"); continue;}
            if (url.indexOf("redditstatic.com/mailgray.png") != -1)
                {console.log("Rejecting reddit icons"); continue;}
            if (url.indexOf("redditstatic.com/start_chat.png") != -1)
                {console.log("Rejecting reddit icons"); continue;}
            if (url.indexOf("preview.redd.it/award_images") != -1)
                {console.log("Rejecting reddit awards"); continue;}
            if (url.indexOf("redditstatic.com/gold/awards") != -1)
                {console.log("Rejecting reddit awards"); continue;}
            if (url.indexOf("pixel.reddit") != -1 || url.indexOf("reddit.com/static/pixel") != -1)
                {console.log("Rejecting reddit pixel"); continue}
            if (url.indexOf("/thumb/") != -1)
                {console.log("Rejecting /thumb/"); continue;}
            if (url.indexOf("/loaders/") != -1)
                {console.log("Rejecting loader"); continue;}
            if (url.indexOf("memegen") != -1)
                {console.log("Rejecting retardation"); continue;}
            if (url.indexOf("4cdn") != -1 && url.indexOf("s.jpg") != -1)
                {console.log("Rejecting 4chan thumb"); continue;}

            sub_urls = normalize_url(url);
            if (sub_urls == null)
                {continue;}

            for (var url_index = 0; url_index < sub_urls.length; url_index += 1)
            {
                sub_url = sub_urls[url_index];
                if (seen_urls.has(sub_url))
                    {continue;}

                if (force_mediatype !== undefined)
                {
                    urls.push({"url": sub_url, "mediatype": force_mediatype});
                }
                else
                {
                    urls.push(sub_url);
                }
                seen_urls.add(sub_url);
            }
            seen_urls.add(url);
        }
    }

    var docs = [];
    docs.push(document);
    while (docs.length > 0)
    {
        var d = docs.pop();
        include(d.links, "href");
        include(d.images, "src", "image");
        include(d.getElementsByTagName("audio"), "src", "audio");
        include(d.getElementsByTagName("video"), "src", "video");
        include(d.getElementsByTagName("source"), "src");
    }
    console.log("collected " + urls.length + " urls.");
    return urls;
}

function get_alternate_sources(url)
{
    /*
    For sites that must try multiple resource urls, that logic
    may go here
    */
    return [url];
}

function get_basename(url)
{
    var basename = url.split("/");
    basename = basename[basename.length - 1];
    return basename;
}

function get_gfycat_video(id)
{
    console.log("Resolving gfycat " + id);
    var url = "https://api.gfycat.com/v1/gfycats/" + id;
    var request = new XMLHttpRequest();
    request.answer = null;
    request.onreadystatechange = function()
    {
        if (request.readyState == 4 && request.status == 200)
        {
            var text = request.responseText;
            var details = JSON.parse(text);
            request.answer = details["gfyItem"]["mp4Url"];
        }
    };
    var asynchronous = false;
    request.open("GET", url, asynchronous);
    request.send(null);
    return request.answer;
}

function get_lazy_divs()
{
    var divs = document.getElementsByTagName("div");
    var lazy_elements = [];
    for (index = 0; index < divs.length; index += 1)
    {
        var div = divs[index];
        if (div.image && div.image.lazy_src)
        {
            lazy_elements.push(div);
        }
    }
    return lazy_elements;
}

function get_odi_divs()
{
    var divs = document.getElementsByTagName("div");
    var odi_divs = [];
    for (index = 0; index < divs.length; index += 1)
    {
        var div = divs[index];
        if (div.id.indexOf("odi_") == -1)
        {
            continue;
        }
        odi_divs.push(div);
    }
    return odi_divs;
}

function generate_id(length)
{
    /* Thanks csharptest http://stackoverflow.com/a/1349426 */
    var text = [];
    var possible = "abcdefghijklmnopqrstuvwxyz";

    for(var i = 0; i < length; i += 1)
    {
        c = possible.charAt(Math.floor(Math.random() * possible.length));
        text.push(c);
    }
    return "odi_" + text.join("");
}

function ingest()
{
    /* Take the text from the INGEST box, and make odi divs from it */
    console.log("Ingesting");
    var odi_divs = get_odi_divs();
    var ingestbox = document.getElementById("ingestbox");
    var text = ingestbox.value;
    var urls = text.split("\n");
    for (var index = 0; index < urls.length; index += 1)
    {
        url = urls[index].trim();
        sub_urls = normalize_url(url);
        if (sub_urls == null)
            {continue;}

        for (var url_index = 0; url_index < sub_urls.length; url_index += 1)
        {
            sub_url = sub_urls[url_index];
            var odi_div = create_odi_div(sub_url);
            if (odi_div == null)
                {continue;}
            odi_divs.push(odi_div);
        }
    }
    ingestbox.value = "";
    clear_workspace();
    fill_workspace(odi_divs);
}

function lazy_load_all()
{
    console.log("Starting lazyload");
    lazies = get_lazy_divs();
    lazies.reverse();
    lazy_buttons = document.getElementsByClassName("load_button");
    for (var index = 0; index < lazy_buttons.length; index += 1)
    {
        lazy_buttons[index].parentElement.removeChild(lazy_buttons[index]);
    }
    while (lazies.length > 0)
    {
        var element = lazies.pop();
        if (element.image != undefined)
        {
            break;
        }
    }
    if (element == undefined)
    {
        return;
    }
    lazy_load_one(element, true);
    return;
}

function lazy_load_one(element, comeback)
{
    var image = element.image;
    if (!image.lazy_src)
    {
        return;
    }
    image.onload = function()
    {
        width = this.naturalWidth;
        height = this.naturalHeight;
        if (width == 161 && height == 81)
            {delete_odi_div(this);}
        this.arealabel.innerHTML = width + " x " + height;
        this.odi_div.style.minWidth = "0px";
        if (comeback){lazy_load_all()};
    };
    image.onerror = function()
    {
        delete_odi_div(this);
        if (comeback){lazy_load_all()};
    };
    /*console.log("Lazy loading " + element.lazy_src)*/
    image.src = image.lazy_src;
    image.lazy_src = null;
    return;
}

function _normalize_url(url)
{
    var protocol = window.location.protocol;
    if (protocol == "file:")
    {
        protocol = "http:";
    }
    url = url.replace("http:", protocol);
    url = url.replace("https:", protocol);

    console.log(url);
    url = url.replace("imgur.com/gallery/", "imgur.com/a/");

    if (url.indexOf("vidble") >= 0)
    {
        url = url.replace("_med", "");
        url = url.replace("_sqr", "");
    }

    else if (url.indexOf("imgur.com/a/") != -1)
    {
        var urls = [];
        var id = url.split("imgur.com/a/")[1];
        id = id.split("#")[0].split("?")[0];
        console.log("imgur album: " + id);
        var url = "https://api.imgur.com/3/album/" + id;
        var request = new XMLHttpRequest();
        request.onreadystatechange = function()
        {
            if (request.readyState == 4 && request.status == 200)
            {
                var text = request.responseText;
                var images = JSON.parse(request.responseText);
                images = images['data']['images'];
                for (var index = 0; index < images.length; index += 1)
                {
                    var image = images[index];
                    var image_url = image["mp4"] || image["link"];
                    if (!image_url){continue;}
                    image_url = normalize_url(image_url)[0];
                    console.log("+" + image_url);
                    urls.push(image_url);
                }
            }
        };
        var asynchronous = false;
        request.open("GET", url, asynchronous);
        request.setRequestHeader("Authorization", "Client-ID 1d8d9b36339e0e2");
        request.send(null);
        return urls;
    }

    else if (url.indexOf("imgur.com") >= 0)
    {
        var url_parts = url.split("/");
        var image_id = url_parts[url_parts.length - 1];
        var extension = ".jpg";
        if (image_id.indexOf(".") != -1)
        {
            image_id = image_id.split(".");
            extension = "." + image_id[1];
            image_id = image_id[0];
        }
        extension = extension.replace(".gifv", ".mp4");
        extension = extension.replace(".gif", ".mp4");

        if (image_id.length % 2 == 0)
        {
            image_id = image_id.split("");
            image_id[image_id.length - 1] = "";
            image_id = image_id.join("");
        }
        url = protocol + "//i.imgur.com/" + image_id + extension;
    }

    else if (url.indexOf("gfycat.com") >= 0)
    {
        var gfy_id = url.split("/");
        gfy_id = gfy_id[gfy_id.length - 1];
        gfy_id = gfy_id.split(".")[0];
        if (gfy_id.length > 0)
        {
            url = get_gfycat_video(gfy_id);
        }
    }

    else if (url.indexOf("commons.wikimedia.org/wiki/File:") >= 0)
    {
        url = url.replace("commons.wikimedia.org/wiki/File:", "commons.wikimedia.org/wiki/Special:FilePath/");
    }
    return [url];
}

function normalize_url(url)
{
    try
    {
        return _normalize_url(url);
    }
    catch (e)
    {
        return [];
    }
}

function resize_images(height)
{
    odi_divs = get_odi_divs();
    height = height.toString() + "px";
    for (var index = 0; index < odi_divs.length; index += 1)
    {
        var div = odi_divs[index];
        if (div.image)
        {
            div.image.style.height = height;
        }
        else if (div.media && div.mediatype == "video")
        {
            div.media.style.height = height;
        }
    }
}

function sort_size()
{
    console.log("sorting size");

    odi_divs = get_odi_divs();
    odi_divs.sort(sort_size_comparator);
    odi_divs.reverse();
    clear_workspace();
    fill_workspace(odi_divs);
}

function sort_size_comparator(div1, div2)
{
    if (div1.odi_type != "image" || div1.lazy_src)
    {
        return -1;
    }
    if (div2.odi_type != "image" || div2.lazy_src)
    {
        return 1;
    }
    pixels1 = div1.image.naturalHeight * div1.image.naturalWidth;
    pixels2 = div2.image.naturalHeight * div2.image.naturalWidth;
    if (pixels1 < pixels2)
        {return -1;}
    if (pixels1 > pixels2)
        {return 1;}
    return 0;
}

function start()
{
    lazy_load_all();
    has_started = true;
}

function main()
{
    var all_urls = get_all_urls();
    var divs = create_odi_divs(all_urls);
    create_workspace();
    fill_workspace(divs);
}

main();
undefined;
