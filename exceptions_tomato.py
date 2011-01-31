# -*- coding: utf-8 -*-
"""
Tomato.exceptions

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

# Bit 演算に関連するエラー
class BitsError(Exception): pass
class NegativeIntError(Exception): pass
class AlignError(Exception): pass

# MovieClip 取得に関するエラー
class MovieClipDoesNotExist(Exception): pass

# PlaceObject2 取得に関するエラー
class PlaceObject2DoesNotExist(Exception): pass

# 不正なキャラクター ID に関するエラー
class InvalidCharacterId(Exception): pass

# 文字列の最後に \0 (\x00) がない場合のエラー
class NullCharacterDoesNotExist(Exception): pass
class StringError(Exception): pass

# 不正な SWF ファイルに関するエラー
class InvalidSWF(Exception): pass


def is_valid_swf(swf):
    if swf[:4] != 'FWS\x04':
        if swf[:3] in ('FWS', 'CWS') and swf[3] != '\x04':
            raise InvalidSWF("Not Flash Lite 1.1 (Version: %d)" % ord(swf[3]))
        else:
            raise InvalidSWF("Invalid Flash File")

