# -*- coding: utf-8 -*-
"""
SwfImageReplacer:
  Flash の画像置き換えツール(GIF, PNG, JPEG 対応版)
  必要ライブラリ: Python Imaging Library 1.1.7

--

MIT License

Copyright (C) 2011 by Takahiro Kamatani, Hajime Nakagami

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
import struct
import zlib
from cStringIO import StringIO
from PIL import Image
from math import ceil
from utils import _h32, _h16, le2byte, le4byte
from exceptions_tomato import is_valid_swf


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


class SwfImage(object):
    def __init__(self, swf):
        is_valid_swf(swf)
        self.swf = swf
        self.swf_pos = 0
        self.parse_swf_head()
        self.parse_swfblocks()

    def parse_swf_head(self):
        "swf_header"
        self.magic = self.swf_read(3)
        self.version = ord(self.swf_read(1))
        self.file_length = le4byte(self.swf_read(4))

        "swf_header_movie"
        # twips 関連のヘッダは、今は飛ばす
        rectbits = ord(self.swf_read(1)) >> 3
        total_bytes = int(ceil((5 + rectbits * 4) / 8.0))
        self.swf_read(total_bytes - 1)

        # frame 関連
        self.frame_rate_decimal = ord(self.swf_read(1))
        self.frame_rate_integer = ord(self.swf_read(1))
        self.frame_count = le2byte(self.swf_read(2))

        # ヘッダー, twips, frame データを取っておく
        self.swf_head = self.swf[:self.swf_pos]

        if DEBUG:
            print "magic: %s\nver: %d\nlen: %d\n" \
                "frame_rate: %d.%d\ncount: %d\n" % ( \
                self.magic,
                self.version,
                self.file_length,
                self.frame_rate_integer,
                self.frame_rate_decimal,
                self.frame_count)

    def parse_swfblocks(self):
        "Parse/Split blocks."
        self.swf_blocks = []
        block = self.parse_swfblock()
        while block:
            self.swf_blocks.append(block)
            block = self.parse_swfblock()

        if DEBUG:
            for block in self.swf_blocks:
                print block['tag_name'], block['block_len']

    def replace_images(self, images):
        for block in self.swf_blocks:
            if block['tag'] in (20, 21, 36):
                image_id = le2byte(block['value'][6:8])
                if image_id in images:
                    if block['tag'] in (20, 36):   # DefineBitsLossless, DefineBitsLossless2
                        self.replace_lossless(block, images[image_id])
                    elif block['tag'] == 21:   # DefineBitsJPEG2
                        self.replace_jpeg(block, images[image_id])

    def replace_jpeg(self, block, image_data):
        """
        DefineBitsJPEG2 を置き換える関数
        1. SWF ヘッダーの length の置き換え
        2. tag block の書き換え
        """
        assert image_data[:2] == '\xff\xd8'   # JPEG SOI marker
        
        tag_raw = block['value'][:2]
        image_id = block['value'][6:8]

        # 1.
        old_length = block['block_len']
        new_length = len(image_data) + 2
        self.file_length += (new_length - old_length)

        # 2.
        block['block_len'] = new_length
        block['value'] = \
            tag_raw + \
            _h32(new_length) + \
            image_id + \
            image_data

    def replace_lossless(self, block, image_data):
        """
        DefineBitsLossless, DefineBitsLossless2 を置き換える関数
        画像を置き換える際に行うこと
        1. lossless データの置き換え
        2. ヘッダーの length の置き換え
        3. tag block での length の置き換え
        4. width, height, format データの置き換え
        """
        tag_raw = block['value'][:2]
        old_length = block['block_len']   # block['value'][2:6] と同じはず
        image_id = le2byte(block['value'][6:8])
        # format = ord(block['value'][8])

        # 1.
        g = Image2lossless(image_data, block['tag'])
        fv_read = g.convert()
        new_length = len(fv_read) + 7

        # 2.
        self.file_length += (new_length - old_length)

        # 3.
        block['block_len'] = new_length

        # 4.
        block['value'] = \
            tag_raw + \
            _h32(new_length) + \
            _h16(image_id) + \
            g.get_lossless_format() + \
            _h16(g.width()) + \
            _h16(g.height()) + \
            fv_read

    def parse_swfblock(self):
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

        ret = {}
        ret['block_start'] = swf_block_start
        ret['tag'] = swf_tag
        ret['block_len'] = block_len
        ret['tag_name'] = swf_tag_name
        self.swf_pos += block_len
        ret['value'] = self.swf[swf_block_start:self.swf_pos]
        return ret

    def swf_read(self, num):   # num byte(s) ずつ swf を読み出す
        self.swf_pos += num
        return self.swf[self.swf_pos - num: self.swf_pos]

    def write(self, f):
        "swf 出力"
        # ヘッダー長を書き換え
        fl = _h32(self.file_length)
        self.swf_head = self.swf_head[:4] + fl + self.swf_head[8:]
        f.write(self.swf_head)
        for block in self.swf_blocks:
            f.write(block['value'])
        f.write('\00\00')


class Image2lossless(object):
    def __init__(self, image_data, tag):
        """
        GIF/PNG 形式から Flash 独自フォーマット
        lossless(2) 形式に変換する

        GIF/PNG での Palette モードの場合
            [transparency に何もセットされていないとき]
            Palette  ->  DefineBitsLossless   format 3

            [transparency がセットされている場合]
                     ->  DefineBitsLossless2  format 3

        PNG で頻繁に用いられる RGB, RGBA モードの場合
            RGB      ->  DefineBitsLossless   format 5
            RGBA     ->  DefineBitsLossless2  format 5
        """
        self.image = Image.open(StringIO(image_data))
        assert self.image.format in ('GIF', 'PNG')
        self.tag = tag

    def get_lossless_format(self):
        if self.image.mode == 'P':
            return chr(3)
        elif self.image.mode in ('RGB', 'RGBA'):
            return chr(5)

    def width(self):
        return self.image.size[0]

    def height(self):
        return self.image.size[1]

    def alex_width(self):
        return alex_width(self.image.size[0])

    def colormap_count(self):
        if self.image.mode == 'P':
            """
            パレットの場合、色数を返す
            （ただし 0 から数えるので - 1 する）

            3 で割っているのはパレット形式の場合、
            パレット中に RGB 順で色が並ぶと仮定してるため
            """
            return chr(len(self.image.palette.palette) / 3 - 1)
        else:
            return ""   # Otherwise absent

    def convert(self):
        if self.image.mode == 'P':
            return self.convert_palette()
        elif self.image.mode in ('RGB', 'RGBA'):
            return self.convert_rgb()

    def convert_rgb(self):
        """
        RGB/RGBA 形式の画像を lossless(2) に変換する
        基本的に PNG のみ
        """
        def rgba2argb(l):
            # RGBA で並んでいる列を ARGB に直す
            a = l[3]
            r, g, b = l[0] * a / 255, l[1] * a / 255, l[2] * a / 255
            return chr(a) + chr(r) + chr(g) + chr(b)

        indices = ""
        if self.tag == 20:   # DefineBitsLossless
            for tpl in list(self.image.getdata()):
                # tpl は (23, 136, 244).  PIX24 format
                indices += ('\xff' +
                            ''.join(map(chr, tpl[:3])))

        elif self.tag == 36:   # DefineBitsLossless2
            for tpl in list(self.image.getdata()):
                # 置き換え先の画像も透明値を持つ事が前提
                assert len(tpl) == 4   # R,G,B,A
                indices += rgba2argb(tpl)

        return self.colormap_count() + zlib.compress(indices)

    def convert_palette(self):
        """
        パレット形式の GIF/PNG 画像を lossless(2) に変換する
        基本的には、GIF、PNG で差異は存在しない
        """
        palette = pack(map(ord, self.image.palette.palette), 3)

        """
        colormap を定義する
        DefineBitsLossless なら PIL の palette が使えるが
        DefineBitsLossless2 だと、Alpha の値を加える必要がある
        """
        if self.tag == 20:   # DefineBitsLossless
            colormap = self.image.palette.palette
        elif self.tag == 36:  # DefineBitsLossless2
            if 'transparency' in self.image.info:
                transparency = int(self.image.info['transparency'])
            else:
                transparency = 65535
            colormap = ""
            for i, c in enumerate(palette):
                if i == transparency:
                    colormap += ''.join(map(chr, [0, 0, 0, 0]))
                else:
                    colormap += ''.join(map(chr, c + [255]))

        """
        実際の indices とくっつける
        もし横幅が alex_width（4 の倍数）でなければ
        画像を 4 の倍数に調節する
        """
        raw_indices = ''.join(
            map(chr, list(self.image.getdata())))

        if self.width() != alex_width(self.width()):
            indices = adjust_palette_data(raw_indices, self.width())
        else:
            indices = raw_indices

        return self.colormap_count() + zlib.compress(colormap + indices)


def alex_width(num):
    return (num + 3) & -4


def adjust_palette_data(data, width):
    """
    Flash の画像の大きさについては
    width が 4 の倍数でなければならない
    indices をそのようにあわせる
    """
    new_data = ""
    gap = alex_width(width) - width
    for i in range(0, len(data), width):
        new_data += data[i:(i + width)] + '\0' * gap
    return new_data


def pack(l, num):
    ret = []
    for i in range(len(l) / num):
        ret.append(l[i * num: (i + 1) * num])
    return ret


if __name__ == '__main__':
    replace_images = {}
    replace_images[7] = open('sample/bitmap/kinoko_blue.jpg').read()
    replace_images[8] = open('sample/bitmap/kinoko_blue.png').read()
    replace_images[4] = open('sample/bitmap/kinoko_blue_alpha.png').read()

    swf = SwfImage(swf=open('sample/bitmap/bitmap.swf').read())

    swf.replace_images(replace_images)
    swf.write(open('sample/bitmap/out.swf', 'wb'))

