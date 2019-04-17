import os

paths = os.getenv('PATH').split(';')
paths = [p for p in paths if os.path.exists(p)]

extensions = os.getenv('PATHEXT').split(';')
extensions = [e.lower() for e in extensions]
print('Extensions according to PATHEXT:', extensions)

for path in paths:
    print(path)
    files = os.listdir(path)
    files = [f for f in files if any(f.lower().endswith(e) for e in extensions)]
    files = ['    ' + f for f in files]
    print('\n'.join(files))
