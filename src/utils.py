# SharedState.py
import tkinter as tk

class SharedState:
    def __init__(self, master):
        self.is_playing = True
        self.current_frame_number = 0

        self.status_frame = tk.Frame(master)
        self.status_frame.pack(side=tk.TOP, fill=tk.X)

        self.play_pause_button = tk.Button(self.status_frame, text="Pause", command=self.toggle_play_pause)
        self.play_pause_button.pack(side="left")

        self.forward_button = tk.Button(self.status_frame, text="Forward", command=self.fast_forward)
        self.forward_button.pack(side="left")

        self.slider = tk.Scale(self.status_frame, from_=0, to=100, orient="horizontal", command=self.on_slider_move)
        self.slider.pack(side="left")

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_pause_button.config(text="Pause")
        else:
            self.play_pause_button.config(text="Play")

    def fast_forward(self):
        self.current_frame_number += 10

    def on_slider_move(self, value):
        self.current_frame_number = int(value)

# import os
# import tkinter as tk
# from tkinter import ttk
#
# def open_file_location(file_path):
#     os.system(f'explorer /select,"{file_path}"')
#
# root = tk.Tk()
# frame = ttk.Frame(root)
# frame.pack(fill='both', expand=1)
#
# tree = ttk.Treeview(frame, columns=('Input Video', 'Calibration File', 'Corrected Video'), show='headings')
# tree.heading('Input Video', text='Input Video')
# tree.heading('Calibration File', text='Calibration File')
# tree.heading('Corrected Video', text='Corrected Video')
#
# tree.tag_configure('oddrow', background='orange')
# tree.tag_configure('evenrow', background='purple')
#
# data = {
#     'Input Video': [r'C:\Users\sadebayo\Documents\Blog\Caibration-Test\CorrectedVideos', 'video2.mp4'],
#     'Calibration File': ['calib1.npz', 'calib2.npz'],
#     'Corrected Video': ['corrected1.mp4', 'corrected2.mp4'],
# }
#
# for i in range(len(data['Input Video'])):
#     tag = 'oddrow' if i % 2 else 'evenrow'
#     tree.insert('', i, values=(data['Input Video'][i], data['Calibration File'][i], data['Corrected Video'][i]), tags=(tag,))
#
# tree.pack(expand=1, fill='both')
#
# tree.bind("<Double-1>", lambda event: open_file_location(tree.item(tree.selection())['values'][0]))
#
# root.mainloop()

