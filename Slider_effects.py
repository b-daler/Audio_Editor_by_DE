import tkinter as tk
class Slider_effects(tk.Canvas):
    SLIDER_SIZE = 13
    PROGRESS_HEIGHT = 6

    def __init__(self, master, length, initial_position=0):
        super().__init__(
            master, width=length, height=self.SLIDER_SIZE,
            bg='#585050', bd=0, highlightthickness=0, highlightbackground='#585050'
        )
        self.length = length
        self.slider = None
        self.progress_bar = None
        self.slider_position = 0
        self.bind('<Enter>', self.show_slider)
        self.bind('<Leave>', self.hide_slider)
        self.bind('<Button-1>', self.on_click)
        self.bind('<B1-Motion>', self.on_drag)

        self.configure(borderwidth=0)
        self.set_position(initial_position)
        self.hide_slider(None)
    def set_position(self, position):
        position = min(position, self.length - self.SLIDER_SIZE)  # Ограничиваем позицию максимальным значением
        if not 0 <= position <= self.length - self.SLIDER_SIZE:
            raise ValueError(f"Недопустимая позиция слайдера: {position}")

        progress_y = (self.SLIDER_SIZE - self.PROGRESS_HEIGHT) / 2
        if position == 0:
            if self.progress_bar:
                self.delete(self.progress_bar)
                self.progress_bar = None
        else:
            if not self.progress_bar:
                self.progress_bar = self.create_rectangle(
                    0, progress_y, position, progress_y + self.PROGRESS_HEIGHT,
                    fill='white', outline='white', width=0, tags='progress'
                )
            else:
                self.coords(
                    self.progress_bar, 0, progress_y, position,
                    progress_y + self.PROGRESS_HEIGHT
                )
        if not self.slider:
            self.slider = self.create_oval(
                0, 0, self.SLIDER_SIZE, self.SLIDER_SIZE, fill='gray', outline='gray'
            )
        self.coords(
            self.slider, position, 0, position + self.SLIDER_SIZE, self.SLIDER_SIZE
        )
        self.slider_position = position
    def get_position(self):
        return self.slider_position

    def show_slider(self, event):
        self.itemconfigure(self.slider, state='normal')
        self.itemconfigure(self.progress_bar, fill='black', outline='black')

    def hide_slider(self, event):
        self.itemconfigure(self.slider, state='hidden')
        if self.progress_bar:
            self.itemconfigure(self.progress_bar, fill='white', outline='white')

    def on_click(self, event):
        x = event.x - self.SLIDER_SIZE / 2
        if x < 0:
            x = 0
        elif x > self.length - self.SLIDER_SIZE:
            x = self.length - self.SLIDER_SIZE

        if 0 <= x <= self.length - self.SLIDER_SIZE:
            self.set_position(x)


    def on_drag(self, event):
        x = event.x - self.SLIDER_SIZE / 2
        if x < 0:
            x = 0
        elif x > self.length - self.SLIDER_SIZE:
            x = self.length - self.SLIDER_SIZE

        if 0 <= x <= self.length - self.SLIDER_SIZE:
            self.set_position(x)
            self.show_slider(None)

if __name__ == '__main__':
    root = tk.Tk()
    track_length = 300
    root.geometry("1300x700")
    slider = Slider_effects(root, track_length)
    slider.pack(expand=True)
    root.mainloop()
