=================
SWF から画像抽出
=================

swf_image_dumper.py
---------------------

``tomato/swf_image_dumper.py`` を用いることで、SWF 内のビットマップ画像
（JPEG, Lossless) を ``CharacterID`` と共に抽出することができます。

``CharacterID`` とは SWF 内部の画像や音声、アニメーションと行ったコンテンツについて
内部で定義された ID のことです。

下の SWF は ``tomato/sample/bitmap/bitmap.swf`` になります。この SWF から
ビットマップ画像を抽出してみましょう。


.. raw:: html

    <embed src="../swf/bitmap.swf" embed src="example.swf" type="application/x-shockwave-flash" width="240" height="266" />


実行結果
------------------

.. code-block:: sh

    $ cd tomato/
    $ python swf_image_dumper.py sample/bitmap/bitmap.swf


コマンドは無事終了すると、 ``tomato/sample/bitmap`` ディレクトリ内に、
``bitmap_4.png``, ``bitmap_7.jpg``, ``bitmap_8.png`` ファイルが出力されます。

+---------------------------------+--------------+--------------+
| 画像                            | ファイル名   | CharacterID  |
+=================================+==============+==============+
| .. image:: img/bitmap_7.jpg     | bitmap_7.jpg | 7            |
+---------------------------------+--------------+--------------+
| .. image:: img/bitmap_4.png     | bitmap_4.png | 4            |
+---------------------------------+--------------+--------------+
| .. image:: img/bitmap_8.png     | bitmap_8.png | 8            |
+---------------------------------+--------------+--------------+

Lossless 形式の画像は ``.png`` ファイルに、
JPEG 形式の画像は ``.jpg`` ファイルとして出力されます。

これらの出力されたファイル名の後ろについている数字は ``CharacterID`` です。

Tomato はこの ``CharacterID`` を用いて SWF 内の画像を置き換えることができます。

