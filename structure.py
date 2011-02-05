#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tomato.structure - Flash Tags' Classes

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
import hashlib
import parser

from bitarray import bitarray
from collections import defaultdict
from utils import _h32, _h16, le2byte, le4byte, \
     flatten_defaultdict_set, \
     Bits, SignedBits as SB, s2b, b2i, _oct, \
     MATRIX, CXFORMWITHALPHA, RECT, \
     SERIALIZER_MOVIECLIP_V1 as MOVIECLIP_V1
from exceptions_tomato import *


DEBUG = False


class StreamIO(object):
    __slots__ = ('value', 'bitvalue', 'pos', 'bpos')
    
    def __init__(self, value=""):
        self.value = value
        self.bitvalue = s2b(value)
        self.pos = 0
        self.bpos = 0   # bit 毎に読み込むための offset

    def read(self, num):
        self.align_byte()
        self.pos += num
        self.bpos = self.pos * 8
        if len(self.value) < self.pos:
            raise StringError('%s - len(value): %d < pos: %d' % (
                self.__class__.__name__, len(self.value), self.pos))
        return self.value[self.pos - num: self.pos]

    def read_bits(self, num):
        self.bpos += num
        return self.bitvalue[self.bpos - num: self.bpos]

    def align_pos(self):
        self.pos = self.bpos / 8

    def set_pos(self, num):
        self.pos = num
        self.bpos = num * 8
    
    def get_bits(self, num):
        return self.bitvalue[self.bpos: self.bpos + num]
        
    def read_string(self):
        ret_string = ""
        s = self.read(1)
        while s != '\x00':   # Null Character
            if s == '':
               raise NullCharacterDoesNotExist('%s: %s' % (self, repr(ret_string)))
            ret_string += s
            s = self.read(1)
        return ret_string

    def align_byte(self):
        self.bpos = _oct(self.bpos)
        self.pos = self.bpos / 8


class SwfBlock(StreamIO):
    _serialize_attr_ = {
        MOVIECLIP_V1: ('tag', 'length', 'content_offset', 'value')
        }

    def __init__(self, tag, length, content_offset, value, base_block, swf=None, IS_PARSE=True):
        if IS_PARSE:
            StreamIO.__init__(self, value)
        else:
            self.value = value
        self.tag = tag
        self.length = length
        self.content_offset = content_offset
        self.set_pos(self.content_offset)   # タグ種別と長さの分を足す
        self.base_block = base_block
        self.swf = swf
        self.IS_PARSE = IS_PARSE

    def __len__(self):
        return len(self.value)
        
    def __str__(self):
        return "%s(%d) - len:%d" % (self._get_class_name(), self.tag, self.length)

    def __repr__(self):
        return "<SWF Tag: %s(length: %d) at %#x>" % (self._get_class_name(), self.length, id(self))

    def __unicode__(self):
        return self._get_class_name()

    def _get_class_name(self):
        name = self.__class__.__name__ 
        if name == "SwfBlock":
            return "unknown"
        else:
            return name

    @property
    def tag_name(self):
        return self.__class__.__name__

    def copy(self, swf=None, base_block=None):
        if not base_block:
            base_block = self.base_block
        new = self.__class__(
            self.tag,
            self.length,
            self.content_offset,
            self.value,
            base_block,
            swf,
            False)    # IS_PARSE
        return new

    def set_length(self, num):
        """
        タグ（block）の length を変える. length の長さによって形式が変わる
        See swf_file_format_spec_v10.pdf (p.27)
        """
        old_tag_code_and_length = le2byte(self.value[:2])
        length = old_tag_code_and_length & 0x3f

        if length != 63:
            """
            short. TagCodeAndLength は 2 byte のみ
            """
            tag_code_and_length = (self.tag << 6) + num
            self.value = _h16(tag_code_and_length) + self.value[2:]
        else:
            """
            large. TagCodeAndLength は 2 byte + 4 byte
            後ろの 4 byte の length を変えれば良い
            """
            self.value = self.value[:(self.content_offset - 4)] + _h32(num) + \
                self.value[self.content_offset:]
        self.length = num

    def serialize(self, serializer_version):
        ret = []
        for attr in self._serialize_attr_[serializer_version]:
            ret.append(getattr(self, attr))
        return tuple(ret)


class DefinitionTag(SwfBlock):
    """
    Flash の Definition Tag のクラス
    定義されているコンテンツのハッシュ値の作成などを行う
    """
    _serialize_attr_ = {
        MOVIECLIP_V1: (
            'tag',
            'length',
            'content_offset',
            'value',
            'character_id_offset',
            'character_id',
            'hash')
        }

    def __init__(self, *args):
        SwfBlock.__init__(self, *args)

        if self.IS_PARSE:
            # Definition Tag には最初２バイトに必ずユニークな character_id が存在している
            self.character_id_offset = self.pos
            self.character_id = le2byte(self.value[self.pos:(self.pos + 2)])

            # ハッシュの生成
            self.generate_hash()

    def generate_hash(self):
        self.hash = hashlib.md5(self.value[(self.pos + 2):]).hexdigest()

    def copy(self, swf=None, base_block=None):
        if not base_block:
            base_block = self.base_block
        # DefinitionTag は、hash, character_id, character_id_offset も保持する
        new = self.__class__(
            self.tag,
            self.length,
            self.content_offset,
            self.value,
            base_block,
            swf,
            False)    # IS_PARSE
        new.hash = self.hash
        new.character_id = self.character_id
        new.character_id_offset = self.character_id_offset
        return new

    def set_character_id(self, num):
        "CharacterId を置き換える"
        assert isinstance(num, int)
        self.value = \
            self.value[:self.character_id_offset] + _h16(num) + \
            self.value[(self.character_id_offset + 2):]
        self.character_id = num
    
    def deserialize(self, serializer_version, tpl):
        # except basic attributes (tag, length, content_offset, value)
        for i, attr in enumerate(
            self._serialize_attr_[serializer_version][4:]):
            setattr(self, attr, tpl[i])


class SoundStreamHead2(SwfBlock):     # Tag type: 45
    def __init__(self, *args):
        SwfBlock.__init__(self, *args)
        

class DefineSound(DefinitionTag):    # Tag type: 14
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)


class DefineSprite(DefinitionTag):    # Tag type: 39
    _serialize_attr_ = {
        MOVIECLIP_V1: (
            'tag',
            'length',
            'content_offset',
            'value',
            'character_id_offset',
            'character_id',
            'hash',
            'framecount_offset',
            'framecount',
            'blocks_offset')
        }

    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        self.framecount_offset = None
        self.framecount = None
        self.blocks_offset = None

        if self.IS_PARSE == True:
            self.parse()

    def parse(self):
        self.sprite_id = le2byte(self.read(2))  # Sprite ID

        self.framecount_offset = self.pos
        self.framecount = le2byte(self.read(2))

        self.blocks_offset = self.pos
        self.blocks = parser.SwfBlockParser(
            self.value[self.pos:],
            base_block=self).blocks   # ここからタグが続く        

    def set_framecount(self, num):
        "Framecount を置き換える"
        self.value = \
            self.value[:self.framecount_offset] + \
            _h16(num) + \
            self.value[(self.framecount_offset + 2):]
        self.framecount = num

    def update_value(self):
        "blocks が更新されたときのために、自分自身を更新する"
        self.value = self.value[:self.blocks_offset] + ''.join(map(lambda b: b.value, self.blocks))

        "この tag 自体の length も変更する．ただし最初のタグと長さは含めない"
        self.set_length(len(self.value) - self.content_offset)

    def serialize(self, serializer_version):
        # シリアライズ関数を DefineSprite 専用にオーバーライドする
        ret = []
        for attr in self._serialize_attr_[serializer_version]:
            ret.append(getattr(self, attr))
        
        # blocks はそれぞれシリアライズする必要がある
        ret_blocks = []
        for block in self.blocks:
            ret_blocks.append(block.serialize(MOVIECLIP_V1))
        ret.append(ret_blocks)        
        return ret
    
    def deserialize(self, serializer_version, tpl):
        # except basic attributes (tag, length, content_offset, value)
        for i, attr in enumerate(
            self._serialize_attr_[serializer_version][4:]):
            setattr(self, attr, tpl[i])
        self.blocks = parser.deserialize_blocks(
            swf=self.swf,
            base_block=self,
            blocks_tpl=tpl[-1],
            serializer_version=serializer_version)

    def copy(self, swf=None, base_block=None):
        # DefinitionTag は、hash, character_id, character_id_offset も保持する
        if not base_block:
            base_block = self.base_block
        new = self.__class__(
            self.tag,
            self.length,
            self.content_offset,
            self.value,
            base_block,
            swf,
            False)    # IS_PARSE
        new.hash = self.hash
        new.character_id = self.character_id
        new.character_id_offset = self.character_id_offset

        new.blocks_offset = self.blocks_offset
        new.blocks = map(lambda b: b.copy(swf, base_block=new), self.blocks)
        return new


class MovieClip(object):
    """
    DefineSprite やそれを表示する PlaceObject2 をひとまとめにして
    置き換えを簡単にできるようにするために作ったクラス
    """
    def __init__(self, swf, define_sprite, place_object2):
        self.swf = swf
        self.define_sprite = define_sprite
        self.place_object2 = place_object2

        self._translate = (0, 0)   # twips を基準に
        self._scale, self._rotate = None, None

        if self.place_object2:
            m = self.place_object2.matrix
            
            self._translate = (
                m.getattr_value('translate_x'),
                m.getattr_value('translate_y'))
            if m.getattr_value('has_scale'):
                self._scale = (
                    m.getattr_value('scale_x'),
                    m.getattr_value('scale_y'))
            if m.getattr_value('has_rotate'):
                self._rotate = (
                    m.getattr_value('rotate_skew0'),
                    m.getattr_value('rotate_skew1'))

    @property
    def translate(self):
        return tuple(map(twip2pixel, self._translate))
    
    def set_translate(self, translate_x, translate_y):
        self._translate = pixel2twip(translate_x), pixel2twip(translate_y)
        self.change_matrix()

    @property
    def scale(self):
        return self._scale

    def set_scale(self, scale_x, scale_y):
        self._scale = scale_x, scale_y
        self.change_matrix()

    @property
    def rotate(self):
        return self._rotate
    
    def set_rotate(self, rotate_skew0, rotate_skew1):
        self._rotate = rotate_skew0, rotate_skew1
        self.change_matrix()

    @property
    def depth(self):
        self.get_place_object2()
        return self.place_object2.depth
    
    def set_depth(self, num):
        self.get_place_object2()
        self.place_object2.set_depth(num)

    def change_matrix(self):
        self.get_place_object2()
        self.place_object2.replace_matrix(
            MATRIX().generate(
                   scale=self._scale, 
                   rotate=self._rotate,
                   translate=self._translate))

    def get_place_object2(self):
        if not self.place_object2:
            for p in self.swf.search_tags('PlaceObject2'):
                if p.target_character_id == self.define_sprite.character_id:
                    self.place_object2 = p
                    return

    def copy_inside_definition_tags(self, new_swf, define_sprite):
        """
        new_swf に MovieClip 内部で用いられている
        Definition Tags を追加する
        """
        # ID 更新用辞書
        update_character_dict = {}
        
        # 全ての DefinitionTags'ID を queue に収集する
        queue = self.swf.get_all_definition_tags(define_sprite, depth=1, dts=defaultdict(set))
        """
        new_swf 内に DefinitionTag があるかどうか調べて、
        ・無ければ   -> new_swf の blocks に追加して、新規IDを取得する
        ・存在すれば -> 既存ID を取得する
        """
        for d in flatten_defaultdict_set(queue):
            ch_id = new_swf.get_same_definition_tag(self.swf.character_dict[d])
            if ch_id:
                update_character_dict[d] = ch_id
            else:
                new_dt_id = new_swf.insert_definition_tag(
                    new_dt=self.swf.character_dict[d],
                    before_dt=define_sprite)
                update_character_dict[d] = new_dt_id

        """
        最後に ID 更新用辞書に基づいて queue 内の DefineSprite 内の
        PlaceObject2 の TargetCharacterID を全て更新する

        queue の中身は、階層の深さ毎に ID が set として記述されている
        深い階層から順番に update_value を行う
        """
        for i in range(max(queue), 0, -1):
            for q in queue[i]:
                ds = new_swf.character_dict[update_character_dict[q]]
                if not isinstance(ds, DefineSprite):
                    continue

                for block in ds.blocks:
                    if isinstance(block, PlaceObject2) and block.target_character_id != None:
                        new_id = update_character_dict[block.target_character_id]
                        block.set_target_character_id(new_id)
                ds.update_value()

        for block in define_sprite.blocks:
            if isinstance(block, PlaceObject2) and block.target_character_id != None:
                new_id = update_character_dict[block.target_character_id]
                block.set_target_character_id(new_id)
        define_sprite.update_value()

    def set_name(self, name):
        self.place_object.set_name(name)


def pixel2twip(num): return int(num * 20)
def twip2pixel(num): return num / 20.0


def draw_define_sprite(swf, ds, num_base=1):
    prev = "-" * (num_base * 3)
    if num_base == 1:
        str_x = "%d %s" % (num_base, ds)
        print str_x + (60 - len(str_x)) * " " + str(ds.character_id)
        num_base += 1
    prev = prev + ": %d" % num_base
    for b in ds.blocks:
        if isinstance(b, PlaceObject2):
            if b.target_character_id:
                pp = swf.character_dict[b.target_character_id]
                
                if isinstance(pp, DefineSprite):
                    if hasattr(b, 'name'):
                        str_pp = str(pp) + b.name
                    else:
                        str_pp = str(pp)
                    str_x = "%s %s" % (prev, str_pp)
                    print str_x + (60 - len(str_x)) * " " + str(pp.character_id)
                    draw_define_sprite(swf, pp, num_base + 1)
        else:
            if hasattr(b, 'character_id'):
                #print "%s %s (ID:%d)" % (prev, str(b), b.character_id)
                pass
            else:
                #print "%s %s" % (prev, str(b))
                pass


class FrameLabel(SwfBlock):
    def __init__(self, *args):
        SwfBlock.__init__(self, *args)
        #self.parse()

    def parse(self):
        self.name = self.read_string()
    

class RemoveObject2(SwfBlock):
    def __init__(self, *args):
        SwfBlock.__init__(self, *args)
        #self.parse()
    
    def parse(self):
        self.depth = le2byte(self.read(2))


class DefineButton2(DefinitionTag):
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        #self.parse()
    
    def parse(self):
        pass
        

class DefineBitsLossless2(DefinitionTag):
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        #self.parse()
    
    def parse(self):
        self.character_id = le2byte(self.read(2))
        self.BitmapFormat = ord(self.read(1))
        self.BitmapWidth = le2byte(self.read(2))
        self.BitmapHeight = le2byte(self.read(2))
        if self.BitmapFormat == 3:
            self.BitmapColorTableSize = ord(self.read(1))
        # self.ZlibBitmapData = ...


class DefineBits(DefinitionTag):   # Tag type: 6
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        #self.parse()
        
    def parse(self):
        self.character_id = le2byte(self.read(2))    # CharacterID
        # self.JPEGData = self.read[self.offset:]


class JPEGTables(SwfBlock):   # Tag type: 8
    def __init__(self, *args):
        SwfBlock.__init__(self, *args)


class DefineText(DefinitionTag):  # Tag type: 11
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        #self.parse()
        
    def parse(self):
        self.character_id = le2byte(self.read(2))
        # self.TextBounds = RECT(...)
        # self.TextMatrix = MATRIX(...)
        # self.GlyphBits = ord(self.read(1))
        # self.AdvanceBits = ord(self.read(1))
        # ...


class DefineBitsJPEG2(DefinitionTag):
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        #self.parse()
        
    def parse(self):
        self.character_id = le2byte(self.read(2))
        self.JPEGData = self.read[self.offset:]


class DefineEditText(DefinitionTag):   # Tag type: 37
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        #self.parse()
        
    def parse(self):
        self.character_id = le2byte(self.read(2))
        # self.Bounds = RECT(...)
        # ...


class DefineBitsJPEG3(DefinitionTag):    # Tag type: 35
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        #self.parse()
        
    def parse(self):
        self.character_id = le2byte(self.read(2))
        self.AlphaDataOffset = le4byte(self.read(4))
        # ...


class DefineBitsLossless(DefinitionTag):   # Tag type: 20
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        #self.parse()
        
    def parse(self):
        self.character_id = le2byte(self.read(2))
        self.BitmapFormat = ord(self.read(1))
        self.BitmapWidth = le2byte(self.read(2))
        self.BitmapHeight = le2byte(self.read(2))
        if self.BitmapFormat == 3:
            self.BitmapColorTableSize = ord(self.read(1))
        # self.ZlibBitmapData = ...


class DoAction(SwfBlock):  # Tag type: 12
    def __init__(self, *args):
        SwfBlock.__init__(self, *args)
        #self.parse()
        
    def parse(self):
        pass
        #self.actions = ACTIONRECORD(self.read)
        #self.ActionEndFlag = ord(self.read(1))

"""
構造体を表すクラス
"""
class StructBlock(object):
    def __init__(self, block):
        if block:
            self.block = block
            self.block.align_pos()
            self.before_parse_offset = self.block.pos
            self.read = block.read
            self.read_bits = block.read_bits
            self.align_byte = block.align_byte
            self.get_bits = block.get_bits
            
    def parse_end(self):
        self.block.align_byte()
        self._value = self.block.value[self.before_parse_offset: self.block.pos]
        self.length = self.block.pos - self.before_parse_offset

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, dict):
        for attr, value in dict.items():
            setattr(self, attr, value)


class RGB(StructBlock):
    def __init__(self, block):
        StructBlock.__init__(self, block)
        self.r = ord(self.read(1))
        self.g = ord(self.read(1))
        self.b = ord(self.read(1))


class RGBA(StructBlock):
    def __init__(self, block):
        StructBlock.__init__(self, block)
        self.r = ord(self.read(1))
        self.g = ord(self.read(1))
        self.b = ord(self.read(1))
        self.a = ord(self.read(1))


class GRADERECORD(StructBlock):
    def __init__(self, block):
        StructBlock.__init__(self, block)

        self.Ratio = ord(self.read(1))
        if self.block.tag_name in ('DefineShape1', 'DefineShape2'):
            self.Color = RGB(self.block)
        elif self.block.tag_name == "DefineShape3":
            self.Color = RGBA(self.block)


class GRADIENT(StructBlock):
    def __init__(self, block):
        StructBlock.__init__(self, block)
        
        self.SpreadMode = self.read_bits(2)
        self.InterPolationMode = self.read_bits(2)
        self.NumGradients = self.read_bits(4)
        
        self.GradientRecords = []
        for i in range(self.NumGradients):
            self.GradientRecords.append(GRADERECORD(self.block))


class FILLSTYLE(StructBlock):
    def __init__(self, block):
        StructBlock.__init__(self, block)
        
        self.FillStyleType = self.read(1)
        
        if self.FillStyleType == '\x00':
            if self.block.tag_name in ('DefineShape', 'DefineShape2'):
                self.color = RGB(self.block)
            elif self.block.tag_name == 'DefineShape3':
                self.color = RGBA(self.block)

        if self.FillStyleType in ('\x10', '\x12', '\x13'):
            self.GradientMatrix = MATRIX()
            self.GradientMatrix.parse(self.block)
        
        if self.FillStyleType in ('\x10', '\x12'):
            self.Gradient = GRADIENT(self.block)
        # elif self.FillStyleTYPE == '\x13':  # SWF 8 or later
        #     self.Gradient = FOCALGRADIENT(self.block)

        if self.FillStyleType in ('\x40', '\x41', '\x42', '\x43'):
            self.BitmapId = le2byte(self.read(2))
            self.BitmapMatrix = MATRIX()
            self.BitmapMatrix.parse(self.block)


class FILLSTYLEARRAY(StructBlock):
    def __init__(self, block):
        StructBlock.__init__(self, block)

        self.FillStyleCount = ord(self.read(1))
        if self.FillStyleCount == '\xff':
            self.FillStyleCountExtended = le2byte(self.read(2))

        self.FillStyles = []
        for i in range(self.FillStyleCount):
            self.FillStyles.append(FILLSTYLE(self.block))


class LINESTYLE(StructBlock):
    def __init__(self, block):
        StructBlock.__init__(self, block)
        self.width = le2byte(self.read(2))
        if self.block.tag_name in ('DefineShape', 'DefineShape2'):
            self.color = RGB(self.block)
        elif self.block.tag_name == 'DefineShape3':
            self.color = RGBA(self.block)


class LINESTYLEARRAY(StructBlock):
    def __init__(self, block):
        StructBlock.__init__(self, block)
        self.LineStyleCount = ord(self.read(1))
        if self.LineStyleCount == ord('\xff'):
            self.LineStyleCountExtended = le2byte(self.read(2))

        self.LineStyles = []
        if self.block.tag_name in ('DefineShape', 'DefineShape2', 'DefineShape3'):
            for i in range(self.LineStyleCount):
                self.LineStyles.append(LINESTYLE(self.block))
        #elif self.block.tag_name == 'DefineShape4':
        #    self.LineStyles.append(LINESTYLE2(self.block))


"""
SHAPERECORDS には、４種類の ShapeRecord, 
・EndShapeRecord
・StyleChangeRecord
・StraightEdgeRecord
・CurvedEdgeRecord
が連なり、それぞれが byte_aligned されていない
それをパースする
"""
class EndShapeRecord(StructBlock):
    def __init__(self, block):
        StructBlock.__init__(self, block)
        self.TypeFlag = self.read_bits(1)
        self.EndOfShape = self.read_bits(5)

class StyleChangeRecord(StructBlock):
    def __init__(self, block, fill_bits, line_bits):
        StructBlock.__init__(self, block)
        self.TypeFlag = self.read_bits(1)
        self.StateNewStyles = self.read_bits(1)   # New styles flag (only DefineShape2, 3) 
        self.StateLineStyle = self.read_bits(1)
        self.StateFillStyle1 = self.read_bits(1)
        self.StateFillStyle0 = self.read_bits(1)
        self.StateMoveTo = self.read_bits(1)
        if b2i(self.StateMoveTo):
            self.MoveBits = self.read_bits(5)
            self.MoveDeltaX = SB(self.read_bits(b2i(self.MoveBits)))
            self.MoveDeltaY = SB(self.read_bits(b2i(self.MoveBits)))
        if b2i(self.StateFillStyle0):
            self.FillStyle0 = self.read_bits(fill_bits)
        if b2i(self.StateFillStyle1):
            self.FillStyle1 = self.read_bits(fill_bits)
        if b2i(self.StateLineStyle):
            self.LineStyle = self.read_bits(line_bits)
        if b2i(self.StateNewStyles) and False:
            self.FillStyes = FILLSTYLEARRAY(self.block)
            self.LineStyles = LINESTYLEARRAY(self.block)
            self.NumFillBits = self.read_bits(4)
            self.NumLineBits = self.read_bits(4)


class StraightEdgeRecord(StructBlock):
    def __init__(self, block):
        StructBlock.__init__(self, block)
        self.TypeFlag = self.read_bits(1)
        self.StraightFlag = self.read_bits(1)
        self.NumBits = self.read_bits(4)   # 2 less than the actual number
        self.GeneralLineFlag = self.read_bits(1)

        if b2i(self.GeneralLineFlag) == 0:
            self.VertLineFlag = self.read_bits(1)

        self.DeltaX = None
        self.DeltaY = None

        if b2i(self.GeneralLineFlag) == 1 or b2i(self.VertLineFlag) == 0:
            self.DeltaX = SB(self.read_bits(b2i(self.NumBits) + 2))
        if b2i(self.GeneralLineFlag) == 1 or b2i(self.VertLineFlag) == 1:
            self.DeltaY = SB(self.read_bits(b2i(self.NumBits) + 2))

class CurvedEdgeRecord(StructBlock):
    def __init__(self, block):
        StructBlock.__init__(self, block)
        self.TypeFlag = self.read_bits(1)
        self.StraightFlag = self.read_bits(1)
        self.NumBits = self.read_bits(4)
        self.ControlDeltaX = SB(self.read_bits(b2i(self.NumBits) + 2))
        self.ControlDeltaY = SB(self.read_bits(b2i(self.NumBits) + 2))
        self.AnchorDeltaX = SB(self.read_bits(b2i(self.NumBits) + 2))
        self.AnchorDeltaY = SB(self.read_bits(b2i(self.NumBits) + 2))


class SHAPERECORDS(StructBlock):
    def __init__(self, block, NumFillBits, NumLineBits):
        StructBlock.__init__(self, block)
        self.blocks = []
        self.FillBits = NumFillBits
        self.LineBits = NumLineBits

        block.align_byte()
        self.block.shape_records_offset = self.block.pos
        s = self.parse_shape_record()
        while True:
            self.blocks.append(s)
            if isinstance(s, EndShapeRecord):
                break
            s = self.parse_shape_record()
        self.parse_end()

        self.block.shape_records_length = self.length

    def parse_shape_record(self):
        shape_bits = self.get_bits(6)
        type_flag = shape_bits[0]
        if not type_flag:   # Non-edge record flag
            if b2i(shape_bits[1:]) == 0:
                return EndShapeRecord(self.block)
            else:
                return StyleChangeRecord(
                    self.block,
                    self.FillBits,
                    self.LineBits
                    )
        else:   # Edge Record Flag
            if not shape_bits[1]:
                return CurvedEdgeRecord(self.block)
            else:
                return StraightEdgeRecord(self.block)

    @property
    def value(self):
        return Bits(self._value)


class SHAPEWITHSTYLE(StructBlock):
    def __init__(self, block):
        StructBlock.__init__(self, block)
        self.FillStyles = FILLSTYLEARRAY(self.block)
        self.LineStyles = LINESTYLEARRAY(self.block)
        self.NumFillBits = b2i(self.read_bits(4))
        self.NumLineBits = b2i(self.read_bits(4))
        self.ShapeRecords = SHAPERECORDS(self.block, self.NumFillBits, self.NumLineBits)


"""
DefineShape, DefineShape2, DefineShape3, 
DefineShape4 (only SWF 8 or later)
"""
class DefineShape(DefinitionTag):
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        if self.swf and self.swf.flag['PARSE_SHAPE']:
            self.parse()

    def parse(self):
        self.ShapeId = le2byte(self.read(2))   # Shape ID
        self.rect_offset = self.pos
        self.ShapeBounds = RECT()
        self.ShapeBounds.parse(self)
        self.align_byte()
        self.Shapes = SHAPEWITHSTYLE(self)

    def replace_rect(self, rect):
        self.value = self.value[:self.rect_offset] + \
            rect.value + \
            self.value[(self.rect_offset + len(self.ShapeBounds.value)):]
        self.ShapeBounds = rect


class DefineShape2(DefinitionTag):
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        #self.parse()

    def parse(self):
        self.ShapeId = le2byte(self.read(2))    # Shape ID
        self.ShapeBounds = RECT()
        self.ShapeBounds.parse(self)
        # self.Shapes = SHAPEWITHSTYLE(self)


class DefineShape3(DefinitionTag):
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        #self.parse()

    def parse(self):
        self.ShapeId = le2byte(self.read(2))    # Shape ID
        self.ShapeBounds = RECT()
        self.ShapeBounds.parse(self)
        # self.Shapes = SHAPEWITHSTYLE(self)


class DefineMorphShape(DefinitionTag):
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        self.parse()

    def parse(self):
        pass
        #self.ShapeId = le2byte(self.read(2))    # Shape ID
        #self.ShapeBounds = RECT()
        #self.ShapeBounds.parse(self)
        # self.Shapes = SHAPEWITHSTYLE(self)


class SetBackgroundColor(SwfBlock):
    def __init__(self, *args):
        SwfBlock.__init__(self, *args)
        #self.rgb = RGB(self)


class End(SwfBlock):
    def __init__(self, *args):
        SwfBlock.__init__(self, *args)


class ShowFrame(SwfBlock):
    def __init__(self, *args):
        SwfBlock.__init__(self, *args)


class DefineFont2(DefinitionTag):
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        # self.parse()
    
    def parse(self):
        self.character_id = le2byte(self.read(2))  # FontID


class DefineFontName(DefinitionTag):
    def __init__(self, *args):
        DefinitionTag.__init__(self, *args)
        #self.parse()
    
    def parse(self):
        self.character_id = le2byte(self.read(2))  # FontID
        self.FontName = self.read_string()
        self.FontCopyright = self.read_string()


"""
PlaceObject は SWF3 以降滅多に用いられないようなので記述せず
PlaceObject2 が Flash Lite 1.1 では一般的
PlaceObject3 は Flash Player 9.0.45.0 以降なので今のところはいらない
"""
class PlaceObject2(SwfBlock):
    _serialize_attr_ = {
        MOVIECLIP_V1: (
            'tag',
            'length',
            'content_offset',
            'value',
            'depth_offset',
            'depth',
            'target_character_id_offset',
            'target_character_id',
            'matrix_offset',
            'matrix',
            'color_transform',
            'f_place_has_name',
            'name_offset',
            'name')
        }

    def __init__(self, *args):
        SwfBlock.__init__(self, *args)
        if self.IS_PARSE:
            self.parse()

    def serialize(self, serializer_version):
        # シリアライズ関数を PlaceObject2 専用にオーバーライドする
        ret = []
        for attr in self._serialize_attr_[serializer_version]:
            if hasattr(self, attr):
                if attr in ('matrix', 'color_transform'):
                    ret.append(getattr(self, attr).serialize())
                else:
                    ret.append(getattr(self, attr))
            else:
                ret.append(None)
        return ret
    
    def deserialize(self, serializer_version, tpl):
        # except basic attributes (tag, length, content_offset, value)
        self.depth_offset, \
        self.depth, \
        self.target_character_id_offset, \
        self.target_character_id, \
        self.matrix_offset, \
        matrix, \
        color_transform, \
        self.f_place_has_name, \
        self.name_offset, \
        name = tpl

        if matrix:
            self.matrix = MATRIX().deserialize(matrix)
        if color_transform:
            self.color_transform = CXFORMWITHALPHA().deserialize(color_transform)
        if name:
            self.name = name

    def copy(self, swf=None, base_block=None):
        """
        PlaceObject2 のパースはコストがかかるので、
        copy する際はパースしないように関数をオーバーライドする
        """
        if not base_block:
            base_block = self.base_block

        new = self.__class__(
            self.tag,
            self.length,
            self.content_offset,
            self.value,
            base_block,
            swf,
            False)    # IS_PARSE
        # attribute をコピーする
        for attr in ('matrix', 'color_transform'):
            if hasattr(self, attr):
                setattr(new, attr, getattr(self, attr).copy())
        for attr in (
            'depth_offset',
            'depth',
            'target_character_id_offset',
            'target_character_id',
            'matrix_offset',
            'name_offset',
            'name',
            ):
            if hasattr(self, attr):
                setattr(new, attr, getattr(self, attr))
        return new

    def parse(self):
        # See: http://www.m2osw.com/swf_tag_placeobject2
        # Flash Lite 1.1 (Flash Version 4) を想定したコード

        self.f_place_reserved, \
        self.f_place_has_clipping_depth, \
        self.f_place_has_name, \
        self.f_place_has_ratio, \
        self.f_place_has_color_transform, \
        self.f_place_has_matrix, \
        self.f_place_has_character, \
        self.f_place_has_move = self.read_bits(8)

        self.depth_offset = self.pos
        self.depth = le2byte(self.read(2))

        if self.f_place_has_character:
            self.target_character_id_offset = self.pos
            self.target_character_id = le2byte(self.read(2))
        else:
            self.target_character_id = None
        
        if self.f_place_has_matrix:
            self.matrix_offset = self.pos
            self.matrix = MATRIX()
            self.matrix.parse(self)
            self.align_byte()

        if self.f_place_has_color_transform:
            self.color_transform = CXFORMWITHALPHA()
            self.color_transform.parse(self)

        if self.f_place_has_ratio:
            f_ratio = le2byte(self.read(2))

        if self.f_place_has_name:
            self.name_offset = self.pos
            self.name = self.read_string()

        if self.f_place_has_clipping_depth:
            if DEBUG: print "\tClip Depth:", le2byte(self.read(2))

    def replace_matrix(self, matrix):
        diff = len(matrix) - len(self.matrix)
        
        self.value = self.value[:self.matrix_offset] + \
            matrix.value + self.value[(self.matrix_offset + len(self.matrix)):]
        self.matrix = matrix
        
        # PlaceObject2 自体のヘッダーの長さを変更する
        self.set_length(len(self.value) - self.content_offset)
        if self.base_block:
            self.base_block.update_value()

    def set_target_character_id(self, num):
        assert isinstance(num, int)
        assert hasattr(self, 'target_character_id_offset')
        self.value = \
            self.value[:self.target_character_id_offset] + _h16(num) + \
            self.value[(self.target_character_id_offset + 2):]
        self.target_character_id = num

    def set_depth(self, num):
        assert isinstance(num, int)
        self.value = \
            self.value[:self.depth_offset] + _h16(num) + \
            self.value[(self.depth_offset + 2):]
        self.depth = num
        
    def set_name(self, name):
        if self.f_place_has_name:
            new_name = name + '\x00'
            self.value = \
                self.value[:self.name_offset] + new_name + \
                self.value[(self.name_offset + len(self.name) + 1):]
            self.name = name
            self.set_length(len(self.value) - self.content_offset)
        else:
            pass

