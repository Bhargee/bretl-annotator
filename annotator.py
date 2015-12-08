#!/usr/bin/python

import kivy
kivy.require('1.9.0')

from kivy.app import App

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox

from kivy.graphics import Color, Line
from kivy.graphics.instructions import InstructionGroup

from kivy.properties import ListProperty, NumericProperty

from kivy.core.window import Window

# for exiting, parsing cmd args, and creating imdir/oitputdir structures
import sys
from optparse import OptionParser
from glob import glob
from os.path import join

# for saving
import json
from itertools import izip_longest

class AnnotatorApp(App):
    def build(self):
        self.root = FloatLayout()

        box = BoxLayout(
                padding=10,
                spacing=10,
                size_hint=(1,None),
                pos_hint={'top':1},
                height=44)

        image = Image(
                size_hint=(None,None),
                size=(30,30),
                source='hand-icon.png')

        label = Label(
                height=24,
                text='Annotator')
        with label.canvas:
            Color(1,1,1,.8)

        box.add_widget(image)
        box.add_widget(label)
        self.root.add_widget(box)
        self.root.add_widget(ImageDisplay())
        self.icon = 'hand-icon.png'

class ImageDisplay(Widget):
    _instructions_text = ("Create a bounding box around the depth image to closely "
                          "bound the object, ignoring noise. Bounding boxes must be "
                         "created with a smooth movement. To delete a bad box, "
                         "simply click anywhere else in the depth image. After "
                         "selecting a grip, hit the right and left arrow keys to move on or see")


    def __init__(self, **kwargs):
        self.image_list = self._get_files()
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.im_idx = 0
        self.annotations = dict()
        super(ImageDisplay, self).__init__(**kwargs)

    def _get_files(self):
        filenames = sorted(glob(join(options.imdir, '*.jpg')))
        return filenames

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        # don't walk off either end of list of images
        if self.im_idx == 0 and keycode[1] == 'left':
            return
        elif self.im_idx == (len(self.image_list)/3)-1 and keycode[1] == 'right':
            return

        if keycode[1] == 'left':
            self.im_idx -= 1
        elif keycode[1] == 'right':
            self.im_idx += 1

        self.record_annotation()
        self.ids.left_image.source = self.left_image()
        self.ids.right_image.source = self.right_image()
        self.ids.depth_image.source = self.depth_image()
        self.ids.depth_image.clear_line()

    def left_image(self):
        return self.image_list[(self.im_idx*3)+1]
    def right_image(self):
        return self.image_list[(self.im_idx*3)+2]
    def depth_image(self):
        return self.image_list[self.im_idx*3]

    def record_annotation(self):
        curr_left_im = self.left_image()
        handle = curr_left_im[len(options.imdir):curr_left_im.rfind('_')]
        self.annotations[handle] = dict()

        grip = 'None'
        if self.ids.power.active:
            grip = 'power'
        elif self.ids.tool.active:
            grip = 'tool'
        elif self.ids.tjc.active:
            grip = '3 jaw chuck'
        elif self.ids.pinch.active:
            grip = 'pinch'
        elif self.ids.key.active:
            grip = 'key'
        self.annotations[handle]['grip'] = grip

        self.annotations[handle]['comment'] = self.ids.comments.text
        repeated_points = [iter(self.ids.depth_image.line_disp.points)] * 2
        grouped_points = izip_longest(fillvalue=None, *repeated_points)
        (xo, yo) = self.ids.depth_image.pos
        self.annotations[handle]['line'] = map(lambda (x,y): (x-xo, y-yo),
                                               grouped_points)

    def save_annotations(self):
        outfile_name = options.output_dir + 'annotations.json'
        with open(outfile_name, 'w') as outfile:
            json.dump(self.annotations, outfile)

class BorderDrawer(Image):
    # TODO compute local line coords for matlab
    def __init__(self, **kwargs):
        super(BorderDrawer, self).__init__(**kwargs)
        self.line_disp = Line()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        self.clear_line()
        self.canvas.add(self.line_disp)

    def on_touch_move(self, touch):
        if not self.collide_point(*touch.pos):
            return
        self.line_disp.points += [touch.x, touch.y]

    def clear_line(self):
        self.line_disp.points = []


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--imdir', '-i', dest='imdir',
            help='location of all duo left/right and depth map images')
    parser.add_option('--output-dir', '-o', dest='output_dir',
            help='location where app output files should go')

    (options, args) = parser.parse_args()
    if options.imdir is None or options.output_dir is None:
        print 'Must start with image directory and output directory args'
        sys.exit(1)
    if options.imdir[-1] is not '/':
        options.imdir += '/'
    if options.output_dir is not '/':
        options.output_dir += '/'

    AnnotatorApp().run()
