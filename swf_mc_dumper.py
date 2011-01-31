"""
mc2swf.py
  Swf MovieClip Dumper

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
from swf_processor import Swf
from swf_checker import SwfDepthChecker

def mc2swf(in_swf_filename, out_dir, limit_depth):
    print "parsing %s ..." % in_swf_filename
    in_swf = Swf(open(in_swf_filename).read())
    mc_base_bin = open('sample/mc/blank.swf').read()

    for mc_name in in_swf.get_movie_clip_name():
        # generating MovieClip
        mc_base = Swf(mc_base_bin)
        ret = mc_base.replace_movie_clip("replace_movie_clip", in_swf.get_movie_clip(mc_name))
        ret.place_object2.set_name(mc_name)
        mc_file_str = os.path.join(out_dir, mc_name) + ".swf"
        print "writing %s ..." % mc_file_str
        mc_base.write(open(mc_file_str, 'w'))
        
        # checking MC's depth
        SwfDepthChecker(mc_base, limit_depth)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "usage: python swf_mc_dumper.py [input.swf] [output directory] [limit_depth]"
    else:
        if len(sys.argv) == 4:
            limit_depth = int(sys.argv[3])
        else:
            limit_depth = 3

        mc2swf(sys.argv[1], sys.argv[2], limit_depth)

