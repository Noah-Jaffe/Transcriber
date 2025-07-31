from tkinter import messagebox
import traceback
import tkinter as tk
from tkinter import ttk
from typing import List

from DataMapping import DataMapping
from Config import *
from Tooltip import ToolTip
import Utils


class MainGUI(tk.Tk):
    """Runtime config. Populated by cache"""
    data_config: DataMapping = DataMapping()
    auto_retry_failures: tk.BooleanVar = None
    debug_mode: tk.BooleanVar = None
    """Dynamic list of file entries to be updated during runtime. Populated by cache"""
    data_file_entries: List[tk.Frame] = []
    
    """Main header section"""
    header_frame: tk.Frame = None
    """Button to add new files"""
    header_button_add_files: tk.Button = None
    """Label for button to add new files"""
    header_label_file_management: tk.Label = None
    
    """Main center section"""
    center_frame: tk.Frame = None
    """Canvas for the center frame"""
    center_canvas: tk.Canvas = None
    """Center frame for the scrollable/dynamic file list"""
    center_canvas_window: tk.Frame = None
    """Scrollbar for the file entries"""
    center_scrollbar_file_entries: tk.Scrollbar = None
    """Frame for the file entries inside the scrollable canvas window. Populated by cache"""
    center_frame_file_entries: tk.Frame = None
    
    """Main footer section"""
    footer_frame: tk.Frame = None
    """Combo box for model selection. Populated by cache"""
    footer_combobox_model_selector: ttk.Combobox = None
    """Button to find additional models"""
    footer_button_find_additional_models: tk.Button = None
    """Button to start transcribe"""
    footer_button_start_transcribe: tk.Button = None
    """Checkbox to retry failures. Populated by cache"""
    footer_checkbox_auto_retry_failures: ttk.Checkbutton = None
    """Checkbox for debug mode. Populated by cache"""
    footer_checkbox_debug_mode: ttk.Checkbutton = None
    
    def __init__(self):
        super().__init__()
        
        tk.Tk.report_callback_exception = self.show_error
        
        self.load_config()
        
        self.title("Transcriber")
        self.minsize(600, 300)
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.create_header()
        self.create_center()
        self.create_footer()
        
        self.bind("<Configure>", self.on_resize)
    
    def create_header(self):
        """Creates the header section contents and configures their layout.
            - title
            - select files button
            - @TODO: ADD FUTURE FEATURES HERE
        """
        # header root node
        self.header_frame = tk.Frame(self, bg=COLOR_THEME.MAIN_WINDOW)
        self.header_frame.grid(row=0, column=0, sticky="new")
        self.header_frame.grid_propagate(False)
        
        # file management - label
        self.header_label_file_management = tk.Label(self.header_frame, text="Files for transcription:", font=LABEL_FONT, bg=COLOR_THEME.MAIN_WINDOW, justify="right", anchor="ne")
        self.header_label_file_management.pack(side="left", padx=5, pady=5)
        ToolTip(self.header_label_file_management, text="Select the files to be transcribed!\nNote that we will handle file conversions!")
        
        # file management - add files
        self.header_button_add_files = tk.Button(self.header_frame, text="Select Files", command=self.select_files, background=COLOR_THEME.BUTTON)
        self.header_button_add_files.pack(side="right", padx=5, pady=5)
        ToolTip(self.header_button_add_files, text = "Select your file(s) to be transcribed. (Opens file selection window).")
    
    def create_center(self):
        """Creates the center section contents and configures their layout.
            - file selection and management
            - @TODO: ADD FUTURE FEATURES HERE
        """
        # center node
        self.center_frame = tk.Frame(self, bg=COLOR_THEME.MAIN_WINDOW)
        self.center_frame.grid(row=1, column=0, sticky="nsew")
        
        # Scrollable canvas for dynamic list of files
        self.center_canvas = tk.Canvas(self.center_frame, borderwidth=0, background=COLOR_THEME.MAIN_WINDOW)
        self.center_frame_file_entries = tk.Frame(self.center_canvas, background=COLOR_THEME.MAIN_WINDOW)
        self.center_scrollbar_file_entries = tk.Scrollbar(self.center_frame, orient="vertical", command=self.center_canvas.yview, background=COLOR_THEME.BUTTON)
        self.center_canvas.configure(yscrollcommand=self.center_scrollbar_file_entries.set)
        
        self.center_scrollbar_file_entries.pack(side="right", fill="y")
        self.center_canvas.pack(side="left", fill="both", expand=True)
        
        self.center_canvas_window = self.center_canvas.create_window((0, 0), window=self.center_frame_file_entries, anchor="nw", tags="inner")
        
        self.center_canvas.bind("<Configure>", self.on_canvas_resize)
        self.center_frame_file_entries.bind("<Configure>", self.on_frame_configure)
        self.center_frame_file_entries.grid_columnconfigure(0, weight=1)
        
        # @TODO add cached files at some point? where? here or when we load cache?
        self.data_file_entries = self.data_file_entries or []
    
    def create_footer(self):
        """Creates the footer section contents and configures their layout.
            - model selection
            - start transcribe button
            - @TODO: ADD FUTURE FEATURES HERE
        """
        # footer frame root node
        self.footer_frame = tk.Frame(self, bg=COLOR_THEME.MAIN_WINDOW)
        self.footer_frame.grid(row=2, column=0, sticky="nsew")
        self.footer_frame.grid_propagate(False)
        
        # configure the height/widths of each module by weights, 1 = max fill, 0 = min fill.
        self.footer_frame.grid_rowconfigure(0, weight=1)    # model selection, max height allowed
        self.footer_frame.grid_rowconfigure(1, weight=1)    # options/config
        self.footer_frame.grid_rowconfigure(2, weight=1)    # start button, max height allowed
        self.footer_frame.grid_columnconfigure(0, weight=1) # max width allowed
        
        # model selection row
        model_selection_row = tk.Frame(self.footer_frame, background=COLOR_THEME.MAIN_WINDOW)
        model_selection_row.grid(row=0, column=0, sticky="ew")
        model_selection_row.grid_columnconfigure(0, weight=2)   # model select label
        model_selection_row.grid_columnconfigure(1, weight=6)   # model select dropdown
        model_selection_row.grid_columnconfigure(2, weight=2)   # model select search
        
        # model selection 
        self.footer_button_find_additional_models = tk.Button(model_selection_row, text="Find a different model", command=Utils.open_hf_search, font=BUTTON_FONT, bg=COLOR_THEME.BUTTON)
        self.footer_button_find_additional_models.pack(side="right", padx=(5, 10))
        
        # @TODO figure out how to dynamically set the min width of the dropdown so the text does not get cut off
        self.footer_label_select_model = tk.Label(model_selection_row, text="Select AI Model:", font=LABEL_FONT, bg=COLOR_THEME.MAIN_WINDOW)
        self.footer_label_select_model.pack(side="left", padx=(10, 5))
        # @TODO populate footer_stringvar_model_selection_value from cache.modelCache
        self.footer_stringvar_model_selection_value = tk.StringVar()
        self.footer_combobox_model_selector = ttk.Combobox(model_selection_row, values=self.data_config.models, textvariable=self.footer_stringvar_model_selection_value)
        self.footer_combobox_model_selector.pack(fill="both", padx=(10, 10), pady=5)
        model_help_text = "\n".join([
            'Models can be set from any valid huggingface model.', 
            'Reccomended to use one of the following:', 
            'From batchalign:', 
            "    - 'talkbank/CHATWhisper-en'", 
            '', 
            'From OpenAI:', 
            '    * Choose the size that runs well on your computer.', 
            "    'openai/whisper-<TYPE>'", 
            '    Where you replace <TYPE> with the selected model. ', 
            "    For example, if you want the English only tiny type, then the value should be 'openai/whisper-tiny.en'.", 
            '    ╔════════╦══════════════╦══════════╦══════════╗', 
            '    ║        ║ English-only ║ Required ║ Relative ║', 
            '    ║  TYPE  ║     TYPE     ║   VRAM   ║  speed   ║', 
            '    ╠════════╬══════════════╬══════════╬══════════╣', 
            '    ║ tiny   ║   tiny.en    ║   ~1 GB  ║   ~10x   ║', 
            '    ║ base   ║   base.en    ║   ~1 GB  ║    ~7x   ║', 
            '    ║ small  ║   small.en   ║   ~2 GB  ║    ~4x   ║', 
            '    ║ medium ║   medium.en  ║   ~5 GB  ║    ~2x   ║', 
            '    ║ large  ║   N/A        ║  ~10 GB  ║     1x   ║', 
            '    ║ turbo  ║   N/A        ║   ~6 GB  ║    ~8x   ║', 
            '    ╚════════╩══════════════╩══════════╩══════════╝', 
            '', 
            'From other providers:', 
            '    Use the search button and find a model that you wish to use from huggingface.', 
            "    Enter the model ID to use as '<AUTHOR>/<NAME>' (the same pattern as the talkbank and openai models).", 
            '    Note that not all models will be valid, and you will only find out when it crashes when it attempts to transcribe.', 
            '    Use a model that is based off of the Openai whisper base!', 
            '', 
            'See the README.md file for more info!'
        ])
        ToolTip(self.footer_combobox_model_selector, text=model_help_text)
        ToolTip(self.footer_label_select_model, text=model_help_text)
        
        # Options/config row
        options_config_row = tk.Frame(self.footer_frame, background=COLOR_THEME.MAIN_WINDOW)
        options_config_row.grid(row=1, column=0, sticky="NEW", padx=10)
        
        # Auto-retry on failures
        # @TODO populate auto_retry_failures from cache.autoRetryFailuresMode
        self.auto_retry_failures = tk.BooleanVar(value=False)
        self.footer_checkbox_auto_retry_failures = ttk.Checkbutton(options_config_row, text="Auto-retry failures", variable=self.auto_retry_failures)
        self.footer_checkbox_auto_retry_failures.pack(side="left", padx=5)
        ToolTip(self.footer_checkbox_auto_retry_failures, text="Some errors caused by the AI have some known potential work-arounds. Selecting this will enable us to retry a transcription attempt if we know of a potential work-around for the issue encountered.")
        
        # Print debug/status lines (ENABLED BY DEFAULT)
        # @TODO populate debug_mode from cache.debugMode
        self.debug_mode = tk.BooleanVar(value=True)
        self.footer_checkbox_debug_mode = ttk.Checkbutton(options_config_row, text="Debug mode", variable=self.debug_mode)
        self.footer_checkbox_debug_mode.pack(side="left", padx=5)
        ToolTip(self.footer_checkbox_debug_mode, text="Sometimes knowing what went right or wrong can help with troubleshooting or validating the transcription. Selecting this will add '@DEBUG' lines to the bottom of the output transcript. Information in the @DEBUG lines may include:\n" + "\n".join([f"\t- {x}" for x in ["Help messages", "Status of each step of the pipeline", "Error messages", "Crash logs", "etc."]]))
        
        
        # Activity buttons row
        activity_button_row = tk.Frame(self.footer_frame, background=COLOR_THEME.MAIN_WINDOW)
        activity_button_row.grid(row=2, column=0, sticky="EWS", padx=10)
        
        # Start transcribe button
        self.footer_button_start_transcribe = tk.Button(activity_button_row, text="Start Transcribe", command=self.start_transcribe, font=BUTTON_FONT, bg=COLOR_THEME.BUTTON)
        self.footer_button_start_transcribe.pack(side="right")
        ToolTip(self.footer_button_start_transcribe, text="Click here to start transcribing the files in the list!\nNote: If the transcription seems off, try running it again! Its possible the AI gets different results each time.")
    
    def add_file_row(self, filepath="demo/path/file.mp3"):
        row = tk.Frame(self.center_frame_file_entries)
        row.pack(fill="x", expand=True, padx=5, pady=3)
        
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)
        row.grid_columnconfigure(2, weight=0)
        row.grid_columnconfigure(3, weight=0)
        
        label = tk.Label(row, text=f"{filepath}\ntranscribe info", justify="right", anchor="e")
        label.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        spin = tk.Spinbox(row, from_=1, to=99, width=6)
        spin.grid(row=0, column=1, padx=4)
        
        btn1 = tk.Button(row, text="Lang", width=6)
        btn1.grid(row=0, column=2, padx=2)
        
        btn2 = tk.Button(row, text="Del", width=6, command=lambda r=row: self.remove_row(r))
        btn2.grid(row=0, column=3, padx=2)
        
        self.data_file_entries.append(row)
    
    def remove_row(self, row):
        row.destroy()
        self.data_file_entries.remove(row)
    
    def select_files(self):
        # Placeholder for file dialog logic
        self.add_file_row("/path/to/newfile.wav")
    
    def on_resize(self, event):
        win_h = self.winfo_height()
        header_h = min(max(40, int(0.1 * win_h)), 100)
        center_h = min(max(200, int(0.7 * win_h)), int(0.7 * win_h))
        footer_h = min(max(80, int(0.2 * win_h)), int(0.2 * win_h))
        
        self.header_frame.config(height=header_h)
        self.footer_frame.config(height=footer_h)
    
    def on_frame_configure(self, event):
        self.center_canvas.configure(scrollregion=self.center_canvas.bbox("all"))
    
    def on_canvas_resize(self, event):
        self.center_canvas.itemconfig("inner", width=event.width)
    
    def show_error(self, *args):
        """Display the error to the user as a popup window"""
        err = traceback.format_exception(*args)
        print("\n".join(err), flush=True)
        messagebox.showerror("Error!", '\n'.join([str(a) for a in args[1].args]) + "\n\n\n\nPlease see the console for the full error message!")
    
    def load_config(self):
        """Loads and imports data from the config cache file to save time."""
        self.data_config.models = ['listofmodels1','listofmodels2','listofmodels3']
        print("@todo implement me")
    
    def start_transcribe(self):
        """Starts the transcribe process in the background
        
        Returns: 
            : @todo: pipe?
        """
        pass
        # self.update_cache()
        # if not is_valid_model_id(self.dropdown_model_selector.get()):
        #     if not spawn_popup_activity("Error!", f"An issue occured when we attempted to get the\n\n{self.dropdown_model_selector.get()}\n\nmodel. Please verify your huggingface token allows for read permissions of the given model.\n\nYes to continue with default model, no to abort!"):
        #         return
        
        # selected_model = self.dropdown_selection_value.get()
        # if len(SelectedFileConfigElement.MANAGER) == 0:
        #     raise Exception("Please select a file to transcribe first!")
        
        # mascot = self.show_mascot("IM TRANSCRIIIIBINNNG!!\nTRANSCRIPTION STARTED, DONT CLICK THE START TRANSCRIBE BUTTON AGAIN UNLESS YOU WANT MULTIPLE TRANSCRIPTIONS RUNNING FOR THE SELECTED FILES AT THE SAME TIME!")
        # for item in SelectedFileConfigElement.MANAGER:
        #     valid = validate_language(item.get_lang())
        #     if valid is None:
        #         spawn_popup_activity('WARNING!','Transcript process DID NOT START.\nPlease fix the errors and try again.')
        #         return
        # start = time()
        # parsetime = 0
        # twords = 0
        # runtime = datetime.timedelta(0)
        # for item in SelectedFileConfigElement.MANAGER:
        #     # needs conversion?
        #     if not (item.get_file().split('.')[-1] in get_audio_file_types()):
        #         # looks like it probably needs conversion
        #         ntype = ".mp3"
        #         print(f"Converting {item.get_file()} to mp3 type so that it can be transcribed!")
        #         item.filepath = convert_file_to_type(item.get_file(), ntype)
        #         print(f"Convertion completed! Audio file can be found {item.get_file()}")
            
        #     # priority_levels = [
        #     #     psutil.NORMAL_PRIORITY_CLASS, # normal,
        #     #     psutil.ABOVE_NORMAL_PRIORITY_CLASS, # above normal
        #     #     psutil.ABOVE_NORMAL_PRIORITY_CLASS, # above normal
        #     #     psutil.HIGH_PRIORITY_CLASS, # high priority
        #     # ]
        #     # priority_points = 0
        #     # curr_state = psutil.virtual_memory()
        #     # if (curr_state.total/(2**30) > 16):
        #     #     # 16gb+ ram
        #     #     priority_points += 1
        #     # if (is_cuda_available()):
        #     #     # has cuda
        #     #     priority_points += 1
        #     #     if (get_cuda_mem_info()[1]/(2**30) > 10):
        #     #         # has big cuda
        #     #         priority_points += 1
        #     pstart = datetime.datetime.now()
        #     d = soundfile.info(item.get_file()).duration
        #     print(f"Starting timer for ({d}) '{item.get_file()}'")
        #     proc = subprocess.Popen(
        #         args=[
        #             sys.executable,
        #             TRANSCRIBE_SUBPROC_FILENAME,
        #             json.dumps({
        #                 'input_file': item.get_file(), 
        #                 'num_speakers': item.get_speakers(), 
        #                 'lang': item.get_lang(), 
        #                 'model_name':selected_model
        #                 },
        #                 skipkeys=True, 
        #                 separators=(',', ':'))
        #             ],
        #             cwd=os.getcwd(),
        #             start_new_session=True
        #         )
        #     # psutil.Process(proc.pid).nice(priority_levels[priority_points])
        #     self.title("Transcriber - PLEASE DONT KILL ME - I AM WORKING! I PROMISE!")
        #     while proc.poll() == None:
        #         try:
        #             self.update_idletasks()
        #             sleep(0.1)
        #             #proc.wait(timeout=1)
        #         except:
        #             pass
        #     ptime = datetime.datetime.now() - pstart
        #     runtime += ptime
        #     parsetime += d
        #     estwordcount = f"{item.get_file()}.cha"
        #     est_word_count = 0
        #     if os.path.isfile(estwordcount):
        #         with open(estwordcount, 'r', encoding='utf-8') as f:
        #             est_word_count = sum([len([w for w in re.sub(r"^\*\w+:\s*(.*?)\s*\.\s*$", "\\1", l, count=0, flags=re.MULTILINE | re.IGNORECASE).replace(r'\s*[/]\s*',' ').split()]) for l in f.readlines() if re.match(r'^\*\w+:\s*(.*?)\s*\.\s*(?:\u0015.*?\u0015)?\s*$', l, re.MULTILINE|re.IGNORECASE)])
        #     print(f"Took {ptime} to transcribe ~{est_word_count} words from ({soundfile.info(item.get_file()).duration}) '{item.get_file()}' using {selected_model}")
        # try:
        #     mascot.destroy()
        # except:
        #     pass
        # self.title("Transcriber")
        # # spawn_popup_activity("Transcriber", "Completed transcribing the files!")
        # print("Completed transcribing the latest batch!")
        # print(f"Took {runtime} to transcribe ~{twords} words from ({parsetime}) across {len(SelectedFileConfigElement.MANAGER)} files!")
    
if __name__ == "__main__":
    from Utils import setup_local_user_cfgs
    setup_local_user_cfgs()
    app = MainGUI()
    app.mainloop()
