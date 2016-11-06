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

from kivy.graphics import Color, Line, Ellipse
from kivy.graphics.instructions import InstructionGroup

from kivy.properties import NumericProperty, StringProperty

from kivy.core.window import Window

# for exiting, parsing cmd args, and creating imdir/outputdir structures
import sys
from optparse import OptionParser
from glob import glob
from os.path import join, exists, basename
import json

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
        imd = ImageDisplay()
        self.root.add_widget(imd)
        self.icon = 'hand-icon.png'

class ImageDisplay(Widget):
    progress = StringProperty()

    def __init__(self, **kwargs):
        self.image_list = self._get_files() # collect all image files
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.im_idx = 0
        self.progress = ("%s/%s" % (self.im_idx+1, len(self.image_list)) )

        self.annotations = dict()
        if exists(options.output_file):
            self.annotations = self.load_old_annotations()

        super(ImageDisplay, self).__init__(**kwargs)

        first_image = basename(self.curr_image())
        if first_image in self.annotations.keys():
            self.ids.curr_image.reset(self.annotations[first_image])


    def _get_files(self):
        filenames = sorted(glob(join(options.imdir, '*')))
        return filenames

    def _keyboard_closed(self):
        pass

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == "e":
            for _ in range(2):
                self.ids.curr_image.points.pop()
        self.ids.curr_image.reset(self.ids.curr_image.points)


        if keycode[1] != "left" and keycode[1] != "right":
            return

        # don't walk off either end of list of images
        if self.im_idx == 0 and keycode[1] == 'left':
            return
        elif self.im_idx == len(self.image_list)-1 and keycode[1] == 'right':
            return

        # add annotation to data structure (save when hitting 'save
        # annotations')
        self.record_annotation()

        # change index
        if keycode[1] == 'left':
            self.im_idx -= 1
        elif keycode[1] == 'right':
            self.im_idx += 1

        # update progress
        self.progress = "%s/%s" % (self.im_idx+1, len(self.image_list))

        # display new image
        self.ids.curr_image.source = self.curr_image()
        next_image = basename(self.ids.curr_image.source)
        if next_image in self.annotations.keys():
            self.ids.curr_image.reset(self.annotations[next_image])
        else:
            self.ids.curr_image.reset([])

    def curr_image(self):
        return self.image_list[self.im_idx]

    def record_annotation(self):
        im_name = basename(self.ids.curr_image.source)
        self.annotations[im_name] = self.ids.curr_image.points

    def save_annotations(self):
        with open(options.output_file, 'w') as outfile:
            full_annotations = filter(
                    lambda (name, points): len(points) > 0,
                    self.annotations.iteritems())
            annotation_str = '\n'.join(['%s-%s'%(name, str(points)[1:-1]) for
                                name, points in full_annotations])
            outfile.write(annotation_str)

    def load_old_annotations(self):
        annotations = {}
        with open(options.output_file, 'r') as old_anno:
            lines = old_anno.readlines()
            for line in lines:
                name, coords = line.split('-')
                annotations[name] = map(lambda c: float(c), coords.split(','))
        return annotations

class QuadDrawer(Image):
    def __init__(self, **kwargs):
        super(QuadDrawer, self).__init__(**kwargs)
        self.points = []
        self.canvas_points = []
        self.d = 10
    
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        if len(self.points) == 8:
            return
        new_points = [touch.x, touch.y]
        self.points.extend(new_points)
        self._display(new_points)

    def quad_point_annotations(self):
        return str(self.points)[1:-1]

    def reset(self, p):
        self.points = p
        for cp in self.canvas_points:
            self.canvas.remove(cp)
        self.canvas_points = []
        if len(p) > 0:
            self._display(self.points)

    def _display(self, points):
        with self.canvas:
            Color(0,0,0)
            for i in range(0, len(points)-1,2):
                x,y = points[i], points[i+1]
                e = Ellipse(pos=(x-self.d/2,y-self.d/2), 
                                             size=(self.d, self.d))
                self.canvas_points.append(e)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--imdir', '-i', dest='imdir',
            help='location of images')
    parser.add_option('--output-file', '-o', dest='output_file',
            help='path for output file')

    (options, args) = parser.parse_args()
    if options.imdir is None or options.output_file is None:
        print 'Must start with image directory and output directory args'
        sys.exit(1)
    if options.imdir[-1] is not '/':
        options.imdir += '/'

    AnnotatorApp().run()
