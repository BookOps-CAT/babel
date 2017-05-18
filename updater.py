# updates Babel as frozen binaries
import tkinter as tk
import shutil
import os.path
import os
import sys


def run_update(directory):
    success = False
    if os.path.isfile('babel.exe'):
        try:
            os.remove('babel.exe')
            shutil.copy2(directory + 'babel.exe', 'babel.exe')
            success = True
        except Exception as e:
            error = str(e)

    root = tk.Tk()
    root.title("Babel update")
    root.columnconfigure(0, minsize=300)
    m = tk.StringVar()
    tk.Label(root, textvariable=m).grid(
        row=0, column=0, columnspan=4, sticky='snew', padx=10, pady=10)
    tk.Button(root, text='close',
              command=quit).grid(
        row=1, column=0, sticky='snew', padx=10, pady=10)
    if success:
        m.set('update sucessfull - please launch Babel')
    else:
        m.set('update failed!\n{}'.format(error))

    root.mainloop()

if __name__ == '__main__':
    run_update(sys.argv[1])
