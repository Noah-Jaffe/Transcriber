import os
from time import sleep, time
import tkinter as tk
from tkinter import BOTH, CENTER, END, LEFT, SOLID, TOP, X, Button, IntVar, Label, Spinbox, StringVar, Tk, Toplevel, filedialog, Frame, messagebox
from tkinter.font import BOLD, ITALIC, NORMAL
# from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Combobox
from types import FunctionType
from typing import Dict, List
import whisper
import traceback
# import batchalign as ba
import sys
import subprocess
import pathlib
import json
# import logging
class COLOR_THEME:
    IN_PROGRESS = "lightyellow"
    LOADED = "aqua"
    MAIN_WINDOW = "lightblue"
    FAILED = "lightred"
    COMPLETED = "green"
    BUTTON = "pink"

def get_model_list() -> List[str]:
    """
    Returns:
        List[str]: List of available model names
    """
    ret = list(whisper._MODELS.keys())
    return ret

def todo_get_available_langs() -> Dict[str,str]:
    """Returns:
        Dict[str,str]: a dict where keys are full names and values are the short of languages available for transcription.
    """
    ret = {}
    ret["English"] = "eng"
    return ret

def todo_get_ffmpeg_supported_file_types() -> List[str]:
    """
    Returns:
        List[str]: list of supported file types
    """
    ret = []
    # temp solution: add the known file types
    ret += ['mp4', 'mp3', 'avi', 'wav', 'mov', 'fla', 'ogg', 'webm', '3gp', '3g2', 'mj2', 'm4v', 'dv', 'avr', 'afc']
    # @TODO parse output from 'ffmpeg -demuxers -hide_banner'
    return ret

LABEL_FONT = ("Arial", 12, BOLD)
BUTTON_FONT = ("Arial", 12, NORMAL)
FILE_NAME_FONT = ("Consolas", 10, NORMAL)
TOOLTIP_FONT = ("Consolas", 8, NORMAL)


# MODELS_DIRECTORY="./models" # where to save the models to
# class CustomStdOut:
#     def __init__(self, tkScrolledText):
#         self.buffer = ""
#         self.tkScrolledText = tkScrolledText
#     def write(self, message):
#         self.buffer += str(message)
#     def flush(self):
#         # Define what happens on flush (e.g., print to a file, network, etc.)
#         self.tkScrolledText.config(state=NORMAL)
#         self.tkScrolledText.insert(END, f"{self.buffer}\n")
#         self.tkScrolledText.see(END)
#         self.tkScrolledText.config(state="disabled")
#         self.buffer = ""

#     def __getattr__(self, attr):
#         # Delegate other attributes/methods to the original stdout
#         return getattr(sys.__stdout__, attr)

class MainGUI:
    def __init__(self, root):
        """Main window for the app
        
        Args:
            root (ttk): The root for this window.
        """
        Tk.report_callback_exception = self.show_error
        self.root = root
        self.root.title("Transcriber")
        self.root.geometry(self.get_initial_geometry())
        self.root.config(bg = COLOR_THEME.MAIN_WINDOW)
        
        # file management - label
        self.label_file_management = Label(self.root, text="Files for transcription", font=LABEL_FONT, bg=COLOR_THEME.MAIN_WINDOW)
        self.label_file_management.pack(padx=5, pady=3, side=TOP)
        ToolTip(self.label_file_management, text="Select the files to be transcribed!\nNote that we will handle file conversions!")
        
        # file management - list area
        self.frame_file_management_list = Frame(self.root, bg=COLOR_THEME.MAIN_WINDOW)
        self.frame_file_management_list.pack(fill=BOTH, expand=True)
        
        # file management - add files
        # @TODO: should the first element be self.root or the self.frame_file_management_list?
        self.button_add_files = Button(self.frame_file_management_list, text="Select Files", command=self.select_new_files, font=BUTTON_FONT, bg=COLOR_THEME.BUTTON)
        self.button_add_files.pack(padx=5, pady=3)
        ToolTip(self.button_add_files, text = "Select multiple files to be transcribed. (Opens file selection window).")
        
        # model selection
        self.label_select_model = Label(self.root, text="Select AI Model:", font=LABEL_FONT, bg=COLOR_THEME.MAIN_WINDOW)
        self.label_select_model.pack()
        model_list = get_model_list()
        self.dropdown_selection_value = StringVar()
        self.dropdown_model_selector = Combobox(self.root, values=model_list, textvariable=self.dropdown_selection_value)
        reccomended = ['small.en', 'medium.en', 'small', 'medium.en', model_list[0] if len(model_list) else None]
        for r in reccomended:
            try:
                idx = model_list.index(r)
                self.dropdown_model_selector.current(idx)
                break
            except:
                pass
        self.dropdown_model_selector.pack()
        model_help_text = """MODEL TYPES EXPLAINED
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

        Reccomended to use any of the '[size].en' models for english audio."""
        ToolTip(self.dropdown_model_selector, text=model_help_text)
        ToolTip(self.label_select_model, text=model_help_text)
        
        # start activity button
        self.button_start_transcribe = Button(self.root, text="Start Transcribe", command=self.start_transcribe, font=BUTTON_FONT, bg=COLOR_THEME.BUTTON)
        self.button_start_transcribe.pack(pady=5)
        ToolTip(self.button_start_transcribe, text="Click here to start transcribing the files in the list!\nNote: If the transcription seems off, try running it again! Its possible the AI gets different results each time.")
        
        # console monitor
        # Create a ScrolledText widget inside the frame
        # self.output_box = ScrolledText(self.root, wrap=tk.WORD, padx=5, pady=5, relief=SOLID, font=("consolas", 8, NORMAL), height=100)
        # self.output_box.pack(fill=BOTH, expand=True)
        # self.output_box.configure(state="disabled")
        # self.output_handler = CustomStdOut(self.output_box)
        # # Redirect stdout to the custom class
        # sys.stdout = self.output_handler

        # # Configure the logger
        # self.logger = logging.getLogger('batchalign')
        # multiprocessing.get_logger().addHandler(sys.stdout)
        # self.logger.setLevel(logging.DEBUG)

        # # Create a handler and set the output stream to the custom stdout
        # self.handler = logging.StreamHandler(sys.stdout)
        # self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        # self.handler.setFormatter(self.formatter)
        # self.logger.addHandler(self.handler)


        # # Example usage
        # self.logger.info("This is a test log message.")
        # print("This will also be captured by the custom stdout.", flush = True)

    def get_initial_geometry(self) -> str:
        """
        Returns:
            str: window size geometry f"{PxX}x{PxY}"
        """
        return f"{max(self.root.winfo_screenwidth()/3, 800)}x{max(self.root.winfo_screenheight()/3,430)}"
    
    def select_new_files(self):
        """Selects new files to be added to the file managament list."""
        audio_video_types = todo_get_ffmpeg_supported_file_types()
        file_paths = filedialog.askopenfilenames(filetypes=[("Audio/Video", ";".join([f"*.{x}" for x in audio_video_types])), ('All Files', "*.*")])
        langs = list(todo_get_available_langs().values())
        for file in file_paths:
            SelectedFileConfigElement(self.frame_file_management_list, filepath=os.path.normpath(file), min_speakers=1, max_speakers=99, languages=langs)
    
    def start_transcribe(self):
        """Starts the transcribe process in the background
        
        Returns: 
            : @todo: pipe?
        """
        selected_model = self.dropdown_selection_value.get()
        if len(SelectedFileConfigElement.MANAGER) == 0:
            raise Exception("Please select a file to transcribe first!")
        
        #shell, exepath = shellingham.detect_shell()
        currloc = pathlib.Path(__file__).parent.resolve()
        spawn_popup_activity(title="TRANSCRIBING!", message="TRANSCRIPTION STARTED, DONT CLICK THE BUTTON UNLESS YOU WANT MULTIPLE TRANSCRIPTIONS RUNNING FOR THE SELECTED THINGIES")
        for item in SelectedFileConfigElement.MANAGER:
            proc = subprocess.Popen(args=[sys.executable, f"{currloc}\\subproc.py", json.dumps({'input_file': item.get_file(), 'num_speakers': item.get_speakers(), 'lang': item.get_lang(), 'model_name':selected_model}, skipkeys=True, separators=(',', ':'))], cwd=os.getcwd(), start_new_session=True)
            self.root.title("Transcriber - PLEASE DONT KILL ME - I AM WORKING! I PROMISE!")
            while proc.poll() == None:
                try:
                    proc.wait()
                except:
                    pass
        self.root.title("Transcriber")
    
    def show_error(self, *args):
        """Display the error to the user as a popup window"""
        err = traceback.format_exception(*args)
        print("\n".join(err), flush=True)
        messagebox.showerror("Error!", f"{'\n'.join([str(a) for a in args[1].args])}\n\n\n\nPlease see the console for the full error message!")

class SelectedFileConfigElement:
    MANAGER = []
    def __init__(self, parent, filepath, min_speakers, max_speakers, languages):
        self.parent = parent
        self.filepath = filepath
        parentDir, filename = os.path.split(self.filepath)
        # make row frame
        self.row_frame = Frame(parent,borderwidth=2, relief=SOLID)
        self.row_frame.pack(fill=X, pady=2)
        # insert label frame for multiline file path
        self.label_frame = Frame(self.row_frame, padx=0, pady=0)
        self.label_frame.pack(side=LEFT, expand=True, anchor="w", padx=0, pady=0)
        # insert file labels
        self.path_label = Label(self.label_frame, text=f"{parentDir}{os.path.sep}", font=("consolas", 8, ITALIC), anchor="w", justify=LEFT)
        self.file_label = Label(self.label_frame, text=filename, width=35, font=("consolas", 10, BOLD), anchor="w", justify=LEFT, )
        self.path_label.grid(row=0, column=0)
        self.file_label.grid(row=1, column=0)
        ToolTip(self.label_frame, f"File path to be transcribed:\n\t{self.filepath}")
        # @todo: make quick context menu?
        # self.context_menu = Menu(self.parent, tearoff=0)
        # self.context_menu.add_command(label="Copy file path", command=self.set_clipboard_to_filepath)
        # self.context_menu.add_command(label="Remove", command=self.delete_row)
        # self.label_frame.bind("<Button-3>", func=self.show_context_menu)
        # insert config controls:
        # insert spinbox
        self.spinbox_num_speakers = Spinbox(self.row_frame, from_=min_speakers, to=max_speakers, justify=CENTER, width=5, textvariable=IntVar(value=2))
        self.spinbox_num_speakers.pack(side=LEFT, padx=5, pady=0)
        ToolTip(self.spinbox_num_speakers, "Estimated number of speakers in this file.\nBetween 1 thru 99 inclusive.")
        # insert language selection
        self.lang_combo = Combobox(self.row_frame, values=languages, width=10)
        self.lang_combo.pack(side=LEFT, padx=5)
        self.lang_combo.set(languages[0])
        ToolTip(self.lang_combo, "The language to be transcribed.\nIf its not here then its not supported :c")
        
        # insert delete button
        # 🗑️= \U0001F5D1; 🗴 1F5F4 🗶 1F5F6 🞨 1F7A8; 🞩 1F7A9; 🞪 1F7AA;🞫 1F7AB;🞬1F7AC;🞭1F7AD;🞮1F7AE;
        self.delete_button = Button(self.row_frame, text="\U0001F5D1", command=self.delete_row, font=BUTTON_FONT)
        self.delete_button.pack(side=LEFT, padx=5)
        ToolTip(self.delete_button, "Remove this file from the list of files to be transcribed.")
        self.set_bg(COLOR_THEME.MAIN_WINDOW)
        
        SelectedFileConfigElement.MANAGER.append(self)
    
    def set_bg(self, color):
        self.row_frame.configure(bg=color)
        self.label_frame.configure(bg=color)
        self.file_label.configure(bg=color)
        self.path_label.configure(bg=color)

    def set_clipboard_to_filepath(self, event):
        self.parent.clipboard_clear()
        self.parent.clipboard_append(self.filepath)
    
    def get_pointer(self):
        return self.row_frame
    
    def get_lang(self):
        return self.lang_combo.get()
    
    def get_file(self):
        return self.filepath
    
    def get_speakers(self):
        return int(self.spinbox_num_speakers.get())
    
    def delete_row(self):
        self.row_frame.destroy()
        SelectedFileConfigElement.MANAGER.remove(self)


class ToolTip(object):
    ACTIVE_TOOLTIPS = []
    def __init__(self, widget, text):
        """Binds a tooltip popup to a widget on <Enter> and <Leave>
        
        Args:
            widget (tkinter.Widget): element to attach tip to.
            text (str): tool tip string to display.
        """
        widget.bind('<Enter>', self.enter)
        widget.bind('<Leave>', self.leave)
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        ToolTip.ACTIVE_TOOLTIPS.append(self)
    
    def __del__(self):
        self.hidetip()
        ToolTip.ACTIVE_TOOLTIPS.remove(self)
    
    @staticmethod
    def hideall():
        for tt in ToolTip.ACTIVE_TOOLTIPS:
            try:
                tt.hidetip()
            except:
                pass
    
    def showtip(self, text):
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
                      font=TOOLTIP_FONT)
        label.pack(ipadx=1)
    
    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
    
    def enter(self, event):
        self.showtip(self.text)
    
    def leave(self, event):
        self.hidetip()


# def transcribe_file(input_file, model_name=None, num_speakers=2, lang="eng"):
#     # transcribe
#     whisper = ba.WhisperEngine(model=model_name, lang=lang)
#     diarization = ba.NemoSpeakerEngine(num_speakers=num_speakers)
#     disfluency = ba.DisfluencyReplacementEngine()
#     retrace = ba.NgramRetraceEngine()
#     # morphotag
#     morphosyntax = ba.StanzaEngine()
#     # align
#     utr = ba.WhisperUTREngine()
#     fa = ba.Wave2VecFAEngine()

#     pipeline_activity = [action for action in [
#         whisper,
#         diarization if num_speakers > 1 else None,
#         disfluency,
#         retrace,
#         morphosyntax,
#         utr,
#         fa
#     ] if action]
    
#     # create a pipeline
#     nlp = ba.BatchalignPipeline(*pipeline_activity)
#     doc = ba.Document.new(media_path=input_file, lang=lang)
#     doc = nlp(doc)
#     chat = ba.CHATFile(doc=doc)
#     n = 0
#     output_file = f"{input_file}{'_'+str(n) if n > 0 else ''}.cha"
#     while 1:
#         output_file = f"{input_file}{'_'+str(n) if n > 0 else ''}.cha"
#         if not os.path.exists(output_file):
#             break
#         n += 1
#     chat.write(output_file)
#     print(f"Wrote to {output_file}", flush=True)
#     return spawn_nonblocking_popup_activity(title="COMPLETED!",message=f"Completed transcription of\n{input_file}\nOutput file can be found here:\n{output_file}\nOpen file now?", yes=lambda: os.open(output_file))

# def spawn_nonblocking_popup_activity(title, message, yes=None, no=None):
#     def executable():
#         result = messagebox.askyesno(title=title, message=message)
#         if result and yes and type(yes) == function:
#             yes()
#         elif not result and no and type(no) == function:
#             no()
    
#     p = multiprocessing.Process(target=executable)
#     p.start()
#     return p

def spawn_popup_activity(title, message, yes=None, no=None):
    result = messagebox.askyesno(title=title, message=message)
    if result and yes and type(yes) == FunctionType:
        return yes()
    elif not result and no and type(no) == FunctionType:
        return no()
    
if __name__ == "__main__":
    root = tk.Tk()
    app = MainGUI(root=root)
    root.mainloop()
