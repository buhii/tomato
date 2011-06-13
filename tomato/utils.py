# -*- coding: utf-8 -*-
"""
Tomato.utils

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
import struct
from bitarray import bitarray
from array import array
from math import ceil
from tomato.exceptions_tomato import BitsError, NegativeIntError, AlignError

# serializer version
SERIALIZER_MOVIECLIP_V1 = 'MCV1'


def _h32(v):
    return struct.pack('<L', v)


def _h16(v):
    return struct.pack('<H', v)


def le2byte(s):
    "LittleEndian to 2 Byte"
    return struct.unpack('<H', s)[0]


def le4byte(s):
    "LittleEndian to 4 Byte"
    return struct.unpack('<L', s)[0]


def get_fixed_point_number(v):
    """
    固定小数点数 (short fixed)
    (8bit).(8bit) の形になっており、FixedPointBits と違う
    """
    _decimal, _integer = ord(v[0]), ord(v[1])
    while _decimal > 1:
        _decimal /= 10.0
    return _integer + _decimal


def _oct(num):
    return (num + 7) & -8

def _oct_ceil(num):
    return ((num + 7) & -8) / 8

"""
Bit Values
"""
def _bin(num):
    if num == 0:
        ret = bitarray('0', endian='big')
    else:
        ret = bitarray(endian='big')
        nums = array('B')
        while num != 0:
            nums.append(num % 256)
            num >>= 8
        for n in reversed(nums):
            ret.fromstring(chr(n))
        ret = _bit_cut(ret)
    return ret


def _bit_cut(b):
    """
    文字から bit 列に直す際に0が残ってしまうので
    最初に出現する 0 のビット列を消す
    文字 C (99): 01000011
               -> 1000011
    """
    pos = -1
    for i, f in enumerate(b):
        if not f:
            pos = i
        else:
            break
    return b[(pos + 1):]


def string2bits(s):
    c = bitarray(endian='big')
    c.fromstring(s)
    return c
s2b = string2bits


def bin2int(l):
    return reduce(lambda a, b: a + a + b, l, 0)
b2i = bin2int


def flatten_defaultdict_set(defaultdict_set):
    x = set()
    for ds in defaultdict_set.values():
        x.update(ds)
    return x


def bits_list2string(l):
    tmp_bits = bitarray(endian='big')
    if isinstance(l, bitarray):
        tmp_bits = l
    else:
        for e in l:
            if isinstance(e, Bits):
                tmp_bits += e.bits
            elif isinstance(e, bitarray):
                tmp_bits += e
    bits = Bits(tmp_bits)
    bits.align(int(ceil(len(bits) / 8.0)) * 8, after=True)
    return bits.bits.tostring()


def dump_bits(bits):
    print "bits length: %d" % len(bits)
    for i, b in enumerate(range(len(bits))[::8]):
        print "bits[%04d]:  %r" % (i, bits[b: b + 8])


def bits2string(bits):
    len_after = _oct_ceil(len(bits)) * 8
    ret = bits + bitarray('0', endian='big') * (len_after - len(bits))
    return ret.tostring()
b2s = bits2string


class FieldsIO(object):
    """
    FieldsIO を継承することで BitFields 等を
    python で擬似的に記述できるようにする

    _fields_ = (
        (attribute, controller, status),
        ...
        )

    * attribute には、BitField の名前が来る
    * controller には、attribute の Type か 数値が来る
      - Type だと attribute を status に従って read or write
      - 数値 だと 条件式となり、attribute == controller で、
        status の文が実行される
    """
    __slots__ = ('rests', )
    def parse(self, block):
        self.parse_fields(self._fields_, block)

    def parse_fields(self, fields, block):
        "パース用内部関数"
        for attr, ctrl, stat in fields:
            if isinstance(ctrl, int):   # 条件文
                if self.getattr_value(attr) == ctrl:
                    self.parse_fields(stat, block)   # 再帰的にパースする
                else:
                    # flag が立っていないので値自体が存在しない
                    for a, c, s in stat:
                        self.setattr_bit(a, None)
            else:
                """
                control が Type. status の長さ分のビットフィールドを取る
                status が数値のときは固定長、文字であれば可変長
                """
                if isinstance(stat, int):   # 固定長
                    bit_len = stat
                else:   # 可変長
                    bit_len = self.getattr_value(stat)
                
                if bit_len == 0:
                    self.setattr_bit(attr, bitarray('0', endian='big'))
                else:
                    self.setattr_bit(attr, block.read_bits(bit_len))

    def generate_bits(self):
        "構造体のビット列を生成する"
        self.make_restrictions()   # 制約条件の生成
        for attr, align in self.rests.items():
            if isinstance(align, str):
                align = self.getattr_value(align)
            self.setattr_value(attr, self.getattr_value(attr), align)

    def make_restrictions(self, fields=None):
        "構造体のビット列を生成する際に attribute に対して制約条件を決定する"
        if not fields:
            self.rests = {}
            fields = self._fields_
        for attr, ctrl, stat in reversed(fields):
            if isinstance(ctrl, int):
                "条件文内の attr がすでに存在していればあらかじめ bit 値を生成しておく"
                self.setattr_bit(attr, bitarray('0', endian='big'))   # False
                for a, c, s in stat:
                    if hasattr(self, a) and self.getattr_bit(a) != None:
                        self.setattr_bit(attr, bitarray('1', endian='big'))   # True
                        break
                self.make_restrictions(stat)
            elif hasattr(self, attr) and getattr(self, attr) != None:
                """
                (attr, ctrl=type, stat=bit_length) なのでサイズ制約を決定
                ex. ('n_rotate_bits', UB, 5)
                    ('has_scale', UB, 1)
                    ('scale_x', FB, 'n_scale_bits')
                """
                if stat != 1:   # flag はすでに上記で設定しているので制約条件は設定しない
                    self.rests[attr] = stat
                if isinstance(stat, str):
                    "可変長サイズの場合は、attr の長さに応じてあらかじめ stat に bit 値を設定しておく"
                    if not hasattr(self, stat) or getattr(self, stat) == None:
                        self.setattr_value(stat, 0)
                    self.setattr_value(
                        stat,
                        max(self.getattr_value(stat),
                            len(self.getattr_bit(attr))))
            else:
                setattr(self, attr, None)

    def setattr_bit(self, attr, bit_value):
        return setattr(self, attr, bit_value)

    def getattr_bit(self, attr):
        return getattr(self, attr)

    def setattr_value(self, attr, value, bit_length=None):
        if value == None:
            setattr(self, attr, None)
        else:
            klass = self._types_[attr]
            setattr(self, attr, klass.write(value, bit_length))

    def getattr_value(self, attr):
        klass = self._types_[attr]
        return klass.read(getattr(self, attr))

    @property
    def value(self):
        ret = bitarray(endian='big')
        for b in filter(lambda a: a, map(lambda x: getattr(self, x), self.__slots__)):
            ret.extend(b)
        return b2s(ret)

    @property
    def length(self):
        return len(self.value)

    def __len__(self):
        return len(self.value)

    def copy(self):
        new = self.__class__()
        for attr in self.__slots__:
            setattr(new, attr, getattr(self, attr))
        return new

    def __getstate__(self):
        return dict((attr, getattr(self, attr)) for attr in self.__slots__)
    
    def __setstate__(self, dict):
        for attr, value in dict.items():
            setattr(self, attr, value)

    def serialize(self):
        ret = []
        for t in [getattr(self, attr) for attr in self.__slots__]:
            if not t:
                ret.append(None)
            else:
                ret.append(t.to01())
        return ret

    def deserialize(self, tpl):
        for i, attr in enumerate(self.__slots__):
            if tpl[i]:
                setattr(self, attr, bitarray(tpl[i], endian='big'))
            else:
                setattr(self, attr, None)
        return self


class UB(object):
    @classmethod
    def read(cls, val):
        return b2i(val)

    @classmethod
    def write(cls, num, align=None):
        raw_bits = _bin(num)
        if align == None: return raw_bits
        else: return cls.align(raw_bits, align)

    @classmethod
    def align(cls, bits, align):
        if align < len(bits):
            raise AlignError('Illegal align number: %d -> %d' % (len(bits), align))
        else:
            return bitarray('0' * (align - len(bits)), endian='big') + bits


class SB(object):
    @classmethod
    def read(cls, val):
        if len(val) == 0: return 0
        if val[0] == 1:
            return -((1 << len(val)) - b2i(val))
        else:
            return b2i(val)

    @classmethod
    def write(cls, num, align=None):
        tmp = bitarray('0', endian='big')
        if num >= 0:
            tmp.extend(_bin(num))
        else:
            tmp.extend(_bin(-num))
            tmp.invert()
            tmp = _bin(b2i(tmp) + 1)
        if align == None: return tmp
        else: return cls.align(tmp, align)

    @classmethod
    def align(cls, bits, align):
        if align < len(bits):
            raise AlignError('Illegal align number: %d -> %d' % (len(bits), align))
        else:
            b = '1' if bits[0] else '0'
            return bitarray(b * (align - len(bits)), endian='big') + bits


class FB(object):
    @classmethod
    def read(cls, val):
        return SB.read(val) / float(1 << 16)

    @classmethod
    def write(cls, num, align=None):
        tmp = SB.write(int(ceil(num * (1 << 16))))
        if align == None: return tmp
        else: return SB.align(tmp, align)


class UI(object):
    pass


def make_slots(fields):
    ret = []
    for attr, ctrl, stat in fields:
        if isinstance(ctrl, int):
            for a, c, s in stat:
                ret.append(a)
        else:
            ret.append(attr)
    return tuple(ret)


def make_type_dict(fields):
    ret = {}
    for attr, ctrl, stat in fields:
        if isinstance(ctrl, int):
            for a, c, s in stat:
                ret[a] = c
        else:
            ret[attr] = ctrl
    return ret


class RECT(FieldsIO):
    _fields_ = (
        ('nbits', UB, 5),
        ('x_min', SB, 'nbits'),
        ('x_max', SB, 'nbits'),
        ('y_min', SB, 'nbits'),
        ('y_max', SB, 'nbits'),
    )
    _types_ = make_type_dict(_fields_)
    __slots__ = make_slots(_fields_)


class CXFORMWITHALPHA(FieldsIO):
    _fields_ = (
        ('has_add_terms', UB, 1),
        ('has_mult_terms', UB, 1),
        ('nbits', UB, 4),
        ('has_mult_terms', 1, (
            ('red_mult_term', SB, 'nbits'),
            ('green_mult_term', SB, 'nbits'),
            ('blue_mult_term', SB, 'nbits'),
            ('alpha_mult_term', SB, 'nbits'),
            )),
        ('has_add_terms', 1, (
            ('red_add_term', SB, 'nbits'),
            ('red_add_term', SB, 'nbits'),
            ('red_add_term', SB, 'nbits'),
            ('red_add_term', SB, 'nbits'),
            )),
        )
    _types_ = make_type_dict(_fields_)
    __slots__ = make_slots(_fields_)


class MATRIX(FieldsIO):
    _fields_ = (
        ('has_scale', UB, 1),
        ('has_scale', 1, (
            ('n_scale_bits', UB, 5),
            ('scale_x', FB, 'n_scale_bits'),
            ('scale_y', FB, 'n_scale_bits'),
            )),
        ('has_rotate', UB, 1),
        ('has_rotate', 1, (
            ('n_rotate_bits', UB, 5),
            ('rotate_skew0', FB, 'n_rotate_bits'),
            ('rotate_skew1', FB, 'n_rotate_bits'),
            )),
        ('n_translate_bits', UB, 5),
        ('translate_x', SB, 'n_translate_bits'),
        ('translate_y', SB, 'n_translate_bits'),
    )
    _types_ = make_type_dict(_fields_)
    __slots__ = make_slots(_fields_)

    def generate(self, scale=None, rotate=None, translate=(0,0)):
        s = self.setattr_value
        if scale:
            s('scale_x', scale[0])
            s('scale_y', scale[1])
        if rotate:
            s('rotate_skew0', rotate[0])
            s('rotate_skew1', rotate[1])
        if translate:
            s('translate_x', translate[0])
            s('translate_y', translate[1])
        self.generate_bits()
        return self


class Bits(object):
    __slots__ = ('bits',)
    def __init__(self, value):
        self.bits = bitarray(endian='big')
        if isinstance(value, str):
            self.fromstring(value)
        elif isinstance(value, bitarray):
            self.fromlist(value)
        elif isinstance(value, int):
            self.fromint(value)
        elif isinstance(value, array):
            self.bits = value

    def __str__(self):
        return str(int(self))

    def __len__(self):
        "bit列の長さを返す"
        return len(self.bits)
    
    def __getitem__(self, index):
        return self.bits[index]

    def __getslice__(self, index1, index2):
        return self.__class__(self.bits[index1:index2])

    def __int__(self):
        return self.get_int()
        
    def __list__(self):
        return self.bits

    def get_int(self):
        return bin2int(self.bits)

    def fromstring(self, value):
        self.bits.fromstring(value)

    def fromlist(self, value):
        self.bits = value

    def fromint(self, value):
        self.bits = self.unsigned_int2bits(value)

    def unsigned_int2bits(self, num):
        if num < 0:
            raise NegativeIntError('Illegal negative value')
        else:
            return _bin(num)
    
    def align(self, num, after=False):
        if num < len(self.bits):
            raise AlignError('Illegal align number: %d -> %d' % (len(self.bits), num))
        else:
            if after:
                self.bits = self.bits + bitarray('0', endian='big') * (num - len(self.bits))
            else:
                self.bits = bitarray('0', endian='big') * (num - len(self.bits)) + self.bits

    def __getstate__(self):
        return {'bits': self.bits}

    def __setstate__(self, dict):
        for attr, value in dict:
            setattr(self, attr, value)

class SignedBits(Bits):
    """
    符号付き整数を表現するクラス
    2 の補数
    """
    def __init__(self, value):
        __slots__ = ('bits',)
        if isinstance(value, Bits):
            Bits.__init__(self, value.bits)
        elif isinstance(value, int):
            Bits.__init__(self, self.signed_int2bits(value))
        else:
            Bits.__init__(self, value)
       
    def __int__(self):
        if not self.bits: return 0

        if self.bits[0] == 1:
            # 二の補数．最初のビットが 1 であれば負の値になる
            return -((1 << len(self)) - self.get_int())
        else:
            return self.get_int()

    def signed_int2bits(self, num):
        if num >= 0:
            return bitarray('0', endian='big') + _bin(num)
        else:
            tmp = bitarray('0', endian='big') + self.unsigned_int2bits(-num)
            tmp.invert()
            return _bin(bin2int(tmp) + 1)

    def align(self, num, after=False):
        if num < len(self.bits):
            raise AlignError('Illegal align number: %d -> %d' % (len(self.bits), num))
        else:
            b = '1' if self.bits[0] else '0'
            if after:
                self.bits = self.bits + bitarray(b, endian='big') * (num - len(self.bits))
            else:
                self.bits = bitarray(b, endian='big') * (num - len(self.bits)) + self.bits


class FixedPointBits(Bits):
    """
    固定小数点数を表現するクラス
      xbit       -> 整数部
      残り 16bit -> 少数部
    """
    def __init__(self, value):
        __slots__ = ('bits',)
        if isinstance(value, Bits):
            Bits.__init__(self, value.bits)
        elif isinstance(value, float):
            Bits.__init__(self, self.fb2bits(value).bits)
        else:
            Bits.__init__(self, value)

    def __float__(self):
        return int(SignedBits(self.bits)) / float(1 << 16)

    def fb2bits(self, num):
        return SignedBits(int(ceil(num * (1 << 16))))
