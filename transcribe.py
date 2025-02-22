import ffmpeg
import whisper
import subprocess
import os
from math import log10
from tkinter import END, HORIZONTAL, LEFT, SOLID, Button, Label, Listbox, StringVar, Toplevel, filedialog, messagebox, ttk, Tk
from datetime import datetime
import xlsxwriter
import traceback

TEMP_INP_FILES_DIR = "./.top_inp"
TEMP_OUT_FILES_DIR = "./.tmp_out"
os.mkdir(TEMP_INP_FILES_DIR)
os.mkdir(TEMP_OUT_FILES_DIR)

MODELS_DIRECTORY="./models" # where to save the models to
EXPECTED_RAW_FILE_TYPE='mp4' # placeholder, this might not be needed
BEST_FILE_TYPE_FOR_TRANSCRIPTION='wav' # placeholder, this might not be needed


class ToolTip(object):
    ACTIVE_TOOLTIPS = []
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        ToolTip.ACTIVE_TOOLTIPS.append(self)
    
    def __del__(self):
        ToolTip.ACTIVE_TOOLTIPS.remove(self)

    @staticmethod
    def hideall():
        for tt in ToolTip.ACTIVE_TOOLTIPS:
            try:
                tt.hidetip()
            except:
                pass
    
    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(tw, text=self.text, justify=LEFT,
                      background="#ffffe0", relief=SOLID, borderwidth=1,
                      font=("consolas", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

def convert_file_type(oldfile, toType=BEST_FILE_TYPE_FOR_TRANSCRIPTION, toDir=None):
	# extract base name, put to toDir when done
    name, ext = os.path.splitext(oldfile)
    n = 1
    if ext.lower() != toType.lower():
        out_name = f"{name}.{toType}"
        while os.path.exists(out_name):
            out_name = f"{name}_{n}.{toType}"
            n+=1
        ffmpeg.input(oldfile).output(out_name).run()
        return out_name
    return oldfile

def write2sheet(workbook: xlsxwriter.Workbook, sheetname, data, headers=None, conditionalRules=None, headerNotes=None):
    worksheet = workbook.add_worksheet(sheetname)
    if not headers:
        headers = data[0].keys()
    for cidx, header in enumerate(headers):
        worksheet.write(0, cidx, header)
    for ridx,row in enumerate(data, start=1):
        worksheet.write_row(ridx, 0, [row[x] for x in headers])
    if conditionalRules:
        for k in conditionalRules:
            if k in headers:
                cidx = headers.index(k)
                worksheet.conditional_format(1,cidx, len(data) + 1, cidx, conditionalRules[k])
            else:
                print(f'unable to apply conditional rule to {sheetname}::{k}')
    if headerNotes:
        for k in headerNotes:
            if k in headers:
                cidx = headers.index(k)
                worksheet.write_comment(0,cidx,headerNotes[k], {'font_name': 'Consolas', 'font_size': 11})
            else:
                print(f'unable to add header note to {sheetname}::{k}')
    worksheet.autofit()
    return worksheet

def transcribeDirectory(inpDir, outDir):
	if not inpDir or not os.path.exists(inpDir) or not os.path.isDir(inpDir):
		raise Error("Invalid directory")
	if not outDir or not os.path.exists(outDir) or not os.path.isDir(outDir):
		raise Error("Invalid directory")
	#@todo enable multiple languages 
	#@todo step 1
	try:
		result = subprocess.run(["batchalign", "transcribe", "--lang=en", inpDir, outDir])
	except:
		#@todo error popup
		pass
	#@todo step 2
	try:
		result = subprocess.run(["batchalign", "align", inpDir, outDir])
	except:
		#@todo error popup
		pass
	#@todo step 3
	try:
		result = subprocess.run(["batchalign", "morphotag", "--lang=en", inpDir, outDir])
	except:
		#@todo error popup
		pass
	#@todo what to do with the output? 
	# open clan?
	return

def transcribeFiles(filelist, options):
    # colors used for conditional formatting
    hex_colors = {
        'green': '#22ff1d',
        'yellow': '#ffff5c',
        'red': '#ff5c5c',
    }
    outputFiles = {}
    errors = {}

    GUI_progress_label.pack()
    GUI_progress_label.config(text="loading model...\nThis may take a moment on first use...\n:)")
    GUI_progress_bar.pack()
    GUI_progress_bar["value"] = 0
    
    pbarStepSize = 100 / (len(filelist) * 2)
    progressBarPadding = int(log10(3)+1)
    GUI_ROOT.update_idletasks()

    # load the model (will download if not local yet)
    model = whisper.load_model(options['model'] if 'model' in options else 'tiny.en', download_root=MODELS_DIRECTORY)
    
    # process files
    for idx,fn in enumerate(filelist, start=1):
        try:
            fname, ext = os.path.splitext(fn)
            
            # GUI_progress_label.config(text=f"#{idx:0>{progressBarPadding}}/{len(filelist):0>{progressBarPadding}}\n{fname}\nConverting file")
            # GUI_ROOT.update_idletasks()
            # if not fn.endswith(BEST_FILE_TYPE_FOR_TRANSCRIPTION):
            #     convert_file_type(fn)
            # GUI_progress_bar["value"] += pbarStepSize
            # GUI_ROOT.update_idletasks()

            GUI_progress_label.config(text=f"#{idx:0>{progressBarPadding}}/{len(filelist):0>{progressBarPadding}}\n{fname}\nTranscribing file")
            GUI_ROOT.update_idletasks()
            
            bySegment = []
            bySegmentWord = []
            transcript = model.transcribe(fn, word_timestamps=True)
            for seg in transcript['segments']:
                bySegment.append({'segmentID': seg['id'], 'start':seg['start'], 'end':seg['end'], 'text': seg['text'], 'confidence': seg['avg_logprob'], 'no_speech_prob': seg['no_speech_prob']})
                for word in seg['words']:
                    bySegmentWord.append({'segmentID': seg['id'], 'start':word['start'], 'end':word['end'], 'text':word['word'].strip(), 'confidence': word['probability']})
            
            GUI_progress_bar["value"] += pbarStepSize
            GUI_progress_label.config(text=f"#{idx:0>{progressBarPadding}}/{len(filelist):0>{progressBarPadding}}\n{fname}\nWriting output files...")
            GUI_ROOT.update_idletasks()
            
            n = 1
            outname = f"{fname}.xlsx"
            while os.path.exists(outname):
                outname = f"{fname}_{n}.xlsx"
                n+=1
            
            outputFiles[fn] = outputFiles.get(fn, []) + [outname]
            workbook = xlsxwriter.Workbook(outname)
            write2sheet(workbook, 'by segments', bySegment, headers=['segmentID', 'start', 'end', 'text', 'confidence', 'no_speech_prob'], conditionalRules={
                "confidence": {
                    'type': '3_color_scale',
                    'min_type': 'min', 'min_color': hex_colors['red'],
                    'mid_type': 'num', 'mid_value': -2, 'mid_color': hex_colors['yellow'],
                    'max_type': 'num', 'max_value': 0, 'max_color': hex_colors['green']
                },
                "no_speech_prob": {
                    'type': '2_color_scale',
                    'min_type': 'min', 'min_color': hex_colors['green'],
                    'max_type': 'max', 'max_color': hex_colors['red']
                }
            }, headerNotes = {
                "segmentID": f"segmentID\nThe segment ID.\n\nUnique to each segment.",
                "confidence": f"confidence\nThis column represents how confident the AI was with the transcription for the given row.\n\nThe higher the better.",
                "no_speech_prob": f"no_speech_prob\nThis column represents the probability of the segment to actually be halucinated and was just background noise or nobody talking.\n\nValues range from 0 to 1.\n\nThe lower the better.",
                "start": f"start\nTimestamp for start of segment.",
                "end": f"end\nTimestamp for end of segment.",
                "text": "text\nThe AI transcribed segment.",
            })
            write2sheet(workbook, 'by word', bySegmentWord, headers=['segmentID', 'start', 'end', 'text', 'confidence'], conditionalRules={
                "confidence": {
                    'type': '3_color_scale',
                    'min_type': 'num', 'min_value': 0, 'min_color': hex_colors['red'],
                    'mid_type': 'percentile', 'mid_value': 50, 'mid_color': hex_colors['yellow'],
                    'max_type': 'num', 'max_value': 1, 'max_color': hex_colors['green']
                },
            },
            headerNotes = {
                "segmentID": f"segmentID\nThis column links the given value to the 'by segments' sheet. A segmentID of X would correlate to the 'by segments' row that has the 'segmentID' value of X.",
                "confidence": f"confidence\nThis column represents how confident the AI was with the transcription for the given word.\n\nValues range from 0 to 1.\n\nThe higher the better.",
                "start": f"start\nTimestamp for start of word.",
                "end": f"end\nTimestamp for end of word.",
                "text": "text\nThe AI transcribed word.",
            })
            workbook.close()
            
            GUI_progress_bar["value"] += pbarStepSize
            GUI_ROOT.update_idletasks()
        except Exception as e:
            errors[fn] = traceback.format_exc()
        
    GUI_progress_bar.pack_forget()
    GUI_progress_label.pack_forget()
    return outputFiles, errors

def select_files():
    file_paths = filedialog.askopenfilenames(filetypes=[("Audio/Video", "*.mp4;*.mp3;*.avi;*.mov;*.mkv;*.fla;*.*")])
    GUI_listbox.delete(0, END)
    os.system(f"rm -rf {TEMP_INP_FILES_DIR}")
    for file in file_paths:
        GUI_listbox.insert(END, file)
        fname, ext = os.path.splitext(file)
        
        

def transcribeSelection_whisper():
    ToolTip.hideall()
    if GUI_listbox.size() == 0:
        messagebox.showwarning("Warning", "Please select at least one video file.")
        return

    selectedFiles = [GUI_listbox.get(i) for i in range(GUI_listbox.size())]
    options = {
        'model': GUI_model_var.get()
    }
    
    GUI_transcribe_button['state'] = 'disable'
    GUI_ROOT.update_idletasks()
    start = datetime.now()
    resulting_files = {}
    errors = {}
    try:
        resulting_files, errors = transcribeFiles(selectedFiles, options)
        GUI_ROOT.update_idletasks()
        end = datetime.now()
    except Exception as e:
        end = datetime.now()
        errlog=traceback.format_exc()
        print(errlog)
        messagebox.showerror("Failure", f"Sorry, something went wrong while transcribing the files! Check console logs!")
        GUI_transcribe_button['state'] = 'normal'
        GUI_ROOT.update_idletasks()
        return
    errmsg = ""
    if errors:
        errmsg = f"\nWARNING! Failed to process {len(errors)} files.\n\n"
        for k in errors:
            errmsg += f"In: {k}\n{errors[k]}\n\n\n"
    
    decsion = messagebox.askyesno('Transcripts complete', f'Transcription completed for {len(resulting_files)} files.\nProcess took: {str(end-start)}.\n\n{errmsg}The output files should be located in the same place as the original input file.\n\nOpen the {sum([len(resulting_files[x]) for x in resulting_files])} output files for the {len(selectedFiles)} input files now?')
    
    GUI_transcribe_button['state'] = 'normal'
    GUI_ROOT.update_idletasks()
    for k in resulting_files:
        for fn in resulting_files[k]:
            try:
                if decsion:
                    os.startfile(filepath=fn, operation='open')
                else:
                    print(f"{k} ==> {fn}")
            except Exception as e:
                messagebox.showerror("Failure", f"Sorry, something went wrong while tring to open\n{fn}!\n\n{traceback.format_exc()}")
    return

def transcribeSelection_batchalign():
    ToolTip.hideall()
    if GUI_listbox.size() == 0:
        messagebox.showwarning("Warning", "Please select at least one video file.")
        return

    selectedFiles = [GUI_listbox.get(i) for i in range(GUI_listbox.size())]
    options = {
        'model': GUI_model_var.get()
    }
    
    GUI_transcribe_button['state'] = 'disable'
    GUI_ROOT.update_idletasks()
    start = datetime.now()
    resulting_files = {}
    errors = {}
    try:
        results = transcribeFiles_batchalign(TEMP_INP_FILES_DIR, TEMP_OUT_FILES_DIR)
        GUI_ROOT.update_idletasks()
        end = datetime.now()
    except Exception as e:
        end = datetime.now()
        errlog=traceback.format_exc()
        print(errlog)
        messagebox.showerror("Failure", f"Sorry, something went wrong while transcribing the files! Check console logs!")
        GUI_transcribe_button['state'] = 'normal'
        GUI_ROOT.update_idletasks()
        return
    errmsg = ""
    if errors:
        errmsg = f"\nWARNING! Failed to process {len(errors)} files.\n\n"
        for k in errors:
            errmsg += f"In: {k}\n{errors[k]}\n\n\n"
    
    decsion = messagebox.askyesno('Transcripts complete', f'Transcription completed for {len(resulting_files)} files.\nProcess took: {str(end-start)}.\n\n{errmsg}The output files should be located in the same place as the original input file.\n\nOpen the {sum([len(resulting_files[x]) for x in resulting_files])} output files for the {len(selectedFiles)} input files now?')
    
    GUI_transcribe_button['state'] = 'normal'
    GUI_ROOT.update_idletasks()
    for k in resulting_files:
        for fn in resulting_files[k]:
            try:
                if decsion:
                    os.startfile(filepath=fn, operation='open')
                else:
                    print(f"{k} ==> {fn}")
            except Exception as e:
                messagebox.showerror("Failure", f"Sorry, something went wrong while tring to open\n{fn}!\n\n{traceback.format_exc()}")
    return
    
# GUI Setup
GUI_ROOT = Tk()
GUI_ROOT.title("Transcriber")
GUI_ROOT.geometry("600x430")

# File input portion

GUI_select_label = Label(GUI_ROOT, text="Select Video Files", font=("Arial", 12))
GUI_select_label.pack()
CreateToolTip(GUI_select_label, text="Select the files to be transcribed!")

GUI_select_files_button = Button(GUI_ROOT, text="Select Files", command=select_files)
GUI_select_files_button.pack(pady=5)
CreateToolTip(GUI_select_files_button, text = "Clear current selection and select multiple files to be transcribed. (Opens file selection window).")
GUI_listbox = Listbox(GUI_ROOT, width=90, height=10)
GUI_listbox.pack()


# Model selection dropdown
model_options = list(whisper._MODELS.keys())
GUI_model_var = StringVar(value=model_options[0])

GUI_model_dropdown_label = Label(GUI_ROOT, text="Select AI Model:")
GUI_model_dropdown_label.pack()
GUI_model_dropdown = ttk.Combobox(GUI_ROOT, textvariable=GUI_model_var, values=model_options)
GUI_model_dropdown.pack()
modelHelpText = """MODEL TYPES EXPLAINED
╔════════╦════════════╦══════════════╦══════════════╦══════════╦══════════╗
║  Size  ║ Parameters ║ English-only ║ Multilingual ║ Required ║ Relative ║
║        ║            ║    model     ║    model     ║   VRAM   ║  speed   ║
╠════════╬════════════╬══════════════╬══════════════╬══════════╬══════════╣
║  tiny  ║     39 M   ║   tiny.en    ║    tiny      ║   ~1 GB  ║   ~10x   ║
║  base  ║     74 M   ║   base.en    ║    base      ║   ~1 GB  ║    ~7x   ║
║  small ║    244 M   ║   small.en   ║    small     ║   ~2 GB  ║    ~4x   ║
║ medium ║    769 M   ║   medium.en  ║    medium    ║   ~5 GB  ║    ~2x   ║
║  large ║   1550 M   ║   N/A        ║    large     ║  ~10 GB  ║     1x   ║
║  turbo ║    809 M   ║   N/A        ║    turbo     ║   ~6 GB  ║    ~8x   ║
╚════════╩════════════╩══════════════╩══════════════╩══════════╩══════════╝

Reccomended to use any of the '[size].en' models.
"""
CreateToolTip(GUI_model_dropdown, modelHelpText)
CreateToolTip(GUI_model_dropdown_label, modelHelpText)

GUI_transcribe_button = Button(GUI_ROOT, text="Start Transcribe", command=transcribeSelection)
GUI_transcribe_button.pack(pady=5)
CreateToolTip(GUI_transcribe_button, text="Click here to start transcribing the files in the list!\nNote: If the transcription seems off, try running it again! Its possible the AI gets different results each time.")

# progress info and whatnot
GUI_progress_label = Label(GUI_ROOT, text="", font=("Arial", 10))
GUI_progress_bar = ttk.Progressbar(GUI_ROOT, orient=HORIZONTAL, length=400, mode='determinate')
GUI_progress_label.pack(pady=5)
GUI_progress_label.pack_forget()
GUI_progress_bar.pack(pady=5)
GUI_progress_bar.pack_forget()
CreateToolTip(GUI_progress_label, 'Please wait, I promise I am working...')
CreateToolTip(GUI_progress_bar, 'Please wait, I promise I am working...')

if __name__ == '__main__':
    GUI_ROOT.mainloop()