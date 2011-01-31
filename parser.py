#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tomato.parser  - parser for SwfBlock(s)

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
from structure import *
from utils import le2byte, le4byte


SWF_TAG = {
    0:  End,
    1:  ShowFrame,
    2:  DefineShape,
    6:  DefineBits,
    8:  JPEGTables,
    9:  SetBackgroundColor,
    11: DefineText,
    12: DoAction,
    14: DefineSound,
    20: DefineBitsLossless,
    21: DefineBitsJPEG2,
    22: DefineShape2,
    26: PlaceObject2,
    28: RemoveObject2,
    32: DefineShape3,
    34: DefineButton2,
    35: DefineBitsJPEG3,
    36: DefineBitsLossless2,
    37: DefineEditText,
    39: DefineSprite,
    43: FrameLabel,
    45: SoundStreamHead2,
    46: DefineMorphShape,
    48: DefineFont2,
    88: DefineFontName,
    }


class SwfBlockParser(object):
    def __init__(self, value, base_block=None, swf=None):
        "Parse/Split blocks."
        self.offset = 0
        self.value = value
        self.base_block = base_block
        self.swf = swf

        self.blocks = []
        block = self.parse_swfblock()
        while True:
            self.blocks.append(block)
            if block.tag == 0:
                break
            block = self.parse_swfblock()

    def parse_swfblock(self):
        block_start = self.offset
        tag = le2byte(self.read(2))
        block_len = tag & 0x3f
        if block_len == 0x3f:
            block_len = le4byte(self.read(4))
        tag = tag >> 6

        content_offset = self.offset - block_start
        self.offset += block_len

        args = [
            tag,
            block_len,
            content_offset,
            self.value[block_start:self.offset],
            self.base_block,
            self.swf]

        if tag in SWF_TAG:
            return SWF_TAG[tag](*args)
        else:
            return SwfBlock(*args)

    def read(self, num):
        "num byte(s) ずつ swf を読み出す"
        self.offset += num
        return self.value[self.offset - num: self.offset]


def deserialize_blocks(blocks_tpl, serializer_version, swf=None, base_block=None):
    blocks = []
    for tpl in blocks_tpl:
        s = SWF_TAG[tpl[0]](tpl[0], tpl[1], tpl[2], tpl[3], base_block, swf, False)
        if len(tpl) > 4:
            s.deserialize(serializer_version, tpl[4:])
        blocks.append(s)
    return blocks

