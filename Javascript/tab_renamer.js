javascript:
function rename()
{
    var new_title = prompt("New page title:");
    if (new_title !== null)
    {
        document.title = new_title;
    }
}

rename();
undefined;
