#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tomato.swf_checker

--

MIT License

Copyright (C) 2011 by Takahiro Kamatani

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import sys
import os
from tomato.swf_processor import Swf
from structure import PlaceObject2, DefineSprite

class SwfDepthChecker(object):
    def __init__(self, swf, limit_depth):
        self.swf = swf
        self.layer_depth = {}    # MovieClip (DefineSprite) の深さ
        self.check_movie_clip_layer_depth()
        self.character_id_to_mc_name()
        self.print_depth(limit_depth)

    def print_depth(self, limit_depth):
        for name, depth in self.layer_depth.items():
            if depth >= limit_depth:
                if isinstance(name, int):
                    name = "ID: %d" % name
                prev = "Error: MovieClip : %s" % name
                prev = prev + (50 - len(prev)) * " "
                print "%s depth %d" % (prev, depth)

    def character_id_to_mc_name(self):
        for p in self.swf.search_tags("PlaceObject2"):
            if p.target_character_id in self.layer_depth:
                if hasattr(p, 'name'):
                    if p.name:
                        depth = self.layer_depth[p.target_character_id]
                        del self.layer_depth[p.target_character_id]
                        name = "ID: %d - \"%s\" " % (p.target_character_id, p.name)
                        self.layer_depth[name] = depth

    def check_movie_clip_layer_depth(self):
        for b in self.swf.blocks:
            if isinstance(b, DefineSprite):
                self.check_define_sprite_blocks(b)

    def check_define_sprite_blocks(self, define_sprite):
        if define_sprite.character_id not in self.layer_depth:
            self.layer_depth[define_sprite.character_id] = 1

        layer_depth = self.layer_depth[define_sprite.character_id]

        for b in define_sprite.blocks:
            if isinstance(b, PlaceObject2):
                if b.target_character_id in self.swf.character_dict:
                    c = self.swf.character_dict[b.target_character_id]
                    if isinstance(c, DefineSprite):
                        before_depth = layer_depth

                        if c.character_id not in self.layer_depth :
                            self.layer_depth[c.character_id] = 1
                        layer_depth = max(layer_depth, self.layer_depth[c.character_id] + 1)

                        if layer_depth > before_depth:
                            self.layer_depth[define_sprite.character_id] = layer_depth

        return layer_depth


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "usage: python swf_checker.py [input.swf] [limit_depth]"
    else:
        c = SwfDepthChecker(
            swf = Swf(open(sys.argv[1]).read()),
            limit_depth = int(sys.argv[2]))

