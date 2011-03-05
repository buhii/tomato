#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tomato.swf_processor
 - Flash Processor (for Flash Lite 1.1)

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
import os
import sys
import time
import msgpack

from collections import defaultdict

from tomato.utils import _h32, _h16, le2byte, le4byte, get_fixed_point_number, \
     Bits, s2b, b2i, flatten_defaultdict_set, \
     RECT, MATRIX, SERIALIZER_MOVIECLIP_V1 as MOVIECLIP_V1
from tomato.parser import SwfBlockParser, deserialize_blocks
from tomato.structure import StreamIO, DefinitionTag, PlaceObject2, DefineSprite, MovieClip
from tomato.exceptions_tomato import MovieClipDoesNotExist, is_valid_swf
from tomato.swf_injector import create_swf


DEBUG = False


class Swf(StreamIO):
    def __init__(self, value=None, PARSE_SHAPE=False):
        if value:
            is_valid_swf(value)
            StreamIO.__init__(self, value)

            # Swf をパースする際の設定
            self.flag = {}
            self.flag['PARSE_SHAPE'] = PARSE_SHAPE   # DefineShape 関連をパースする

            # Parse Value
            self.parse_swfhead()
            self.blocks = SwfBlockParser(self.swf_tail, swf=self).blocks
            self.character_dict = self.get_character_dict()
        else:
            # デシリアライズの際に用いる
            StreamIO.__init__(self)
        self.inject_params_dict = {}

    def serialize(self, f=None):
        "シリアライズを行う"
        ret = {
            'serializer_version': MOVIECLIP_V1,
            'rect': self.rect.serialize(),
            'swf_head': self.swf_head,
            'swf_tail': self.swf_tail,
            'blocks': [],
            }
        for block in self.blocks:
            ret['blocks'].append(block.serialize(MOVIECLIP_V1))
        data = msgpack.packb(ret)

        if f:
            f.write(data)
        else:
            return data
    dumps = serialize

    def deserialize(self, data, unpacker=None):
        "デシリアライズを行う"
        if unpacker:
            unpacker.feed(data)
            ret = unpacker.unpack()
        else:
            ret = msgpack.unpackb(data)
        
        serializer_version = ret['serializer_version']
        self.rect = RECT().deserialize(ret['rect'])
        self.swf_head = ret['swf_head']
        self.swf_tail = ret['swf_tail']
        self.flag = {'PARSE_SHAPE': False}
        
        self.blocks = deserialize_blocks(
            swf=self,
            blocks_tpl=ret['blocks'],
            serializer_version=serializer_version)
        self.character_dict = self.get_character_dict()
        return self
    loads = deserialize

    def copy(self):
        "コピーを作る（deepcopy）"
        new = Swf()
        new.rect = self.rect.copy()
        new.swf_head = self.swf_head
        new.swf_tail = self.swf_tail
        new.flag = {'PARSE_SHAPE': False}
        new.blocks = map(lambda b: b.copy(swf=new), self.blocks)
        new.character_dict = new.get_character_dict()
        return new

    def get_character_dict(self):
        # DefinitionTag を列挙する
        ret = {}
        for block in self.blocks:
            if isinstance(block, DefinitionTag):
                ret[block.character_id] = block
        return ret

    def get_movie_clips(self):
        ret = {}
        for character_id, block in self.character_dict.items():
            if isinstance(block, DefineSprite):
                ret[character_id] = MovieClip(
                    swf=self,
                    define_sprite=block,
                    place_object2=None)
        return ret

    def get_movie_clip_name(self):
        """
        MovieClip 名を出力する
        """
        ret = []
        for p in self.search_tags('PlaceObject2'):
            if hasattr(p, 'name'):
                ret.append(p.name)
        return ret

    def get_movie_clip(self, mc_name):
        """
        MovieClip を名前で取得する
        MovieClip の名前はそれを参照している PlaceObject2 の
        name に入っているので PlaceObject2 を参照する
        """            
        place_object2 = None
        for p in self.search_tags('PlaceObject2'):
            if hasattr(p, 'name'):
                if p.name == mc_name:
                    place_object2 = p
                    break
        if place_object2:
            return MovieClip(
                swf=self,
                place_object2=place_object2,
                define_sprite=self.character_dict[place_object2.target_character_id]
                )
        else:
            raise MovieClipDoesNotExist(
                'MovieClip \"%s\" does not exist!' % mc_name)

    def get_movie_clip_from_parent(self, parent_mc_name, child_mc_name):
        """
        親 MovieClip 内に含まれる 子 MovieClip を取得する
        """
        parent_mc_place_objecet2, child_mc_place_object2 = None, None
        for p in self.search_tags('PlaceObject2'):
            if hasattr(p, 'name'):
                if p.name == parent_mc_name:
                    parent_mc_place_object2 = p
                    break
        if not parent_mc_place_object2:
            raise MovieClipDoesNotExist(
                'Parent MovieClip \"%s\" does not exist!' % parent_mc_name)
        parent_define_sprite = self.character_dict[
            parent_mc_place_object2.target_character_id]
        
        for tag in parent_define_sprite.blocks:
            if isinstance(tag, PlaceObject2) and hasattr(tag, 'name'):
                if tag.name == child_mc_name:
                    child_mc_place_object2 = tag
                    break
        if child_mc_place_object2:
            return MovieClip(
                swf=self,
                place_object2=child_mc_place_object2,
                define_sprite=self.character_dict[
                    child_mc_place_object2.target_character_id]
                )
        else:
            raise MovieClipDoesNotExist(
                'Child MovieClip \"%s\" in Parent MovieClip \"%s\" does not exist!'
                % (child_mc_name, parent_mc_name))

    def replace_shape(self, old_shape, new_shape):
        """
        DefineShape (2,3,4) の置き換えを行う
        FillStyle に ClippedBitmap として画像が置けるが
        それの置き換えはまだできていない
        """
        old_shape_index = self.blocks.index(old_shape)
        old_shape_id = old_shape.character_id

        new_shape = new_shape.copy()
        new_shape.set_character_id(old_shape_id)
        self.blocks[old_shape_index] = new_shape
        return new_shape

    def get_same_definition_tag(self, new_dt):
        """
        new_dt と同じ DefinitionTag が存在するかどうか調べる
        """
        for character_id, dt in self.character_dict.items():
            if is_same_definition_tags(dt, new_dt):
                return character_id
        return None

    def get_all_definition_tags(self, ds, depth=1, dts=defaultdict(set)):
        """
        DefineSprite(ds) 内の DefinitionTag を全て列挙する
        """
        for block in ds.blocks:
            if isinstance(block, PlaceObject2) and block.target_character_id != None:
                ch_id = block.target_character_id
                if not ch_id in flatten_defaultdict_set(dts):
                    dts[depth].add(ch_id)
                    if not ch_id in self.character_dict:  # ???
                        continue
                    if isinstance(self.character_dict[ch_id], DefineSprite):
                        self.get_all_definition_tags(
                            self.character_dict[ch_id],
                            depth + 1,
                            dts)
        return dts

    def insert_definition_tag(self, new_dt, before_dt):
        """
        dt を before_dt の前に追加する
        """
        new_dt_id = self.get_new_character_id()
        new_dt = new_dt.copy(swf=self)
        new_dt.set_character_id(new_dt_id)
        mc_index = self.blocks.index(before_dt)
        self.blocks = \
            self.blocks[:mc_index] + [new_dt] + \
            self.blocks[mc_index:]
        self.character_dict[new_dt_id] = new_dt
        return new_dt_id

    def replace_movie_clip(self, old_mc, new_mc):
        """
        MovieClip を置き換える
        """
        if isinstance(old_mc, str):
            old_mc = self.get_movie_clip(old_mc)

        assert isinstance(old_mc, MovieClip)
        assert isinstance(new_mc, MovieClip)
        old_mc.get_place_object2()

        ds_index = self.blocks.index(old_mc.define_sprite)
        new_ds = new_mc.define_sprite.copy(new_mc.swf)

        # new_mc の DefineSprite を間に追加する
        self.blocks.insert(ds_index, new_ds)
        new_ds_id = self.get_new_character_id()
        self.character_dict[new_ds_id] = new_ds
        new_ds.set_character_id(new_ds_id)

        old_mc.place_object2.set_target_character_id(new_ds_id)
        if old_mc.place_object2.base_block:
            old_mc.place_object2.base_block.update_value()

        # new_mc 内の Definition Tags を self にコピーする
        new_mc.copy_inside_definition_tags(self, new_ds)

        ret_mc = MovieClip(
            swf=self,
            define_sprite=new_ds,
            place_object2=old_mc.place_object2)
        return ret_mc

    def vanish_movie_clip(self, mc):
        # MovieClip を画面上の参照画像も含めて削除する
        # self.blocks から削除すればファイルには含まれなくなる

        def vanish_define_sprite(swf, ds):
            for block in ds.blocks:
                if isinstance(block, PlaceObject2) and block.target_character_id:
                    dt = swf.character_dict[block.target_character_id]
                    if isinstance(dt, DefineSprite):
                        vanish_define_sprite(swf, dt)
                    else:
                        if dt in swf.blocks:
                            swf.blocks.remove(dt)
            if ds in swf.blocks:
                swf.blocks.remove(ds)
        vanish_define_sprite(self, mc.define_sprite)

    def replace_movie_clip_with_vanishing(self, old_mc, new_mc):
        if isinstance(old_mc, str):
            old_mc = self.get_movie_clip(old_mc)
        ret_mc = self.replace_movie_clip(old_mc, new_mc)
        self.vanish_movie_clip(old_mc)
        return ret_mc

    def delete_movie_clip(self, mc):
        """
        SWF 内の MovieClip を削除する
        画面の参照（PlaceObject2）を削除する形で行う
        """
        def delete_mc_place_object2(mc):
            po2 = mc.place_object2
            base_block = po2.base_block
            if base_block:
                base_block.blocks.remove(po2)
                base_block.update_value()
            else:
                self.blocks.remove(po2)

        if isinstance(mc, str):
            mc = self.get_movie_clip(mc)
            delete_mc_place_object2(mc)
        elif isintance(mc, MovieClip):
            if mc.place_object2:
                delete_mc_place_object2(mc)
                self.blocks.remove(mc.place_object2)
            else:
                mc.get_place_object2()
                delete_mc_place_object2(mc)

    def get_new_character_id(self):
        """
        SWF 内で用いられていない character_id を取得する
        現状 character_id には最大 2 ** 16 - 1 = 65535 の ID を振ることができるので、
        とりあえず現状の character_id の中の最大を更新する形で取るようにしてみる
        """
        return max(self.character_dict) + 1

    def search_tags(self, tag_name, blocks = None):
        """
        タグ名のブロックを再帰的に探索する
        """
        ret = []
        if not blocks:
            blocks = self.blocks

        for block in blocks:
            if block.__class__.__name__ == tag_name:
                ret.append(block)
            if hasattr(block, 'blocks'):   # 内部的にさらにブロックが存在すれば
                ret += self.search_tags(tag_name, block.blocks)
        return ret

    def search_root(self, tag_name):
        """
        タグ名のブロックを self.blocks のみで一段のみで調べる
        """
        return filter(lambda b: b.__class__.__name__ == tag_name, self.blocks)

    def print_used_tags(self, blocks=None):
        if not blocks:
            blocks = self.blocks

        ret = set()
        for block in blocks:
            ret.add((block.tag, block.__class__.__name__))
            if hasattr(block, 'blocks'):
                ret.union(self.print_used_tags(block.blocks))
        return ret

    def print_tags(self):
        l = list(self.print_used_tags())
        l.sort()
        for t in l:
            print "%d\t%s" % (t[0], t[1])

    def parse_swfhead(self):
        "Parse File Header."
        self.magic = self.read(3)
        self.version = ord(self.read(1))
        self.file_length = le4byte(self.read(4))

        # RECT ヘッダ（これは 8 byte 目で固定）
        self.rect = RECT()
        self.rect.parse(self)

        # frame 関連
        self.frame_rate = get_fixed_point_number(self.read(2))
        self.frame_count = le2byte(self.read(2))

        # File Header（head）とその後の部分（tail）を分離する
        self.swf_head = self.value[:self.pos]
        self.swf_tail = self.value[self.pos:]
        
        if DEBUG:
            print " Swf Header ".center(60,'-')
            print "magic: %s\nver: %d\nlen: %d\nframe_rate: %f\ncount: %d" % ( \
                self.magic,
                self.version,
                self.file_length,
                self.frame_rate,
                self.frame_count)
            print " Swf Blocks ".center(60, '-')

    def replace_rect(self, rect):
        self.swf_head = self.swf_head[:8] + rect.value + self.swf_head[(8 + self.rect.length):]
        self.rect = rect

    @property
    def size(self):
        return (b2i(self.rect.x_max) / 20, b2i(self.rect.y_max) / 20)

    @property
    def width(self):
        return b2i(self.rect.x_max) / 20

    @property
    def height(self):
        return b2i(self.rect.y_max) / 20

    def update_file_header(self):
        fl = len(self.swf_head)
        for block in self.blocks:
            fl += len(block)

        self.swf_head = self.swf_head[:4] + _h32(fl) + self.swf_head[8:]

    def combine_blocks(self):
        self.update_file_header()
        self.value = self.swf_head + ''.join(map(lambda b: b.value, self.blocks))

    def inject_params(self, params={}):
        self.inject_params_dict = params

    def write(self, f=None):
        # Output Swf
        self.combine_blocks()

        # inject params
        if self.inject_params_dict:
            self.value = create_swf(self.value, self.inject_params_dict)

        if f:
            f.write(self.value)
        else:
            return self.value


def is_same_definition_tags(ds1, ds2):
    if ds1.hash != ds2.hash:
        return False
    else:
        if isinstance(ds1, DefineSprite) and isinstance(ds2, DefineSprite):
            """
            この場合は DefineSprite 同士が本当に同じか、
            blocks 内の PlaceObject2 の参照先を見ていき詳細に調べる必要がある

            しかしそれには深いところまでパースする必要があるため、
            アニメーション自体が同じかどうか決定するのを放棄する。
            Swf の容量は若干重たくなるが、置き換えの計算は高速になる
            """
            return False
        else:
            return True


if __name__ == '__main__':
    tank = Swf(open('sample/mc/tank.swf').read())
    fish_white = Swf(open('sample/mc/fish_white.swf').read())
    fish_red = Swf(open('sample/mc/fish_red.swf').read())

    mc_white = fish_white.get_movie_clip('white')
    mc_red = fish_red.get_movie_clip('red')

    tank.replace_movie_clip('fish1', mc_red)
    tank.replace_movie_clip('fish2', mc_white)
    tank.write(open('sample/mc/out.swf', 'w'))
