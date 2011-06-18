#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tomato.tests
"""
import unittest
import msgpack
import time

try:
    from PIL import Image
except ImportError:
    import Image

from tomato.swf_processor import Swf
from tomato.exceptions_tomato import MovieClipDoesNotExist
from tomato.utils import bits_list2string, Bits, SignedBits as SB, FixedPointBits as FB, MATRIX


def test_matrix(scale=None, rotate=None, translate=(0,0)):
    m1 = MATRIX().generate(
        scale=scale,
        translate=translate,
        rotate=rotate
        )
    m2 = MATRIX()
    if scale:
        m2.setattr_value('scale_x', scale[0])
        m2.setattr_value('scale_y', scale[1])
    if rotate:
        m2.setattr_value('rotate_skew0', rotate[0])
        m2.setattr_value('rotate_skew1', rotate[1])
    if translate:
        m2.setattr_value('translate_x', translate[0])
        m2.setattr_value('translate_y', translate[1])
    m2.generate_bits()
    return m1.value == m2.value


class TestSwfProcessor(unittest.TestCase):
    def setUp(self):
        self.swf_bitmap = Swf(open('sample/bitmap/bitmap.swf').read())
        self.swf_tank = Swf(open('sample/mc/tank.swf').read())

    def test_bits(self):
        int_num = 31415
        signed_num = -27182
        float_num = 1.6180339
        self.assertEqual(int_num, int(Bits(int_num)))
        self.assertEqual(signed_num, int(SB(signed_num)))
        self.assertAlmostEqual(float_num, float(FB(float_num)), 4)

    def test_bits2string(self):
        spam_string = "This is a spam!"
        self.assertEqual(spam_string, bits_list2string([Bits(spam_string)]))

    def test_matrixes(self):
        self.assertEqual(True, test_matrix())
        self.assertEqual(True, test_matrix(translate=(1250, 744)))
        self.assertEqual(True, test_matrix(scale=(2,4, 3.7)))
        self.assertEqual(True, test_matrix(scale=(-55, -66), translate=(1250, 744)))
        self.assertEqual(True, test_matrix(rotate=(-2.4, -3.8)))
        self.assertEqual(True, test_matrix(rotate=(33, 66), translate=(1250, 744)))
        self.assertEqual(True, test_matrix(scale=(77, 44), rotate=(1,5, -3.7)))
        self.assertEqual(True, test_matrix(translate=(1250, 744), rotate=(-1, -1), scale=(-3, -1)))

    def test_fields_io_serialize_and_deserialize(self):
        m1 = MATRIX().generate(
            scale=(2.4, 3.7),
            translate=(1500, 1500))
        tpl = m1.serialize()
        m2 = MATRIX().deserialize(tpl)
        self.assertEqual(m1.value, m2.value)

    def test_getting_movie_clip(self):
        self.assertNotEqual(None, self.swf_tank.get_movie_clip('kombu'))
        self.assertRaises(MovieClipDoesNotExist, 
            self.swf_bitmap.get_movie_clip, 'this_is_not_spam')

    def test_delete_movie_clip(self):
        self.swf_tank.delete_movie_clip('kombu')
        self.swf_tank.write(open('sample/mc/tank_without_kombu.swf', 'w'))

    def test_copy_swf(self):
        c_tank = self.swf_tank.copy()
        c_bitmap = self.swf_bitmap.copy()
        self.assertEqual(c_tank.write(), self.swf_tank.write())
        self.assertEqual(c_bitmap.write(), self.swf_bitmap.write())
        c_tank.write(open('sample/mc/copy_tank.swf', 'w'))
        c_bitmap.write(open('sample/mc/copy_bitmap.swf', 'w'))


if __name__ == '__main__':
    unittest.main()
