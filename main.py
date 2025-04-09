import os
import re
from time import sleep, time
import tkinter as tk
from tkinter import BOTH, CENTER, E, LEFT, RIGHT, SOLID, TOP, W, X, Button, IntVar, Label, Spinbox, StringVar, Tk, Toplevel, filedialog, Frame, messagebox, font
from tkinter.font import BOLD, ITALIC, NORMAL
# from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Combobox
from types import FunctionType
from typing import List
import traceback
from ffmpeg import FFmpeg
import pycountry
import requests
# import batchalign as ba
import sys
import subprocess
import pathlib
import json
from huggingface_hub.hf_api import repo_exists as is_valid_model_id
from PIL import Image, ImageTk
# import logging

# CONSTANTS
class COLOR_THEME:
    IN_PROGRESS = "lightyellow"
    LOADED = "aqua"
    MAIN_WINDOW = "lightblue"
    FAILED = "lightred"
    COMPLETED = "green"
    BUTTON = "pink"

LABEL_FONT = ("Arial", 12, BOLD)
BUTTON_FONT = ("Arial", 12, NORMAL)
FILE_NAME_FONT = ("Consolas", 10, NORMAL)
TOOLTIP_FONT = ("Consolas", 8, NORMAL)

HF_TOKEN_FILENAME = ".hftoken"
MODELS_CFG_FILENAME = "cfg/models.json"
CACHE_FILENAME = "cfg/cache.json"
MASCOT_FILENAME = "cfg/mascot.png"
TRANSCRIBE_SUBPROC_FILENAME = "transcribe_proc.py"


# @todo if they ask for it, give an in window output text box to display
# the output instead of printing to the shell
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
#         
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
        
        self.load_cache()
        
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
        
        self.frame_model_selection_block = Frame(self.root, bg=COLOR_THEME.MAIN_WINDOW)
        self.frame_model_selection_line = Frame(self.frame_model_selection_block, bg=COLOR_THEME.MAIN_WINDOW)
        # model selection
        self.label_select_model = Label(self.frame_model_selection_block, text="Select AI Model:", font=LABEL_FONT, bg=COLOR_THEME.MAIN_WINDOW)
        self.label_select_model.pack(fill=X, expand=True, anchor=CENTER)
        model_list = self.cache.get('modelCache',[])
        for model in self.get_model_list():
            if model not in model_list:
                model_list.append(model)
        
        self.dropdown_selection_value = StringVar()
        self.dropdown_model_selector = Combobox(self.frame_model_selection_line, values=model_list, textvariable=self.dropdown_selection_value)
        
        reccomended = [self.cache.get('selectedModel','openai/whisper-small.en'),'openai/whisper-small.en', 'openai/whisper-medium.en', 'openai/whisper-small', 'openai/whisper-medium.en', model_list[0] if len(model_list) else None]
        for r in reccomended:
            try:
                idx = model_list.index(r)
                self.dropdown_model_selector.current(idx)
                break
            except:
                pass
        self.dropdown_model_selector.pack(fill=X, side=LEFT, anchor=W, expand=True, padx=10)
        self.button_find_more_models = Button(self.frame_model_selection_line, text="Find a different model", command=open_hf_search, font=BUTTON_FONT, bg=COLOR_THEME.BUTTON)
        self.button_find_more_models.pack(side=RIGHT, anchor=E, padx=10)
        self.frame_model_selection_block.pack(fill=X, expand=True)
        self.frame_model_selection_line.pack(fill=X, expand=True)
        
        model_help_text = """Models can be set from any valid huggingface model.
Reccomended to use one of the following:
From batchalign:
    - 'talkbank/CHATWhisper-en'
    
From OpenAI:
    * Choose the size that runs well on your computer.
    'openai/whisper-<TYPE>'
    Where you replace <TYPE> with the selected model. 
    For example, if you want the English only tiny type, then the value should be 'openai/whisper-tiny.en'.
    ╔════════╦══════════════╦══════════╦══════════╗
    ║        ║ English-only ║ Required ║ Relative ║
    ║  TYPE  ║     TYPE     ║   VRAM   ║  speed   ║
    ╠════════╬══════════════╬══════════╬══════════╣
    ║ tiny   ║   tiny.en    ║   ~1 GB  ║   ~10x   ║
    ║ base   ║   base.en    ║   ~1 GB  ║    ~7x   ║
    ║ small  ║   small.en   ║   ~2 GB  ║    ~4x   ║
    ║ medium ║   medium.en  ║   ~5 GB  ║    ~2x   ║
    ║ large  ║   N/A        ║  ~10 GB  ║     1x   ║
    ║ turbo  ║   N/A        ║   ~6 GB  ║    ~8x   ║
    ╚════════╩══════════════╩══════════╩══════════╝
    
From other providers:
    Use the search button and find a model that you wish to use from huggingface.
    Enter the model ID to use as '<AUTHOR>/<NAME>' (the same pattern as the talkbank and openai models).
    Note that not all models will be valid, and you will only find out when it crashes when it attempts to transcribe.
    Use a model that is based off of the Openai whisper base!

See the README.md file for more info!"""
        ToolTip(self.dropdown_model_selector, text=model_help_text)
        ToolTip(self.label_select_model, text=model_help_text)
        
        # start activity button
        self.button_start_transcribe = Button(self.root, text="Start Transcribe", command=self.start_transcribe, font=BUTTON_FONT, bg=COLOR_THEME.BUTTON)
        self.button_start_transcribe.pack(pady=5)
        ToolTip(self.button_start_transcribe, text="Click here to start transcribing the files in the list!\nNote: If the transcription seems off, try running it again! Its possible the AI gets different results each time.")
        
        # self.dbgbutn = Button(self.root, text="dbgbutton", command=lambda: self.show_mascot("IM TRANSCRIIIIBINNNG!!\nTRANSCRIPTION STARTED, DONT CLICK THE START TRANSCRIBE BUTTON AGAIN UNLESS YOU WANT MULTIPLE TRANSCRIPTIONS RUNNING FOR THE SELECTED THINGIES AT THE SAME TIME!"))
        # self.dbgbutn.pack()
        
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
        
        for fn in self.cache.get("fileCache", []):
            if os.path.exists(fn['filepath']):
                SelectedFileConfigElement(self.frame_file_management_list, filepath=os.path.normpath(fn['filepath']), min_speakers=fn['min_speakers'], max_speakers=fn['max_speakers'], languages=fn['languages'])
    
    
    def __del__(self):
        self.update_cache()
    
    def get_initial_geometry(self) -> str:
        """
        Returns:
            str: window size geometry f"{PxX}x{PxY}"
        """
        return f"{max(self.root.winfo_screenwidth()/3, 800)}x{max(self.root.winfo_screenheight()/3,430)}"
    
    def select_new_files(self):
        """Selects new files to be added to the file managament list."""
        audio_video_types = get_audio_file_types() + get_video_file_types()
        file_paths = filedialog.askopenfilenames(filetypes=[("Audio/Video", ";".join([f"*.{x}" for x in audio_video_types])), ('All Files', "*.*")])
        langs = list(get_available_langs())
        for file in file_paths:
            SelectedFileConfigElement(self.frame_file_management_list, filepath=os.path.normpath(file), min_speakers=1, max_speakers=99, languages=langs)
    
    def start_transcribe(self):
        """Starts the transcribe process in the background
        
        Returns: 
            : @todo: pipe?
        """
        if not is_valid_model_id(self.dropdown_model_selector.get()):
            if not spawn_popup_activity("Error!", f"An issue occured when we attempted to get the\n\n{self.dropdown_model_selector.get()}\n\nmodel. Please verify your huggingface token allows for read permissions of the given model.\n\nYes to continue with default model, no to abort!"):
                return
        
        self.update_cache()
        selected_model = self.dropdown_selection_value.get()
        if len(SelectedFileConfigElement.MANAGER) == 0:
            raise Exception("Please select a file to transcribe first!")
        
        #shell, exepath = shellingham.detect_shell()
        currloc = pathlib.Path(__file__).parent.resolve()
        mascot = self.show_mascot("IM TRANSCRIIIIBINNNG!!\nTRANSCRIPTION STARTED, DONT CLICK THE START TRANSCRIBE BUTTON AGAIN UNLESS YOU WANT MULTIPLE TRANSCRIPTIONS RUNNING FOR THE SELECTED THINGIES AT THE SAME TIME!")
        #spawn_popup_activity(title="TRANSCRIBING!", message="TRANSCRIPTION STARTED, DONT CLICK THE BUTTON UNLESS YOU WANT MULTIPLE TRANSCRIPTIONS RUNNING FOR THE SELECTED THINGIES")
        for item in SelectedFileConfigElement.MANAGER:
            valid = validate_language(item.get_lang())
            if valid is None:
                spawn_popup_activity('WARNING!','Transcript process DID NOT START.\nPlease fix the errors and try again.')
                return
        
        for item in SelectedFileConfigElement.MANAGER:
            # needs conversion?
            if not (item.get_file().split('.')[-1] in get_audio_file_types()):
                # looks like it probably needs conversion
                print(f"Converting {item.get_file()} to mp3 type so that it can be transcribed!")
                item.filepath = convert_file_to_type(item.get_file(), '.mp3')
                print(f"Convertion completed! Audio file can be found {item.get_file()}")
            proc = subprocess.Popen(
                args=[
                    sys.executable,
                    f"{currloc}\\{TRANSCRIBE_SUBPROC_FILENAME}",
                    json.dumps({
                        'input_file': item.get_file(), 
                        'num_speakers': item.get_speakers(), 
                        'lang': item.get_lang(), 
                        'model_name':selected_model
                        },
                        skipkeys=True, 
                        separators=(',', ':'))
                    ],
                    cwd=os.getcwd(),
                    start_new_session=True
                )
            self.root.title("Transcriber - PLEASE DONT KILL ME - I AM WORKING! I PROMISE!")
            while proc.poll() == None:
                try:
                    self.root.update_idletasks()
                    #proc.wait(timeout=1)
                except:
                    pass
        try:
            mascot.destroy()
        except:
            pass
        self.root.title("Transcriber")
    
    def show_error(self, *args):
        """Display the error to the user as a popup window"""
        err = traceback.format_exception(*args)
        print("\n".join(err), flush=True)
        messagebox.showerror("Error!", f"{'\n'.join([str(a) for a in args[1].args])}\n\n\n\nPlease see the console for the full error message!")
    
    def get_model_list(self) -> List[str]:
        """
        Gets an updated list of models
        Returns:
            List[str]: List of available model names
        """
        models = {}
        models_to_search = []
        if os.path.isfile(MODELS_CFG_FILENAME):
            with open(MODELS_CFG_FILENAME, 'r', encoding='utf-8') as f:
                models_to_search = json.load(f)
        for q in models_to_search:
            results = get_hf_search_query(**q)
            for r in results:
                if r.get('pipeline_tag') == 'automatic-speech-recognition':
                    models[r['id']] = r
        models = sorted(models, key = lambda k: models[k].get('downloads', models[k].get('likes', 0)), reverse=True)
        return models
    
    def load_cache(self):
        """Loads and imports data from the cache file to save time."""
        if os.path.isfile(CACHE_FILENAME):
            with open(CACHE_FILENAME, 'r', encoding='utf-8') as f:
                self.cache = json.load(f)
    
    def update_cache(self):
        """Saves an updated cache file"""
        cache = self.cache or {}
        if self.dropdown_model_selector['values']:
            cache["modelCache"] = cache.get('modelCache',[]) + [str(x) for x in self.dropdown_model_selector['values'] if str(x) not in cache.get('modelCache', [])]
        if self.dropdown_selection_value.get():
            cache["selectedModel"] = self.dropdown_selection_value.get() or self.cache.get("selectedModel", None)
        for entry in (SelectedFileConfigElement.MANAGER):
            c = False
            for idx in range(len(cache.get("fileCache",[]))):
                if entry.filepath == cache["fileCache"][idx].get("filepath"):
                    cache["fileCache"][idx] = {"filepath": entry.filepath, "min_speakers": entry.min_speakers, "max_speakers": entry.max_speakers, "languages": [entry.lang_combo.get(), *[x for x in entry.lang_combo['values'] if x != entry.lang_combo.get()]]}
                    c = True
                    break
            if c == False:
                cache["fileCache"] = cache.get("fileCache",[]) + [{"filepath": entry.filepath, "min_speakers": entry.min_speakers, "max_speakers": entry.max_speakers, "languages": [entry.lang_combo.get(), *[x for x in entry.lang_combo['values'] if x != entry.lang_combo.get()]]}]
        if not os.path.exists(os.path.dirname(CACHE_FILENAME)):
            os.mkdir(os.path.pardir(CACHE_FILENAME))
        with open(CACHE_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(cache, indent=2, fp=f)
    
    def show_mascot(self, message):
        # Create popup window
        popup = Toplevel(self.root)
        popup.title("AY, IM WORKIN ERE")
        popup.overrideredirect(True)  # Remove window decorations
        # Set window transparency attributes (Windows only)
        popup.wm_attributes("-transparentcolor", "#f0f0f0")
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Load and scale the image
        img = Image.open(MASCOT_FILENAME)
        img_ratio = img.width / img.height
        max_width, max_height = screen_width - 100, screen_height - 100  # Add padding
        if img.width > max_width or img.height > max_height:
            if img_ratio > 1:
                img = img.resize((max_width, int(max_width / img_ratio)), Image.LANCZOS)
            else:
                img = img.resize((int(max_height * img_ratio), max_height), Image.LANCZOS)
        
        # Convert to Tkinter image
        img_tk = ImageTk.PhotoImage(img)
        
        # Create canvas for displaying the image
        canvas = tk.Canvas(popup, width=img.width, height=img.height, highlightthickness=0)
        canvas.pack()
        
        # Display the image
        canvas.create_image(0, 0, anchor="nw", image=img_tk)
        popup.image = img_tk  # Keep a reference
        
        # Overlay text
        text_label = tk.Label(popup, text=message, font=("Arial", 16, "bold"),
                          fg="black", bg="white", wraplength=img.width - 20)
        text_label.place(anchor=CENTER, y=(img.height // 3) * 2, x = img.width//2, width=img.width - 20)
        
        # Center popup on screen
        x_position = (screen_width - img.width) // 2
        y_position = (screen_height - img.height) // 2
        popup.geometry(f"+{x_position}+{y_position}")

        popup.deiconify()
        popup.wm_protocol("WM_DELETE_WINDOW", popup.destroy)
        popup.wait_visibility()
        return popup

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
        self.min_speakers = min_speakers
        self.max_speakers = max_speakers
        self.spinbox_num_speakers = Spinbox(self.row_frame, from_=min_speakers, to=max_speakers, justify=CENTER, width=5, textvariable=IntVar(value=2))
        self.spinbox_num_speakers.pack(side=LEFT, padx=5, pady=0)
        ToolTip(self.spinbox_num_speakers, "Estimated number of speakers in this file.\nBetween 1 thru 99 inclusive.")
        # insert language selection
        self.lang_combo = Combobox(self.row_frame, values=languages, width=10)
        self.lang_combo.pack(side=LEFT, padx=5)
        self.lang_combo.set(languages[0])
        ToolTip(self.lang_combo, "The language to be transcribed.\nValid language codes are:\nThe 2 letter code such as 'en', 'es', 'zh', etc.\nThe 3 letter code such as 'eng', 'spa', 'zho'\nThe full name such as 'english', 'spanish', 'chinese'.")
        
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


def spawn_popup_activity(title, message, yes=None, no=None):
    result = messagebox.askyesno(title=title, message=message)
    if result and yes and type(yes) == FunctionType:
        return yes()
    elif not result and no and type(no) == FunctionType:
        return no()
    elif result and (yes is not None):
        return yes
    elif result and (no is not None):
        return no
    return result

def get_hf_token():
    try:
        stats = os.stat(HF_TOKEN_FILENAME)
        if stats.st_size == 0:
            raise Exception("Empty file!")
    except:
        with open(HF_TOKEN_FILENAME, 'w') as f:
            f.write("hf_YOUR_TOKEN_HERE\nSee here for details:\n\nhttps://huggingface.co/docs/hub/en/security-tokens")
        spawn_popup_activity("Error!", f"To use the search feature, you must have a file named\n\t'{HF_TOKEN_FILENAME}'\nthat contains your huggingface token!\nSee here for details:\n\nhttps://huggingface.co/docs/hub/en/security-tokens\n\nRetry operation after you have set your token.")
        return
    with open(HF_TOKEN_FILENAME, 'r', encoding='utf-8') as f:
        hf_token = f.read().strip()
    return hf_token

def get_hf_search_query(**kwargs):
    """Get hf search query
    Expects kwargs to pass to the GET request.
    Ex:
    search="whisper",author="openai"
    etc.
    Returns:
        _type_: _description_
    """
    hf_token = get_hf_token()
    response = requests.get(
        "https://huggingface.co/api/models",
        params={
            **{k:kwargs[k] for k in kwargs if not k.lower().strip().startswith('expand')},
            "sort": kwargs.get('sort', "downloads"),
            "limit": kwargs.get('limit', "10"),
            "config": "True",
            "full": "False",
        },
        headers={
            "Authorization":f"Bearer {hf_token}"
        })
    if response.status_code == 401:
        spawn_popup_activity("Error!", f"Invalid huggingface token!\nTo use the search feature, you must have a file named\n\t'{HF_TOKEN_FILENAME}'\nthat contains your huggingface token!\nSee here for details:\n\nhttps://huggingface.co/docs/hub/en/security-tokens")
    return response.json()

def search_for_hf_model(query):
    """Searches huggingface to validate a model name
    Will check for the HF_TOKEN_FILENAME.
    If more than one match is found we will ask the user to select which one they wanted.
    Args:
        query (str): query string to be searched.
    
    Raises:
        Exception: If something went wrong.
    
    Returns:
        str | None: if a model is selected, we will return the model id, otherwise we will return None.
    """
    data = get_hf_search_query(search=query)
    # pre-filter for only whisper based models
    data = [x for x in data if x["config"]["model_type"] == "whisper"]
    if len(data) == 0:
        spawn_popup_activity(f"Search result", f"'{query}' yeilded {len(data)} results. Try again.")
        return None
    
    if not spawn_popup_activity(f"Search result", f"'{query}' yeilded {len(data)} results. Click Yes to view them or No to abort search selection. Click yes on the next window that matches the entry you want to use..."):
        return None
    
    while True:
        for idx, entry in enumerate(data,start=1):
            selected = spawn_popup_activity(f"Search result: #{idx}", f"'{query}' result #{idx}/{len(data)}:\n{entry['id']}\n\n{json.dumps(entry, indent=2)}\n\n Use selection?")
            if selected:
                return entry['id']
        if not spawn_popup_activity(f"Search result", f"End of results for '{query}'.\nYes to restart from the beginning or no to abort search:"):
            return None

def open_hf_search():
    os.startfile("https://huggingface.co/models?pipeline_tag=automatic-speech-recognition&library=transformers")
    spawn_popup_activity("Search", "Use the huggingface search to find the model ID or model name to use. Click yes or no to continue.")

def get_available_langs() -> List[str]:
    """Returns:
        List[str]: language codes or names available for transcription.
    """
    common = ['', 'English', 'Spanish', 'Arabic', 'Egyptian Arabic', 'Bengali', 'Bhojpuri', 'Mandarin Chinese', 'German', 'French', 'Gujarati', 'Hausa', 'Hebrew', 'Hindi', 'Indonesian', 'Italian', 'Javanese', 'Japanese', 'Korean', 'Marathi', 'Iranian Persian', 'Portuguese', 'Russian', 'Tamil', 'Telugu', 'Turkish', 'Urdu', 'Vietnamese', 'Wu Chinese', 'Yue Chinese']
    return common

def validate_language(inp):
    if not inp:
        return inp
    try:
        l = pycountry.languages.lookup(inp)
        return l.alpha_3
    except LookupError as e:
        spawn_popup_activity("Language Error!", f"Unable to determine language: '{inp}'.\nValid language codes are:\nThe 2 letter code such as 'en', 'es', 'zh', etc.\nThe 3 letter code such as 'eng', 'spa', 'zho'\nThe full name such as 'english', 'spanish', 'chinese'.\nPress any button to continue.")
    return None

def get_audio_file_types() -> List[str]:
    return [
        "3gp", "aa", "aac", "aax", "act", "aiff", "alac", "amr", 
        "ape", "au", "awb", "dss", "dvf", "flac", "gsm", "iklax", 
        "ivs", "m4a", "m4b", "m4p", "mmf", "movpkg", "mp3", "mpc", 
        "msv", "nmf", "ogg", "oga", "mogg", "opus", "ra", "rm", 
        "raw", "rf64", "sln", "tta", "voc", "vox", "wav", "wma", 
        "wv", "webm", "8svx", "cda"
    ]

def get_video_file_types() -> List[str]:
    return [
        "webm", "mkv", "flv", "flv", "vob", "ogv", "ogg", "drc",
        "gifv", "mng", "avi", "MTS", "M2TS", "TS", "mov", "qt", 
        "wmv", "yuv", "rm", "rmvb", "viv", "asf", "amv", "mp4", 
        "m4p (with DRM)", "m4v", "mpg", "mp2", "mpeg", "mpe", "mpv",
        "mpg", "mpeg", "m2v", "m4v", "svi", "3gp", "3g2", "mxf", 
        "roq", "nsv", "flv", "f4v", "f4p", "f4a", "f4b"
    ]

def convert_file_to_type(inp_file: str, totype: str):
    """Converts given file to the file type using ffmpeg.

    Args:
        inp_file (str): the input file path
        totype (str): the output file type extention

    Returns:
        str: the output file path
    """
    name, ext = os.path.splitext(inp_file)
    out_name = f"{name}{'' if str(totype).startswith('.') else '.'}{totype}"
    if os.path.exists(out_name):
        # assume it has already converted the file
        print(f"Using cached version of {inp_file}!")
        return out_name
    FFmpeg().input(inp_file).output(out_name).execute()
    return out_name

if __name__ == "__main__":
    root = tk.Tk()
    app = MainGUI(root=root)
    root.mainloop()
