import shlex

HEADER_TEXT = 'number name age address misc. "blank column?"'
BODY_TEXT = '''
4 "John Smith" 26 "123 north street"
17 "Jenny Smith" 8 "123 north street"
55 "Veronica Dove" 20 "456 west street"
77 "Austin Texas" 33 "789 south avenue"
89 "Mister Super Long Name" 123 "planet earth" "he's really old"
120 "Bill" "" "" "Deceased"
999 "Nine Nine" 999 "999 ninth boulevard" "favorite number is 9"
'''
BODY_TEXT = BODY_TEXT.strip()
DELIMITER = ' | '

output_text = ''
# Keep track of the longest entry in each column, to determine
# how wide we should make them.
# Also, look for numerical columns so we can right-justify them.
header = shlex.split(HEADER_TEXT)
column_widths = {index:len(item) for (index, item) in enumerate(header)}
column_types = {}
document_lines = [shlex.split(line) for line in BODY_TEXT.splitlines()]
for line in document_lines:
    for (index, word) in enumerate(line):
        current_width = column_widths.get(index, 0)
        column_widths[index] = max(len(word), current_width)

        try:
            float(word)
        except ValueError:
            # It only takes one failure to make the whole column
            # string type.
            if word != "":
                column_types[index] = 's'

# Move the dictionary into a list where the index is the column
# number, and the value is how wide it should be.
column_widths = list(column_widths.items())
column_widths.sort(key=lambda x: x[0])
column_widths = [x[1] for x in column_widths]

# Format column widths into a string which will become the basis
# for each row.
column_format = '{:%s%d%s}'
column_formats = []
for (index, width) in enumerate(column_widths):
    formtype = column_types.get(index, 'g')
    justify = '<' if formtype == 's' else '>'
    form = column_format % (justify, width, formtype)
    column_formats.append(form)

# Format the header.
column_count = len(column_widths)
diff = len(header) - column_count
if diff > 0:
    # We have labels for columns that were empty.
    column_count = len(header)
else:
    diff *= -1
header += [''] * diff

for (index, label) in enumerate(header):
    form = '{:<%ds}' % column_widths[index]
    header[index] = form.format(label)
header = DELIMITER.join(header)
output_text += header + '\n'

# Format the rows.
for (rowindex, line) in enumerate(document_lines):
    # Does this row need any blank columns?
    diff = column_count - len(line)
    if diff > 0:
        line += [''] * diff
        document_lines[rowindex] = line

    # Format and replace it into the list.
    for (columnindex, word) in enumerate(line):
        if word == '':
            line[columnindex] = ' ' * column_widths[columnindex]
        else:
            if column_types.get(columnindex, 'g') == 'g':
                word = float(word)
            else:
                word = str(word)
            line[columnindex] = column_formats[columnindex].format(word)

document_lines = [DELIMITER.join(line) for line in document_lines]
document_lines = '\n'.join(document_lines)
output_text += document_lines
print(output_text)

'''
number | name                   | age | address             | misc.                | blank column?
     4 | John Smith             |  26 | 123 north street    |                      |              
    17 | Jenny Smith            |   8 | 123 north street    |                      |              
    55 | Veronica Dove          |  20 | 456 west street     |                      |              
    77 | Austin Texas           |  33 | 789 south avenue    |                      |              
    89 | Mister Super Long Name | 123 | planet earth        | he's really old      |              
   120 | Bill                   |     |                     | Deceased             |              
   999 | Nine Nine              | 999 | 999 ninth boulevard | favorite number is 9 |              
'''