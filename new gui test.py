import tkinter as tk
from tkinter import ttk
from tkinter import * 
from tkwinterm.winterminal import Terminal


# this is the function called when the button is clicked
def addfile():
	print('clicked')


# this is the function called when the button is clicked
def removefile():
	print('clicked')


# this is a function which returns the selected combo box item
def getSelectedComboItem():
	return models.get()


# this is a function which returns the selected spin box value
def getSelectedSpinBoxValue():
	return numspeakersval.get()


# this is the function called when the button is clicked
def starttranscribe():
	print('clicked')


# This is a function which increases the progress bar value by the given increment amount
def makeProgress():
	pbar['value']=pbar['value'] + 1
	root.update_idletasks()


# this is a function to check the status of the checkbox (1 means checked, and 0 means unchecked)
def getCheckboxValue():
	checkedOrNot = openwhendone.get()
	return checkedOrNot


openwhendone = tk.IntVar()

root = Tk()
root.geometry('880x580')
root.configure(background='#F0F8FF')
root.title('Transcriber')
Button(root, text='add file', bg='#F0F8FF', font=('arial', 12, 'normal'), command=addfile).pack()
Button(root, text='rm file', bg='#F0F8FF', font=('arial', 12, 'normal'), command=removefile).pack()
models= ttk.Combobox(root, values=['model1', 'model2'], font=('arial', 12, 'normal'), width=10)
models.pack()
models.current(1)
Label(root, text='select model', bg='#F0F8FF', font=('arial', 12, 'normal')).pack()
Label(root, text='num speakers', bg='#F0F8FF', font=('arial', 12, 'normal')).pack()
numspeakersval= Spinbox(root, from_=1, to=50, font=('arial', 12, 'normal'), bg = '#F0F8FF', width=10)
numspeakersval.pack()
Button(root, text='transcribe', bg='#F0F8FF', font=('arial', 12, 'normal'), command=starttranscribe).pack()
Label(root, text='progress label', bg='#F0F8FF', font=('arial', 12, 'normal')).pack()

# This is the section of code which creates a checkbox
xbox_openwhendone=Checkbutton(root, text='open files when done?', variable=openwhendone, bg='#F0F8FF', font=('arial', 12, 'normal'))
xbox_openwhendone.pack()

terminal = Terminal(root, font_size=12, log_file='./.history')
terminal.pack()
root.mainloop()
