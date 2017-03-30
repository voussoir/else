import argparse
import sys
import os

from voussoirkit import bytestring
from voussoirkit import treeclass

HTML_TREE_HEAD = '''
<head>
<meta charset="UTF-8">

<script type="text/javascript">
function collapse(div, force)
{
    if (force !== "block" && div.style.display != "none")
    {
        div.style.display = "none";
    }
    else
    {
        div.style.display = "block";
    }
}
</script>

<style>
*
{
    font-family: Consolas;
}

.directory_even, .directory_odd
{
    padding: 10px;
    padding-left: 15px;
    margin-bottom: 10px;
    border: 1px solid #000;
    box-shadow: 1px 1px 2px 0px rgba(0,0,0,0.3);
}

.directory_even
{
    background-color: #fff;
}

.directory_odd
{
    background-color: #eee;
}
</style>
</head>
<script type="text/javascript">
function open_all()
{
    var divs = document.getElementsByTagName("div");
    for (var index = 0; index < divs.length; index += 1)
    {
        collapse(divs[index], "block");
    }
}
</script>
<button onclick="open_all()">Expand all</button>
'''

HTML_FORMAT_DIRECTORY = '''
<div class="buttonbox">
<button onclick="collapse(this.parentElement.nextElementSibling)">{name} ({size})</button>
{directory_anchor}
</div>
<div class="{css}" style="display:none">
'''.replace('\n', '')

HTML_FORMAT_FILE = '<a href="{url}">{name} ({size})</a><br>'


class PathTree(treeclass.Tree):
    def __init__(
            self,
            path,
            display_name=None,
            item_type=None,
            size=None,
            **kwargs,
        ):
        self.path = normalize_slash(path)
        if display_name is None:
            self.display_name = self.path.split(os.sep)[-1]
        else:
            self.display_name = display_name
        kwargs['identifier'] = self.display_name
        super(PathTree, self).__init__(**kwargs)
        self.size = size
        self.item_type = item_type

def normalize_slash(path):
    path = path.replace('/', '\\')
    path = path.rstrip(os.sep)
    return path

def from_paths(path_datas, root_name):
    all_datas = []
    for data in path_datas:
        if isinstance(data, str):
            data = {'path': data}
        elif isinstance(data, dict):
            pass
        else:
            raise TypeError(data)
        data['parts'] = data['path'].split(os.sep)
        all_datas.append(data)

    #path_parts = path_parts.split('\\')
    #item = {'url': url, 'size': size, 'path_parts': path_parts}
    #all_items.append(item)
    #scheme = url_split(all_items[0]['url'])['scheme']

    all_datas.sort(key=lambda x: x['path'])

    tree_root = PathTree(root_name, item_type='directory')
    tree_root.unsorted_children = all_datas
    node_queue = set()
    node_queue.add(tree_root)

    # In this process, URLs are divided up into their nodes one directory layer at a time.
    # The root has all URLs as its `unsorted_children` attribute, and creates
    # nodes for each of the top-level directories.
    # Those nodes receive all subdirectories, and repeat.
    while len(node_queue) > 0:
        node = node_queue.pop()
        for new_child_data in node.unsorted_children:
            # Create a new node for the subdirectory, which is path_parts[0]
            # The rest of the child path is assigned to that node to be further divided.
            # By popping, we modify the path_parts in place so that the next cycle
            # only deals with the remaining subpath.
            path_parts = new_child_data['parts']
            child_identifier = path_parts.pop(0)
            
            child = node.children.get(child_identifier)
            if not child:
                child = PathTree(child_identifier)
                child.unsorted_children = []
                node.add_child(child)

            if len(path_parts) > 0:
                child.item_type = 'directory'
                child.unsorted_children.append(new_child_data)
            else:
                child.item_type = 'file'
                child.size = new_child_data.get('size')
                child.data = new_child_data.get('data')
            node_queue.add(child)

        if node.parent is not None and node.parent != tree_root:
            node.path = node.parent.path + os.sep + node.path

        del node.unsorted_children
    return tree_root

def recursive_get_size(node):
    '''
    Calculate the size of the Directory nodes by summing the sizes of all children.
    Modifies the nodes in-place.
    '''
    return_value = {
        'size': 0,
        'unmeasured': 0,
    }
    if node.item_type == 'file':
        if node.size is None:
            return_value['unmeasured'] = 1
        # = instead of += because if the node.size is None, we want to propogate
        # that to the caller, rather than normalizing it to 0.
        return_value['size'] = node.size

    else:
        for child in node.list_children():
            child_details = recursive_get_size(child)
            return_value['size'] += child_details['size'] or 0
            return_value['unmeasured'] += child_details['unmeasured']
        node.size = return_value['size']

    return return_value

def recursive_print_node(node, depth=0, use_html=False, header=None, footer=None):
    '''
    Given a tree node (presumably the root), print it and all of its children.

    use_html:
        Generate a neat HTML page instead of plain text.
    header:
        This text goes at the top of the file, or just below the <body> tag.
    footer:
        This text goes at the end of the file, or just above the </body> tag.
    '''
    if depth == 0:
        if use_html:
            yield '<!DOCTYPE html>\n<html>'
            yield HTML_TREE_HEAD
            yield '<body>'
        if header is not None:
            yield header

    size = node.size
    if size is None:
        size = '???'
    else:
        size = bytestring.bytestring(size)

    if use_html:
        css_class = 'directory_even' if depth % 2 == 0 else 'directory_odd'
        if node.item_type == 'directory':
            directory_url = node.path
            directory_anchor = '<a href="{url}">&rightarrow;</a>' if directory_url else ''
            directory_anchor = directory_anchor.format(url=directory_url)
            line = HTML_FORMAT_DIRECTORY.format(
                css=css_class,
                directory_anchor=directory_anchor,
                name=node.display_name,
                size=size,
            )
        else:
            line = HTML_FORMAT_FILE.format(
                name=node.display_name,
                size=size,
                url=node.path,
            )
    else:
        line = '{space}{bar}{name} : ({size})'
        line = line.format(
            space='|   ' * (depth-1),
            bar='|---' if depth > 0 else '',
            name=node.display_name,
            size=size
        )
    yield line

    # Sort by type (directories first) then subsort by lowercase path
    customsort = lambda node: (
        node.item_type == 'file',
        node.path.lower(),
    )

    for child in node.list_children(customsort=customsort):
        yield from recursive_print_node(child, depth=depth+1, use_html=use_html)

    if node.item_type == 'directory':
        if use_html:
            # Close the directory div
            yield '</div>'
        else:
            # This helps put some space between sibling directories
            yield '|   ' * (depth)

    if depth == 0:
        if footer is not None:
            yield footer
        if use_html:
            yield '</body>\n</html>'



def pathtree_argparse(args):
    from voussoirkit import safeprint
    from voussoirkit import spinal
    paths = spinal.walk_generator()
    paths = [{'path': path.absolute_path, 'size': path.size} for path in paths]
    tree = from_paths(paths, '.')
    recursive_get_size(tree)

    if args.output_file:
        output_file = open(args.output_file, 'w', encoding='utf-8')
    else:
        output_file = None

    for line in recursive_print_node(tree, use_html=args.use_html):
        if output_file:
            print(line, file=output_file)
        else:
            safeprint.safeprint(line)

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('output_file', nargs='?', default=None)
    parser.add_argument('--html', dest='use_html', action='store_true')
    parser.set_defaults(func=pathtree_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
