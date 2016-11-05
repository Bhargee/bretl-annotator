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

from kivy.graphics import Color, Line, Point
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
        self.image_list = self._get_files()
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.im_idx = 0
        self.progress = ("%s/%s" % (self.im_idx+1, len(self.image_list)) )

        if exists(options.output_file):
            with open(options.output_file, 'r') as old_annotations:
                exit(3)
                self.annotations = json.load(old_annotations)
        else:
            self.annotations = dict()

        super(ImageDisplay, self).__init__(**kwargs)
        self._load_old_annotation()

    def _get_files(self):
        filenames = sorted(glob(join(options.imdir, '*.png')))
        return filenames

    def _keyboard_closed(self):
        pass
        #self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        #self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        # only deal with arrow keys
        if keycode[1] != "left" and keycode[1] != "right":
            return

        # don't walk off either end of list of images
        if self.im_idx == 0 and keycode[1] == 'left':
            return
        elif self.im_idx == len(self.image_list)-1 and keycode[1] == 'right':
            return

        # save current annotations
        self.record_annotation()
        self.save_annotations()

        # change index
        if keycode[1] == 'left':
            self.im_idx -= 1
        elif keycode[1] == 'right':
            self.im_idx += 1

        # update progress
        self.progress = "%s/%s" % (self.im_idx+1, len(self.image_list))

        # if previously annotated, load old annotations
        self._load_old_annotation()
        # display new image
        self.ids.curr_image.source = self.curr_image()

    def curr_image(self):
        return self.image_list[self.im_idx]

    def record_annotation(self):
        im_name = basename(self.ids.curr_image.source)
        self.annotations[im_name] = self.ids.curr_image.quad_points()

    def save_annotations(self):
        with open(options.output_file, 'w') as outfile:
            annotation_str = '\n'.join(['%s-%s'%(name, str(points)[1:-1]) for
                                name, points in self.annotations.iteritems()])
            outfile.write(annotation_str)

    def _load_old_annotation(self, filename):
        with open(filename, 'r') as old_anno:
            pass

class QuadDrawer(Image):
    def __init__(self, **kwargs):
        super(QuadDrawer, self).__init__(**kwargs)
        self.points = []
    
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        if len(self.points) == 4:
            return
        with self.canvas:
            Color(0,0,0)
            self.points.append((touch.x, touch.y))
            Point(points=(touch.x, touch.y), pointsize=6)
    def quad_points(self):
        # returns flattened list of points
        return list(sum(self.points, ()))

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
