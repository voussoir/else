function post_example(key, value, callback)
{
    var url = "/postexample";
    data = new FormData();
    data.append(key, value);
    return post(url, data, callback);    
}

function null_callback()
{
    return;
}

function post(url, data, callback)
{
    var request = new XMLHttpRequest();
    request.answer = null;
    request.onreadystatechange = function()
    {
        if (request.readyState == 4)
        {
            var text = request.responseText;
            if (callback != null)
            {
                console.log(text);
                callback(JSON.parse(text));
            }
        }
    };
    var asynchronous = true;
    request.open("POST", url, asynchronous);
    request.send(data);
}

function bind_box_to_button(box, button)
{
    box.onkeydown=function()
    {
        if (event.keyCode == 13)
        {
            button.click();
        }
    };
}
function entry_with_history_hook(box, button)
{
    //console.log(event.keyCode);
    if (box.entry_history === undefined)
    {box.entry_history = [];}
    if (box.entry_history_pos === undefined)
    {box.entry_history_pos = -1;}
    if (event.keyCode == 13)
    {
        /* Enter */
        box.entry_history.push(box.value);
        button.click();
        box.value = "";
    }
    else if (event.keyCode == 38)
    {

        /* Up arrow */
        if (box.entry_history.length == 0)
        {return}
        if (box.entry_history_pos == -1)
        {
            box.entry_history_pos = box.entry_history.length - 1;
        }
        else if (box.entry_history_pos > 0)
        {
            box.entry_history_pos -= 1;
        }
        box.value = box.entry_history[box.entry_history_pos];
    }
    else if (event.keyCode == 27)
    {
        box.value = "";
    }
    else
    {
        box.entry_history_pos = -1;
    }
}
