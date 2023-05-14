import tkinter as tk
from tkinter import ttk


class TabbedView(ttk.Notebook):
    def __init__(self, parent):
        super().__init__(parent)

        # Create tabs
        tab1 = ttk.Frame(self)
        tab2 = ttk.Frame(self)
        tab3 = ttk.Frame(self)

        # Add tabs to notebook
        self.add(tab1, text="Tab 1")
        self.add(tab2, text="Tab 2")
        self.add(tab3, text="Tab 3")

        # Add labels to tabs
        label1 = tk.Label(tab1, text="Tab 1 Content")
        label1.pack(pady=20, padx=20)

        label2 = tk.Label(tab2, text="Tab 2 Content")
        label2.pack(pady=20, padx=20)

        # Create buttons for tab3
        button_names = ["bt1", "bt2", "bt3", "bt4", "bt5"]
        self.buttons = []
        self.tabs = []
        for name in button_names:
            button = tk.Button(tab3, text=name, command=lambda name=name: self.show_tab(name))
            button.pack(side=tk.LEFT, padx=10, pady=10)
            self.buttons.append(button)

            subtabs = ttk.Notebook(tab3)
            for i in range(5):
                subtab = ttk.Frame(

                )
                subtabs.add(subtab, text="Subtab {}".format(i + 1))
                label = tk.Label(subtab, text="{} Content".format(name))
                label.pack(pady=20, padx=20)
            self.tabs.append(subtabs)

        # Show initial subtab
        self.show_tab(button_names[0])

    def show_tab(self, button_name):
        for i, name in enumerate(self.buttons):
            if button_name == name["text"]:
                self.buttons[i].config(relief=tk.SUNKEN)
                self.tabs[i].pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
                self.tabs[i].select(i)  # 버튼 순서에 해당하는 하위 탭으로 포커스 이동
            else:
                self.buttons[i].config(relief=tk.RAISED)
                self.tabs[i].pack_forget()


# Create the main window
root = tk.Tk()

# Create the tabbed view
tabbed_view = TabbedView(root)
tabbed_view.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

# Start the main event loop
root.mainloop()