import tkinter as tk
import os
import sys
import subprocess

# --- functions ---
# this is a function to get the user input from the text input box
def getInputBoxValue():
	userInput = tInput.get()
	return userInput


def runCommand():#"batchalign transcribe --lang=eng --whisper --num_speakers=2 --diarize .tmp_test/in .tmp_test/out"):
    #print("Hello World")
    cmd = [x for x in getInputBoxValue().split(' ') if x]
    if cmd:
        p = subprocess.Popen(cmd, bufsize=1,stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE, encoding='UTF-8')
        while True:
            out = p.stdout.read(1)
            if out == '' and p.poll() != None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()
        #p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #print(p.stdout.decode())
        #print(p.stderr.decode())

# def runCommand():
#     cmd = [x for x in getInputBoxValue().split(' ') if x]
#     p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1)
#     for line in iter(p.stdout.readline, b''):
#     print line,
# p.stdout.close()
# p.wait()
# --- classes ---

class Redirect():
    
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        self.widget.insert('end', text)
        self.widget.see('end') # autoscroll
        root.update_idletasks()

    def flush(self):
       root.update_idletasks()
    
    def __call__(self, *args, **kwargs):
        print(args, kwargs)
    
# --- main ---    
   
root = tk.Tk()

text = tk.Text(root)
text.pack()
tInput = tk.Entry(root)
tInput.pack()

button = tk.Button(root, text='TEST', command=runCommand)
button.pack()

old_stdout = sys.stdout    
sys.stdout = Redirect(text)

root.mainloop()

sys.stdout = old_stdout