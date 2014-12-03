import sys
from cx_Freeze import setup, Executable

options = dict(include_files=["asciitable.json"], create_shared_zip='True', build_exe="executable/bin", excludes=["tcl"])
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(name= "ascii",
	version= "0.1",
	#options= {"build_exe": {"packages":["PIL"]}, "included_files":["asciitable.json"]},
	description= "Convert PNG and JPG images to ascii text",
	options= dict(build_exe=options),
	executables=[Executable("ascii.py"), Executable("ascii_gui.pyw", base=base)]
	)