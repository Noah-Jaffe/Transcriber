from src.Gui import MainGUI
from src.Utils import setup_local_user_cfgs

if __name__ == "__main__":
    setup_local_user_cfgs()
    app = MainGUI()
    app.mainloop()