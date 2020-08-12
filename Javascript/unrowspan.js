javascript:
function unrowspan(tbody)
{
    var rows = tbody.children;
    for (var row_index = 0; row_index < rows.length; row_index += 1)
    {
        var row = rows[row_index];
        var columns = row.children;
        for (var column_index = 0; column_index < columns.length; column_index += 1)
        {
            var column = columns[column_index];
            var span = column.rowSpan;
            column.rowSpan = 1;
            for (var i = 1; i < span; i += 1)
            {
                var before = rows[row_index+i].children[column_index];
                console.log("Put " + column.innerText + " before " + column_index + " - " + before.innerText);
                rows[row_index+i].insertBefore(column.cloneNode(true), before);
            }
        }
    }
}

var tbodies = Array.from(document.getElementsByTagName("tbody"));
tbodies.forEach(unrowspan);
undefined;
