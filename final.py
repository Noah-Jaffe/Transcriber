import os
import tkinter as tk
from tkinter import BOTH, CENTER, LEFT, SOLID, TOP, X, Button, IntVar, Label, Spinbox, StringVar, Tk, Toplevel, filedialog, Frame
from tkinter.font import BOLD, ITALIC, NORMAL
from tkinter.ttk import Combobox
import tkinter.messagebox as tkMessageBox
from typing import Dict, List
import whisper
import subprocess
import traceback


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

def todo_start_transcribe():
    raise Exception('not implemented!')
    pass

LABEL_FONT = ("Arial", 12, BOLD)
BUTTON_FONT = ("Arial", 12, NORMAL)
FILE_NAME_FONT = ("Consolas", 10, NORMAL)
TOOLTIP_FONT = ("Consolas", 8, NORMAL)

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
        
        # file management - label
        self.label_file_management = Label(self.root, text="Files for transcription", font=LABEL_FONT)
        self.label_file_management.pack(padx=5, pady=3, side=TOP)
        ToolTip(self.label_file_management, text="Select the files to be transcribed!\nNote that we will handle file conversions!")
        
        # file management - list area
        self.frame_file_management_list = Frame(self.root)
        self.frame_file_management_list.pack(fill=BOTH, expand=True)
        
        # file management - add files
        # @TODO: should the first element be self.root or the self.frame_file_management_list?
        self.button_add_files = Button(self.frame_file_management_list, text="Select Files", command=self.select_new_files, font=BUTTON_FONT)
        self.button_add_files.pack(padx=5, pady=3)
        ToolTip(self.button_add_files, text = "Select multiple files to be transcribed. (Opens file selection window).")
        
        # model selection
        self.label_select_model = Label(self.root, text="Select AI Model:", font=LABEL_FONT)
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
        self.button_start_transcribe = Button(self.root, text="Start Transcribe", command=self.todo_start_transcribe, font=BUTTON_FONT)
        self.button_start_transcribe.pack(pady=5)
        ToolTip(self.button_start_transcribe, text="Click here to start transcribing the files in the list!\nNote: If the transcription seems off, try running it again! Its possible the AI gets different results each time.")
    
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
    
    def todo_start_transcribe(self):
        """Starts the transcribe process in the background

        Returns: 
            : @todo: pipe?
        """
        todo_list = [{'fp': e.get_file(), 'ns': e.get_speakers(), 'lang': e.get_lang()} for e in SelectedFileConfigElement.MANAGER]
        selected_model = self.dropdown_selection_value.get()
        if len(todo_list) == 0:
            raise Exception("Please select a file to transcribe first!")
        print('Using model:', selected_model)
        for item in todo_list:
            print(item)
    
    def show_error(self, *args):
        """Display the error to the user as a popup window"""
        err = traceback.format_exception(*args)
        print("\n".join(err))
        tkMessageBox.showerror("Error!", f"{'\n'.join(args[1].args)}\n\n\n\nPlease see the console for the full error message!")
    

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
        
        SelectedFileConfigElement.MANAGER.append(self)
    
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


if __name__ == "__main__":
    root = tk.Tk()
    app = MainGUI(root=root)
    root.mainloop()
