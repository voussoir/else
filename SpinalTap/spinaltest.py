import spinal
import os

def catchexc(function, fargs=(), fkwargs={}, goalexc=''):
	'''
	Call function with *args fargs and **kwargs fkwargs,
	expecting to get an exception.
	If the raised exception has the description == goalexc,
	we got what we wanted. Else (or if no exception is raised)
	something is wrong.
	'''
	try:
		function(*fargs, **fkwargs)
		raise Exception("This should not have passed")
	except spinal.SpinalError as e:
		if e.description != goalexc:
			raise e

if __name__ == '__main__':
	os.chdir('testdata')
	spinal.os.remove('dstfile.txt')
	spinal.copyfile('srcfile.txt', 'dstfile.txt', callbackfunction=spinal.cb)
	spinal.copyfile('srcfile.txt', 'dstfile.txt', callbackfunction=spinal.cb)
	spinal.copyfile('srcfile.txt', 'dstfile_no_overwrite.txt', overwrite=False, callbackfunction=spinal.cb)
	spinal.copydir('.', '..\\t',precalcsize=True, callbackfile=spinal.cb)
	catchexc(spinal.copyfile, ('nonexist.txt', 'nonexist2.txt'), {'overwrite':False}, goalexc=spinal.EXC_SRCNOTFILE)
	print('You did it!')