#!/usr/bin/env python3
"""
sprite_animator.py

A Tkinter Label that displays a single “sad” PNG, or cycles through
multiple “happy” PNGs at a given interval.  You can pass an optional
size=(width, height) to scale all frames.
"""
import tkinter as tk
from PIL import Image, ImageTk

class SpriteAnimator(tk.Label):
    def __init__(
        self,
        master,
        sad_path: str,
        happy_paths: list[str],
        interval: int = 400,
        size: tuple[int, int] | None = None,
        **kwargs
    ):
        """
        :param master:      parent widget
        :param sad_path:    path to the single “sad” image
        :param happy_paths: list of paths to the “happy” frames
        :param interval:    milliseconds between happy-frame swaps
        :param size:        optional (width, height) to resize all frames
        :param kwargs:      extra tk.Label kwargs (e.g. bg, bd, etc.)
        """
        super().__init__(master, **kwargs)
        self.interval = interval
        self.size     = size  # store for use in loader

        # pick the best LANCZOS filter available
        try:
            resample_filter = Image.Resampling.LANCZOS  # Pillow ≥9.1
        except AttributeError:
            # older Pillow uses Image.LANCZOS
            resample_filter = getattr(Image, "LANCZOS", Image.BICUBIC)

        def load(path: str) -> Image.Image:
            img = Image.open(path)
            if self.size:
                img = img.resize(self.size, resample_filter)
            return img

        # load all PIL images
        self._sad_img_pil    = load(sad_path)
        self._happy_imgs_pil = [load(p) for p in happy_paths]

        # convert to PhotoImage only once
        self._sad_photo    = ImageTk.PhotoImage(self._sad_img_pil)
        self._happy_photos = [ImageTk.PhotoImage(img) for img in self._happy_imgs_pil]

        # initial state: show sad
        self.config(image=self._sad_photo)
        self._animating = False
        self._current   = 0

    def start_animation(self):
        """Start cycling through the happy frames."""
        if not self._animating:
            self._animating = True
            self._animate()

    def stop_animation(self):
        """Alias to revert to sad image."""
        self.show_sad()

    def _animate(self):
        if not self._animating:
            return
        # display next happy frame
        frame = self._happy_photos[self._current]
        self.config(image=frame)
        self._current = (self._current + 1) % len(self._happy_photos)
        self.after(self.interval, self._animate)

    def show_sad(self):
        """Stop the happy animation and show the sad image."""
        self._animating = False
        self.config(image=self._sad_photo)
        self._current = 0
