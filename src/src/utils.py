import webbrowser
from src.gui_element import GUI_ELEMENT

def open_web_page(event):
    webbrowser.open('http://github.com/exponentialR')


class PopulateTask:
    def __init__(self, params, app):
        self.params = params
        self.GUI = GUI_ELEMENT(app)
        self.input_frame = self.GUI.input_frame
        self.task_label = self.GUI.task_label
        self.label_style = self.GUI.label_style
        self.show_frame = self.GUI.show_frame

    def populate_form_with_params(self, params):
        if not hasattr(self, 'task_label'):
            self.task_label = tk.Label(self.input_frame, text="", font=("Verdana", 18, 'bold'), bg='#ADD8E6',
                                       fg='#000000')

        for widget in self.input_frame.winfo_children():
            widget.grid_forget()

        # Then repopulate
        self.task_label.grid(row=0, column=0, columnspan=3, pady=20, sticky="ew")
        n_rows = len(params)

        for i, (text, var, cmd, _) in enumerate(params):
            if not hasattr(self, 'label_style'):
                self.label_style = {'bg': '#ADD8E6', 'fg': '#000000', 'font': ('Courier New', 12)}
            label = tk.Label(self.input_frame, text=text, **self.label_style)
            label.grid(row=i + 1, column=0, sticky="w")

            if text == 'Dictionary:':
                cmd(i + 1, 1, 'dictionary_menu')
            elif text == "Display Video During Calibration?:":
                cmd(i + 1, 1, 'display_video_menu')
            elif text == 'Calibration Pattern Type:':
                cmd(i + 1, 1, 'pattern_type_menu')

            else:

                entry = ttk.Entry(self.input_frame, textvariable=var, width=40)
                entry.grid(row=i + 1, column=1)

                if cmd:
                    ttk.Button(self.input_frame, text="Browse", command=cmd).grid(row=i + 1, column=2)

        # Add the Start Task button
        self.start_task_button.grid(row=n_rows + 1, column=1, padx=5, pady=5)
        # Add a new Back button just for this frame
        ttk.Button(self.input_frame, text="Back", command=lambda: self.show_frame(self.start_frame)).grid(
            row=n_rows + 2, column=1, padx=5, pady=5)

    def populate_form_based_on_task(self, task):
        params_copy = [list(p) for p in self.params]

        if task == "Calibrate Only":
            for i, param in enumerate(params_copy):
                if param[0] == "Video Files (for correction):":
                    param[0] = "Video Files (for calibration):"
            self.populate_form_with_params(params_copy)

        elif task == "Correct Only":
            self.populate_form_with_params(params_copy[:7])  # Assuming first 7 are necessary

        elif task == "Self-Calibrate & Correct":
            self.populate_form_with_params(params_copy)

        elif task == "Single Calib and Multiple Video Correction":
            params_copy.append(["Single Video File:", self.single_video_file_var, self.browse_single_video_file, None])
            self.populate_form_with_params(params_copy)
            self.shift_down_widgets(start_row=4, shift_amount=1)

        elif task == "Generate Calibration Pattern":
            pattern_type = self.pattern_type_var.get()
            if pattern_type == 'Charuco':
                self.populate_pattern_form(self.charuco_exclusive_params)
            else:
                self.populate_pattern_form(self.checker_exclusive_params)
