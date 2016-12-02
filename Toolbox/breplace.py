import brename
import sys

replace_from = sys.argv[1]
replace_to = sys.argv[2]
command = 'x.replace("{f}", "{t}")'.format(f=replace_from, t=replace_to)
brename.brename(command)