# -*- coding: utf-8 -*-
"""
Tomato.swf_image_dumper
  Flash の画像抽出ツール(GIF, PNG, JPEG 対応版)
  必要ライブラリ: Python Imaging Library 1.1.7

--

MIT License

Copyright (C) 2011 by Hajime Nakagami, Takahiro Kamatani

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
import os
import sys
import struct
import zlib
from cStringIO import StringIO
from PIL import Image
from math import ceil
from tomato.utils import _h32, _h16, le2byte, le4byte


DEBUG = False


swf_tag_name_entry = {
    0:  'End',
    1:  'ShowFrame',
    2:  'DefineShape',
    6:  'DefineBitsJPEG',
    8:  'JPEGTables',
    9:  'SetBackgoundColor',
    11: 'DefineText',
    12: 'DoAction',
    20: 'DefineBitsLossLess',
    21: 'DefineBitsJPEG2',
    22: 'DefineShape2',
    26: 'PlaceObject2',
    32: 'DefineShape3',
    35: 'DefineBitsJPEG3',
    36: 'DefineBitsLossless2',
    37: 'DefineEditText',
    39: 'DefineSprite',
    43: 'FrameLabel',
    48: 'DefineFont2',
    88: 'DefineFontName',
}


class SwfImageDumper(object):
    def __init__(self, input_swf, output_swf="", input_image="", image_id="", output_file=""):
        self.image_dict = {}
        if input_image:
            self.input_image = input_image
            self.image_id = image_id
            self.output_swf = output_swf
        else:
            self.image_id = -1
        self.swf = input_swf
        self.swf_pos = 0
        self.parse_swf_head()
        self.output_file = output_file
        self.replace_data()

        if not input_image:
            for k, v in self.image_dict.items():
                self.save_image(k, v)
                v['data'] = len(v['data']) / 1000.0   # del v['data']
                # print "%s\t%s" % (k, v)

    def parse_swf_head(self):
        "swf_header"
        self.magic = self.swf_read(3)
        self.version = ord(self.swf_read(1))
        self.file_length = le4byte(self.swf_read(4))
        
        "swf_header_movie"
        # twips 関連のヘッダは、今は飛ばす
        rectbits = ord(self.swf_read(1)) >> 3
        total_bytes = int(ceil((5 + rectbits * 4) / 8.0)) 
        twips_waste = self.swf_read(total_bytes - 1)
    
        # frame 関連
        self.frame_rate_decimal = ord(self.swf_read(1))
        self.frame_rate_integer = ord(self.swf_read(1))
        self.frame_count = le2byte(self.swf_read(2))
    
        if DEBUG:
            print "magic: %s\nver: %d\nlen: %d\nframe_rate: %d.%d\ncount: %d\n" % ( \
                self.magic,
                self.version,
                self.file_length,
                self.frame_rate_integer,
                self.frame_rate_decimal,
                self.frame_count)

    def replace_data(self):
        "swf_tag"
        while self.parse_swfblock():
            if DEBUG: print self.block['tag_name'], self.block['block_len']
            if self.block['tag'] in (20, 36):
                ret = self.parse_lossless(
                          self.block['value'], 
                          self.block['block_len'])
            elif self.block['tag'] == 21:
                ret = self.parse_jpeg(
                    self.block['value'],
                    self.block['block_len'])
    
    def parse_lossless(self, v, length):
        "共通部分"
        image_id = le2byte(self.block_read(2))
        format = ord(self.block_read(1))
        width = le2byte(self.block_read(2))
        height = le2byte(self.block_read(2))
        data = self.block_read(length-7)

        self.image_dict[image_id] = {
            'tag': swf_tag_name_entry[self.block['tag']],
            'format': format,
            'width': width,
            'height': height,
            'data': data,
            }

    def parse_jpeg(self, v, length):
        image_id = le2byte(self.block_read(2))
        data = self.block_read(length-2)
        self.image_dict[image_id] = {
            'tag': swf_tag_name_entry[self.block['tag']],
            'format': -1,
            'data': data,
            }

    def parse_swfblock(self):
        # print "--swf_pos:", self.swf_pos
        swf_block_start = self.swf_pos
        swf_tag = le2byte(self.swf_read(2))
        block_len = swf_tag & 0x3f
        if block_len == 0x3f:
            block_len = le4byte(self.swf_read(4))
        swf_tag = swf_tag >> 6        
        if swf_tag == 0:
            return None
        
        try:
            swf_tag_name = swf_tag_name_entry[swf_tag]
        except KeyError:
            swf_tag_name = "Unknown"
        
        self.block_pos = 0
        ret = {}
        ret['block_start'] = swf_block_start
        ret['tag'] = swf_tag
        ret['block_len'] = block_len
        ret['tag_name'] = swf_tag_name
        ret['value'] = self.parse_swfblock_misc(swf_tag, block_len)
        self.block = ret
        return True

    def parse_swfblock_misc(self, swf_tag, block_len):
        if block_len:
            return self.swf_read(block_len)
        else:
            return None

    def block_read(self, num): # num byte(s) ずつ swf を読み出す
        self.block_pos += num
        return self.block['value'][self.block_pos - num: self.block_pos]

    def swf_read(self, num): # num byte(s) ずつ swf を読み出す
        self.swf_pos += num
        return self.swf[self.swf_pos - num: self.swf_pos]

    def save_image(self, object_id, v):
        # 実際に出力した画像の ID を保存
        file_base = self.output_file

        if v['tag'] == 'DefineBitsLossLess' and v['format'] == 3:
            color_table_length = ord(v['data'][0])+1
            decompress_data = zlib.decompress(v['data'][1:])
            color_table = []
            for i in range(color_table_length):
                c = (ord(decompress_data[i*3]), 
                     ord(decompress_data[i*3+1]), 
                     ord(decompress_data[i*3+2]))
                color_table.append(c)
            color_map = decompress_data[color_table_length*3:]
            width = v['width']
            height = v['height']
            width = width if width % 4 == 0 else (width/4+1)* 4
            im = Image.new("RGB", (width, height), "white")
            x = y = 0
            for i in range(len(color_map)):
                im.putpixel((x,y), color_table[ord(color_map[i])])
                x += 1
                if x == width:
                    x = 0
                    y += 1

            out_file = "%s_%s.png" % (file_base, object_id)
            im.save(out_file)
            v['file_name'] = os.path.split(out_file)[1]

        elif v['tag'] == 'DefineBitsLossless2' and v['format'] == 3:
            color_table_length = ord(v['data'][0])+1
            decompress_data = zlib.decompress(v['data'][1:])
            color_table = []
            for i in range(color_table_length):
                c = (ord(decompress_data[i*4+0]), 
                     ord(decompress_data[i*4+1]), 
                     ord(decompress_data[i*4+2]),
                     ord(decompress_data[i*4+3]))
                color_table.append(c)
            color_map = decompress_data[color_table_length*4:]
            width = v['width']
            height = v['height']
            width = width if width % 4 == 0 else (width/4+1)* 4
            im = Image.new("RGB", (width, height), "white")
            x = y = 0
            for i in range(len(color_map)):
                im.putpixel((x,y), color_table[ord(color_map[i])])
                x += 1
                if x == width:
                    x = 0
                    y += 1

            out_file = "%s_%s.png" % (file_base, object_id)
            im.save(out_file)
            v['file_name'] = os.path.split(out_file)[1]

        elif v['tag'] == 'DefineBitsLossLess' and v['format'] == 5:
            decompress_data = zlib.decompress(v['data'])
            width = v['width']
            height = v['height']
            im = Image.new("RGB", (width, height), "white")
            x = y = 0
            for i in range(0, len(decompress_data), 4):
                im.putpixel((x,y), (ord(decompress_data[i+1]),
                                    ord(decompress_data[i+2]),
                                    ord(decompress_data[i+3])))
                x += 1
                if x == width:
                    x = 0
                    y += 1

            out_file = "%s_%s.png" % (file_base, object_id)
            im.save(out_file)
            v['file_name'] = os.path.split(out_file)[1]

        elif v['tag'] == 'DefineBitsLossless2' and v['format'] == 5:
            decompress_data = zlib.decompress(v['data'])
            width = v['width']
            height = v['height']
            im = Image.new("RGBA", (width, height), "white")
            x = y = 0
            for i in range(0, len(decompress_data), 4):
                im.putpixel((x,y), (ord(decompress_data[i+1]),
                                    ord(decompress_data[i+2]),
                                    ord(decompress_data[i+3]),
                                    ord(decompress_data[i+0])))
                x += 1
                if x == width:
                    x = 0
                    y += 1

            out_file = "%s_%s.png" % (file_base, object_id)
            im.save(out_file)
            v['file_name'] = os.path.split(out_file)[1]

        elif v['tag'] == 'DefineBitsJPEG2':
            data = v['data']
            if data[:4] == '\xff\xd9\xff\xd8':
                """
                See: http://pwiki.awm.jp/~yoya/?Flash/JPEG
                    JPEG SOI marker (FF D8) -> \xff\xd8
                    JPEG EOI marker (FF D9) -> \xff\xd9
                Flash に格納されているのは基本的にはそのままの JPEG データ
                ただし、データの最初に [EOI] + [SOI] が付けられていることがあり
                その場合は除去する必要がある
                """
                data = data[4:]
            im = Image.open(StringIO(data))

            v['width'] = im.size[0]
            v['height'] = im.size[1]
            out_file = "%s_%s.jpg" % (file_base, object_id)
            im.save(out_file)
            v['file_name'] = os.path.split(out_file)[1]

    def save(self, outfile):
        f = open(outfile, 'w')
        f.write(self.swf)
        f.close()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        output_file = os.path.splitext(os.path.abspath(sys.argv[1]))[0]
        swf = SwfImageDumper(
            input_swf=open(sys.argv[1]).read(),
            output_file=output_file)
    elif len(sys.argv) == 3:
        swf = SwfImageDumper(
            input_swf=open(sys.argv[1]).read(),
            output_file=sys.argv[2])
    else:
        print "usage: python swf_image_dumper.py <input.swf> [<output_file>]"

