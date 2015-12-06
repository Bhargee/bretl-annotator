#!/usr/bin/python

import kivy
kivy.require('1.9.0')

from kivy.app import App

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

from kivy.graphics import Color, Line

from kivy.properties import ListProperty, NumericProperty

from kivy.core.window import Window

import sys
from optparse import OptionParser
from glob import glob
from os.path import join

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

class ImageDisplay(Widget):

    def __init__(self, **kwargs):
        self.image_list = self._get_files()
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.im_idx = 0
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

        self.ids.left_image.source = self.left_image()
        self.ids.right_image.source = self.right_image()
        self.ids.depth_image.source = self.depth_image()

    def left_image(self):
        return self.image_list[(self.im_idx*3)+1]
    def right_image(self):
        return self.image_list[(self.im_idx*3)+2]
    def depth_image(self):
        return self.image_list[self.im_idx*3]

class BorderDrawer(Image):
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return

        with self.canvas:
            Color(1,1,0)
            touch.ud['line'] = Line(points=(touch.x,touch.y))

    def on_touch_move(self, touch):
        if not self.collide_point(*touch.pos):
            return
        touch.ud['line'].points += [touch.x, touch.y]
 
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
