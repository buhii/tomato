# -*- coding: utf-8 -*-
"""
Tomato.swf_injector

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

import struct
import sys
import zlib

from utils import _h32, _h16

def _calctaglen(d, encode_option):
    num = 0
    for k in d:
        value = unicode(d[k]).encode(encode_option, 'ignore')
        num += len(k) + len(value) + 11
    return num + 1

def _maketag(d, encode_option):
    tag = '\x3f\x03'
    tag += _h32(_calctaglen(d, encode_option))
    for k in d:
        value = unicode(d[k]).encode(encode_option, 'ignore')
        tag += '\x96' + _h16(len(k)+2) + '\x00' + k + '\x00'
        tag += '\x96' + _h16(len(value)+2) + '\x00' + value + '\x00'
        tag += '\x1d'
    tag += '\x00'
    return tag

def create_swf(base_swf, params):
    "パラメーターを埋め込んだ Flash lite 1.1/2.0 ファイルを生成"
    # 圧縮されている場合は展開する
    decomp_swf = decompress(base_swf)
    
    # パラメーターを埋め込む
    tag = _maketag(params, get_encode(decomp_swf))
    rectbit = ord(decomp_swf[8]) >> 3
    head_len = int(((( 8 - ((rectbit*4+5)&7) )&7)+ rectbit*4 + 5 )/8) + 12 + 5;
    head = decomp_swf[:head_len]
    tail = decomp_swf[head_len:]
    newhead = head[:4] + _h32(len(decomp_swf) + len(tag)) + head[8:]
    out_swf = newhead + tag + tail

    # もし圧縮されていた場合は、圧縮し直す
    out_swf = compress(out_swf)
    return out_swf    

def get_encode(base_swf):
    """
    4バイト目の Flash のバージョンを読み取り判定
    Flash ver.6 以降は、UTF-8
    See https://secure.m2osw.com/swf_tag_file_header
    4バイト目が必要なだけので、base_swf は header でも swf 本体でも良い
    """
    if base_swf[3] < '\x06': # Flash version 6未満 (Flash Lite 1.1) -> cp932
        return 'cp932'
    else:                    # Flash version 6以上 (Flash Lite 2.0) -> utf-8
        return 'utf-8'

def compress(base_swf):
    "圧縮フラグが付いている場合は、圧縮する"
    header = base_swf[:8]
    tail   = base_swf[8:]
    if   header[:3] == 'FWS': # not compressed
        new_tail = tail
    elif header[:3] == 'CWS': # compressed
        new_tail = zlib.compress(tail)
    return header + new_tail

def decompress(base_swf):
    "圧縮フラグが付いている場合は、展開する"
    header = base_swf[:8]
    tail   = base_swf[8:]
    if   header[:3] == 'FWS': # not compressed
        new_tail = tail
    elif header[:3] == 'CWS': # compressed
        # tail を zlib 展開
        # See http://ne.tc/2008/03/13/
        new_tail = zlib.decompress(tail)
    return header + new_tail


if __name__ == '__main__':
    params = {
        'a': 'hoge',
        'b': u'ふが',
        'c': u'ぴよち'
        }
    s = create_swf(open('sample/params/params.swf').read(), params)
    open('sample/params/out.swf', 'w').write(s)


