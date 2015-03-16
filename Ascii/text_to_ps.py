import os
import subprocess
import tkinter

filename_noext = input(']>> ')
filename_text = filename_noext.replace('.txt', '')
filename_text = filename_noext + '.txt'
filename_ghost = filename_noext + '_render.ps'



filea = open(filename_text, 'r')
lines = filea.read()
lines_split = lines.split('\n')
lines_height = len(lines_split)
lines_width = len(lines_split[0])
print('%d x %d' % (lines_width, lines_height))
lines_height *= 17
lines_width *= 7
filea.close()
t = tkinter.Tk()
c = tkinter.Canvas(t, width=lines_width, height=lines_height)
c.pack()
c.create_text(0, 0, text=lines, anchor="nw", font=("Courier New", 12))
print('Writing Postscript')
c.postscript(file=filename_ghost, width=lines_width, height=lines_height)
t.destroy()
print('Writing PNG')
subprocess.Popen('PNGCREATOR.bat', shell=True, cwd=os.getcwd())