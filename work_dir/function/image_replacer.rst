===================
SWF の画像置き換え
===================

SwfImage オブジェクト
---------------------

Tomato は同じ形式（画像フォーマット, 縦横サイズ）の画像を置き換えることができます。


``tomato/sample/bitmap/bitmap.swf`` 内の画像を置き換えてみましょう。

.. raw:: html

    <embed src="../swf/bitmap.swf" embed src="example.swf" type="application/x-shockwave-flash" width="240" height="266" />


``tomato/sample/bitmap/`` 内のディレクトリに以下の青いキノコの画像がありますので、
これを用いて置き換えを行います。

注意しなければならないことは、置き換え元と先の画像フォーマットは
**同一** でなければならないということです。

まず、画像の縦と横のサイズは同じでなければなりません。

また、画像のフォーマットによって、置き換える画像の種類が変わります。
例えば、SWF に埋め込んだ画像が ``Lossless`` 形式であれば、 ``PNG``, ``GIF`` 形式の
画像でしか置き換えることができません。
``JPEG`` 形式であれば、 ``JPEG`` 形式の画像でしか置き換えることができません。

さらに、アルファ値（透明度）が設定されている画像であれば、
置き換える画像もアルファ値が設定されたものでなければなりません。

+---------------------------------+----+----------+-----------------------------------------+---------------------------+
| SWF 内の画像                    | ID | Format   |  置き換える画像                         | 置き換える画像ファイル名  |
+=================================+====+==========+=========================================+===========================+
| .. image:: img/bitmap_7.jpg     | 7  | JPEG     | .. image:: img/kinoko_blue.jpg          | kinoko_blue.jpg           |
+---------------------------------+----+----------+-----------------------------------------+---------------------------+
| .. image:: img/bitmap_8.png     | 8  | Lossless | .. image:: img/kinoko_blue.png          | kinoko_blue.png           |
+---------------------------------+----+----------+-----------------------------------------+---------------------------+
| .. image:: img/bitmap_4.png     | 4  | Lossless | .. image:: img/kinoko_blue_alpha.png    | kinoko_blue_alpha.png     |
+---------------------------------+----+----------+-----------------------------------------+---------------------------+


ソースコード
--------------

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


実行結果
----------
.. raw:: html

    <embed src="../swf/bitmap_out.swf" embed src="example.swf" type="application/x-shockwave-flash" width="240" height="266" />


