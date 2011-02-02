===================
SWF の画像置き換え
===================

置き換えを行う
------------------

Tomato は同じ形式（画像フォーマット, 縦横サイズ）の画像を置き換えることができます。

``tomato/sample/bitmap/bitmap.swf`` 内の画像を置き換えてみましょう。

.. raw:: html

    <embed src="../swf/bitmap.swf" embed src="example.swf" type="application/x-shockwave-flash" width="240" height="266" />


``tomato/sample/bitmap/`` 内のディレクトリに以下の青いキノコの画像がありますので、
これを用いて置き換えを行います。

+---------------------------------+-----+-----------------------------------------+---------------------------+
| 抽出画像                        | ID  |  置き換える画像                         | 置き換える画像ファイル名  |
+=================================+=====+=========================================+===========================+
| .. image:: img/bitmap_7.jpg     | 7   | .. image:: img/kinoko_blue.jpg          | kinoko_blue.jpg           |
+---------------------------------+-----+-----------------------------------------+---------------------------+
| .. image:: img/bitmap_8.png     | 8   | .. image:: img/kinoko_blue.png          | kinoko_blue.png           |
+---------------------------------+-----+-----------------------------------------+---------------------------+
| .. image:: img/bitmap_4.png     | 4   | .. image:: img/kinoko_blue_alpha.png    | kinoko_blue_alpha.png     |
+---------------------------------+-----+-----------------------------------------+---------------------------+


ソース
------

.. code-block:: python

    from tomato import SwfImage

    replace_images = {}
    replace_images[7] = open('sample/bitmap/kinoko_blue.jpg').read()
    replace_images[8] = open('sample/bitmap/kinoko_blue.png').read()
    replace_images[4] = open('sample/bitmap/kinoko_blue_alpha.png').read()

    swf = SwfImage(swf=open('sample/bitmap/bitmap.swf').read())

    swf.replace_images(replace_images)
    swf.write(open('sample/bitmap/out.swf', 'wb'))


``SwfImage`` オブジェクトを用いて、SWF ファイルの画像置き換えを行います。
置き換えたい画像の ID と画像ファイルの辞書を作成し、 ``swf.replace_images`` 関数
を用いて画像の置き換えを行います。

最終的に ``swf.write()`` 関数で画像が置き換わった SWF を出力します。


結果
------
.. raw:: html

    <embed src="../swf/bitmap_out.swf" embed src="example.swf" type="application/x-shockwave-flash" width="240" height="266" />


