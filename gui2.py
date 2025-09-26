import tkinter as tk
from tkinter import ttk
import os
from time import sleep, time
import tkinter as tk
from tkinter import BOTH, CENTER, E, LEFT, RIGHT, SOLID, TOP, VERTICAL, W, X, IntVar, Label, StringVar, Tk, Toplevel, filedialog, Frame, messagebox, font, Button
from tkinter.ttk import Checkbutton, Combobox, Spinbox
from tkinter.font import BOLD, ITALIC, NORMAL
# from tkinter.scrolledtext import ScrolledText
from types import FunctionType
from typing import List
import traceback
import ffmpeg
import pycountry
import requests
import sys
import subprocess
import json
from huggingface_hub.hf_api import repo_exists as is_valid_model_id
from PIL import Image, ImageTk
from torch.cuda import is_available as is_cuda_available, mem_get_info as get_cuda_mem_info
from pathlib import Path
import shutil
import soundfile
from functools import lru_cache


# CONSTANTS/config
class COLOR_THEME:
    IN_PROGRESS = "#FFFFE0"   # lightyellow
    LOADED = "#00FFFF"        # aqua
    MAIN_WINDOW = "#ADD8E6"   # lightblue
    FAILED = "#E04545"        # lightred
    COMPLETED = "#008000"     # green
    BUTTON = "#FFC0CB"        # pink


DEFAULT_FONT = "Helvetica" if sys.platform == "darwin" else "Arial"
MONO_FONT = "Menlo" if sys.platform == "darwin" else "Consolas"
LABEL_FONT = (DEFAULT_FONT, 12, BOLD)
BUTTON_FONT = (DEFAULT_FONT, 12, NORMAL)

FILE_NAME_FONT = (MONO_FONT, 10, NORMAL)
TOOLTIP_FONT = (MONO_FONT, 8, NORMAL)


def normalize_path(*path):
    """Gets a normalized path

    Args:
        path (str[]|Path): Path to join/normalize

    Returns:
        Path: The normalized path
    """
    if len(path) > 1:
        path = Path(*path)
    else:
        path = path[0] # allow out of bounds exception
    if type(path) == str:
        path = Path(path)
    if not isinstance(path, Path):
        raise ValueError(f"Path argument must be a str or Path")
    return path.expanduser().resolve()

THIS_DIR = normalize_path(__file__).parent

# defaults
TOOLS_DIR_REL = "tools"
CONFIG_FILES_DIRECTORY_REL = "cfg" 

MODELS_FN = "models.json"
CACHE_FN = "cache.json"
MASCOT_FN = "mascot.png"
HF_TOKEN_FN = ".hftoken"
TRANSCRIBE_SUBPROC_FN = "transcribe_proc.py"

MODELS_CFG_DEFAULT = normalize_path(THIS_DIR, CONFIG_FILES_DIRECTORY_REL, MODELS_FN)
CACHE_DEFAULT = normalize_path(THIS_DIR, CONFIG_FILES_DIRECTORY_REL, CACHE_FN)

# per user config file location
PER_USER_ROOT = normalize_path(Path.home())
PER_USER_CONFIG_FILES_DIRECTORY_REL = f".{CONFIG_FILES_DIRECTORY_REL}"
MODELS_CFG_FILENAME = normalize_path(PER_USER_ROOT, PER_USER_CONFIG_FILES_DIRECTORY_REL, MODELS_FN)
CACHE_FILENAME = normalize_path(PER_USER_ROOT, PER_USER_CONFIG_FILES_DIRECTORY_REL, CACHE_FN)


# functional config values
HF_TOKEN_FILENAME = normalize_path(THIS_DIR, HF_TOKEN_FN)
MASCOT_FILENAME = normalize_path(CONFIG_FILES_DIRECTORY_REL, MASCOT_FN)
TRANSCRIBE_SUBPROC_FILENAME = normalize_path(THIS_DIR, TRANSCRIBE_SUBPROC_FN)
FFMPEG_EXE_DIR = normalize_path(TOOLS_DIR_REL)

# add ffmpeg tools to path so that downstream modules can use it (specifically for windows)
sys.path.append(FFMPEG_EXE_DIR.as_posix())

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
        try:
            self.hidetip()
            ToolTip.ACTIVE_TOOLTIPS.remove(self)
        except:
            pass
    
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

def get_available_langs() -> List[str]:
    """Returns:
        List[str]: language codes or names available for transcription.
    """
    common = ['', 'English', 'Spanish', 'Arabic', 'Egyptian Arabic', 'Bengali', 'Bhojpuri', 'Mandarin Chinese', 'German', 'French', 'Gujarati', 'Hausa', 'Hebrew', 'Hindi', 'Indonesian', 'Italian', 'Javanese', 'Japanese', 'Korean', 'Marathi', 'Iranian Persian', 'Portuguese', 'Russian', 'Tamil', 'Telugu', 'Turkish', 'Urdu', 'Vietnamese', 'Wu Chinese', 'Yue Chinese']
    return common

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
    hf_search_url = "https://huggingface.co/models?pipeline_tag=automatic-speech-recognition&library=transformers"
    try:
        import webbrowser
        webbrowser.open(hf_search_url)
    except:
        try:
            os.startfile(hf_search_url)
        except:
            print(f"Visit the following URL to find additional models from huggingface:\n{hf_search_url}")
    spawn_popup_activity("Search", f"Use the huggingface search to find the model ID or model name to use. Click yes or no to continue.\n\nURL: {hf_search_url}")

def validate_language(inp):
    if not inp:
        return inp
    try:
        l = pycountry.languages.lookup(inp)
        return l.alpha_3
    except LookupError as e:
        spawn_popup_activity("Language Error!", f"Unable to determine language: '{inp}'.\nValid language codes are:\nThe 2 letter code such as 'en', 'es', 'zh', etc.\nThe 3 letter code such as 'eng', 'spa', 'zho'\nThe full name such as 'english', 'spanish', 'chinese'.\nPress any button to continue.")
    return None

def get_any_file_type() -> List[str]:
    return ["*", ".*", "*.*"]

def get_audio_file_types() -> List[str]:
    """Supported audio file types that dont need to be converted

    Returns:
        list of file extentions
    """
    # if its not usable by the soundfile package then it will cause an error to be thrown
    return [t.lower() for t in soundfile.available_formats().keys()]

@lru_cache(maxsize=1)
def get_ffmpeg_supported_formats():
    result = subprocess.run(
        ['ffmpeg', '-formats'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True  # decode to string instead of bytes
    )

    ret = set()
    for line in result.stdout.split('\n'):
        if not line:
            continue
        sections = [x for x in line.split(' ') if x]
        if len(sections) < 2:
            continue
        filetypes = sections[1].lower().split(',')
        ret |= set(filetypes)
    if len(ret) < 10:
        # something went wrong
        print("Ensure that ffmpeg is installed correctly!")
    return sorted(ret)

def get_video_file_types() -> List[str]:
    return [
        "webm", "mkv", "flv", "avi", "mov", "mp4", "m4v", "mpeg", 
        "mpg", "mpeg", "m2v", "m4v", "f4v", "f4p", "f4a", "f4b",
        "evo", "divx", "m4a"
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
    try:
        out, err = (ffmpeg
            .input(inp_file)
            .output(out_name)#, format='s16le', acodec='pcm_s16le', ac=1, ar='16k')
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        print(f"Failed to convert '{inp_file}' to '{totype}'! Please attempt to convert it to '{totype}' manually and retrying!")
    return out_name


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        Tk.report_callback_exception = self.show_error

        self.load_cache()

        self.title("Transcriber")
        self.minsize(300, 300)
        self.geometry(self.get_initial_geometry())
        self.config(bg = COLOR_THEME.MAIN_WINDOW)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_header()
        self.create_center()
        self.create_footer()

        self.bind("<Configure>", self.on_resize_window)

    def create_header(self):
        self.header_frame = tk.Frame(self, bg="#dddddd")
        self.header_frame.grid(row=0, column=0, sticky="nsew")
        self.header_frame.grid_propagate(False)

        self.header_buttons = [tk.Button(self.header_frame, text=f"Btn{i+1}", command=self.test_mascot) for i in range(3)]
        for btn in self.header_buttons:
            btn.pack(side="left", padx=2, pady=5)
    def test_mascot(self):
        mascot = Mascot("IM TRANSCRIIIIBINNNG!!\nTRANSCRIPTION STARTED, DONT CLICK THE START TRANSCRIBE BUTTON AGAIN UNLESS YOU WANT MULTIPLE TRANSCRIPTIONS RUNNING FOR THE SELECTED FILES AT THE SAME TIME!")
        sleep(2)
        try:
            mascot.destroy()
        except Exception as e:
            print(e)
        
    def create_center(self):
        self.center_frame = tk.Frame(self, bg="white")
        self.center_frame.grid(row=1, column=0, sticky="nsew")

        # Scrollable canvas
        self.canvas = tk.Canvas(self.center_frame, borderwidth=0, background="white")
        self.scroll_frame = tk.Frame(self.canvas, background="white")
        self.v_scroll = tk.Scrollbar(self.center_frame, orient="vertical", command=self.canvas.yview)

        self.canvas.configure(yscrollcommand=self.v_scroll.set)
        self.v_scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", tags="inner")

        self.scroll_frame.bind("<Configure>", self.on_frame_configure)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.canvas.bind("<Configure>", self.on_resize_canvas)

        for i in range(10):
            self.add_row(i)
    
    def add_row(self, index):
        row = tk.Frame(self.scroll_frame)
        row.pack(fill="x", expand=True, padx=5, pady=3)

        # Configure column 0 (label) to expand
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)
        row.grid_columnconfigure(2, weight=0)
        row.grid_columnconfigure(3, weight=0)

        # Fixed-width Spinbox
        spin = tk.Spinbox(row, from_=0, to=100, width=6)
        spin.grid(row=0, column=1, padx=4)

        langs = get_available_langs()
        self.lang_combo = ttk.Combobox(row, values=langs, width=10)
        self.lang_combo.grid(row=0, column=2, padx=5)

        btn2 = tk.Button(row, text="Del", width=6)
        btn2.grid(row=0, column=3, padx=2)

        # Expanding label
        label = tk.Label(row, text=f"Item {index}\nDescription", justify="right", anchor="e")
        label.grid(row=0, column=0, padx=(0, 10), sticky="NW")

    def create_footer(self):
        self.footer_frame = tk.Frame(self, bg="#f0f0f0")
        self.footer_frame.grid(row=2, column=0, sticky="nsew")
        self.footer_frame.grid_propagate(False)

        self.footer_frame.grid_rowconfigure(0, weight=1)
        self.footer_frame.grid_rowconfigure(1, weight=1)
        self.footer_frame.grid_columnconfigure(0, weight=1)

        top_row = tk.Frame(self.footer_frame)
        top_row.grid(row=0, column=0, sticky="ew", pady=(10, 5))
        top_row.grid_columnconfigure(0, weight=9)
        top_row.grid_columnconfigure(1, weight=1)

        self.selector = ttk.Combobox(top_row, values=["Option 1", "Option 2"])
        self.selector.grid(row=0, column=0, sticky="ew", padx=(10, 5))
        self.find_button = tk.Button(top_row, text="Find")
        self.find_button.grid(row=0, column=1, sticky="ew", padx=(5, 10))

        bottom_row = tk.Frame(self.footer_frame)
        bottom_row.grid(row=1, column=0, sticky="e", padx=10, pady=(0, 10))

        for i in range(3):
            tk.Button(bottom_row, text=f"Action {i+1}").pack(side="right", padx=5)

    def on_resize_window(self, event):
        win_h = self.winfo_height()

        header_h = min(max(40, int(0.1 * win_h)), 100)
        center_h = min(max(200, int(0.7 * win_h)), int(0.7 * win_h))
        footer_h = min(max(80, int(0.2 * win_h)), int(0.2 * win_h))

        self.header_frame.config(height=header_h)
        # self.center_frame.config(height=center_h)
        self.footer_frame.config(height=footer_h)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
    
    def on_resize_canvas(self, event):
        # Match the width of the internal frame to the canvas
        canvas_width = event.width
        self.canvas.itemconfig("inner", width=canvas_width)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def show_error(self, *args):
        """Display the error to the user as a popup window"""
        err = traceback.format_exception(*args)
        print("\n".join(err), flush=True)
        messagebox.showerror("Error!", '\n'.join([str(a) for a in args[1].args]) + "\n\n\n\nPlease see the console for the full error message!")
    
    def get_initial_geometry(self) -> str:
        """
        Returns:
            str: window size geometry f"{PxX}x{PxY}"
        """
        return f"{max(self.winfo_screenwidth()//3, 800)}x{max(self.winfo_screenheight()//3,430)}"
    
    def load_cache(self):
        """Loads and imports data from the cache file to save time."""
        # @TODO: validate and add items to the gui here
        if CACHE_FILENAME.is_file():
            with open(CACHE_FILENAME, 'r', encoding='utf-8') as f:
                self.cache = json.load(f)
        elif CACHE_DEFAULT.is_file():
            with open(CACHE_DEFAULT, 'r', encoding='utf-8') as f:
                self.cache = json.load(f)
        else:
            print(f"ERROR: MISSING CACHE FILE: '{CACHE_FILENAME}' or '{CACHE_DEFAULT}'")
    
    def get_model_list(self) -> List[str]:
        """
        Gets an updated list of models
        Returns:
            List[str]: List of available model names
        """
        models = {}
        models_to_search = []
        if MODELS_CFG_FILENAME.is_file():
            with open(MODELS_CFG_FILENAME, 'r', encoding='utf-8') as f:
                models_to_search = json.load(f)
        else:
            print(f"ERROR: MISSING MODELS CONFIG FILE: '{MODELS_CFG_FILENAME}'")
        for q in models_to_search:
            results = get_hf_search_query(**q)
            for r in results:
                if r.get('pipeline_tag') == 'automatic-speech-recognition':
                    models[r['id']] = r
        models = sorted(models, key = lambda k: models[k].get('downloads', models[k].get('likes', 0)), reverse=True)
        return models
    
class Mascot(tk.Tk):
    def __init__(self, message):
        super().__init__()
        # Create popup window
        self.title("Transcriber message")
        self.overrideredirect(True)  # Remove window decorations
        # Set window transparency attributes (Windows only)
        if sys.platform.startswith("win"):
            self.wm_attributes("-transparentcolor", "#f0f0f0")
        elif sys.platform == "darwin":
            # On macOS Big Sur+ you can get a similar effect
            self.attributes("-transparent", True)
            self.configure(background='systemTransparent')
        else:
            # other platforms – do nothing special
            pass

        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        img = None
        # Load and scale the image
        if MASCOT_FILENAME.is_file:
            img = Image.open(MASCOT_FILENAME)
        else:
            img = Image.new('RGBA', (100, 100), (255, 0, 0, 0))
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
        canvas = tk.Canvas(self, width=img.width, height=img.height, highlightthickness=0)
        canvas.pack()
         
        # Display the image
        canvas.create_image(0, 0, anchor="nw", image=img_tk)
        self.image = img_tk  # Keep a reference
        
        # Overlay text
        text_label = tk.Label(self, text=message, font=(DEFAULT_FONT, 16, "bold"),
                          fg="black", bg="white", wraplength=img.width - 20)
        text_label.place(anchor=CENTER, y=(img.height // 3) * 2, x = img.width//2, width=img.width - 20)
        
        # Center popup on screen
        x_position = (screen_width - img.width) // 2
        y_position = (screen_height - img.height) // 2
        self.geometry(f"+{x_position}+{y_position}")

        self.deiconify()
        self.wm_protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_visibility()
        
    
    

if __name__ == "__main__":
    # Make per user config files
    MODELS_CFG_FILENAME = Path(MODELS_CFG_FILENAME).expanduser()
    CACHE_FILENAME = Path(CACHE_FILENAME).expanduser()
    
    if not MODELS_CFG_FILENAME.exists():
        MODELS_CFG_FILENAME.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy(MODELS_CFG_DEFAULT, MODELS_CFG_FILENAME)
    if not CACHE_FILENAME.exists():
        CACHE_FILENAME.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy(CACHE_DEFAULT, CACHE_FILENAME)
    

    app = App()
    app.mainloop()
