=======================
Tomato API
=======================

Tomato API を用いることで、チュートリアルで紹介した他にも
いろいろな操作を SWF に対して行うことができるようになります。

Swf オブジェクトのメソッド
---------------------------

Swf オブジェクトのメソッド一覧です。

swf
^^^^^^

.. code-block:: python

    >>> from tomato import Swf
    >>> tank_swf = Swf(open('tomato/sample/mc/tank.swf').read())

SWF ファイルを読み込み、Swf オブジェクトを生成します。


swf.size
^^^^^^^^^^

.. code-block:: python

    >>> tank_swf.size
    (240, 266)

``swf.size`` で SWF の縦、横のサイズを取得することができます。
ピクセル単位で出力されます。


swf.copy
^^^^^^^^^^

.. code-block:: python

    >>> tank_swf.copy()
    <tomato.swf_processor.Swf object at 0x51e330>

``copy`` メソッドはSWF オブジェクトの deep copy を作成します。

python の `copy モジュール <http://docs.python.org/library/copy.html>`_ の
``deepcopy`` メソッドよりも 8 倍程度高速にコピーを生成することができます。

Global 変数に置き換え元の SWF を宣言し、MovieClip
の置き換えを行う際に ``copy()`` したものを用いる事で、
SWF ファイルを読み込みパースを行う際のコストを抑えることができます。


swf.get_movie_clip_name
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> tank_swf.get_movie_clip_name()
    ['kombu', 'fish1', 'fish2']

``get_movie_clip_name`` メソッドで Swf 内の MovieClip を取得することができます。


swf.get_movie_clip
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> tank_swf.get_movie_clip('kombu')
    <tomato.structure.MovieClip object at 0x5102d0>

``get_movie_clip`` メソッドで SWF 内の MovieClip から MovieClip オブジェクトを生成します。


swf.get_movie_clip_from_parent
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``tomato/sample/mc/fish_red_fin.swf`` は金魚の MovieClip (``red``)
の内部にヒレの MovieClip (``fin``) があります。

このように入れ子構造の MovieClip を取得したい場合は
``get_movie_clip_from_parent`` メソッドを用います。

.. raw:: html

    <embed src="swf/fish_red_hire.swf" embed src="example.swf" type="application/x-shockwave-flash" width="240" height="266" />
    <img src="img/tomato_fin.png" />

.. code-block:: python

    >>> s = Swf(open('tomato/sample/mc/fish_red_fin.swf').read())
    >>> s.get_movie_clip_from_parent('red', 'fin')
    <tomato.structure.MovieClip object at 0x1b7570>

``fin`` という名前の MovieClip が一つしかない場合は ``get_movie_clip`` メソッドでも
問題なく取得することができますが、

- ``fish1`` MovieClip の中の ``fin`` MovieClip
- ``fish2`` MovieClip の中の ``fin`` MovieClip
- ``fish3`` MovieClip の中の ``fin`` MovieClip
- ...

といったような構造の場合、SWF の中で最初に発見された
``fin`` MovieClip を取得しようとしてうまくいきません。

このような場合に ``get_movie_clip_from_parent`` メソッドを
用いるとうまく処理を行うことができます。


swf.delete_movie_clip
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   >>> tank_swf.delete_movie_clip('kombu')
   >>> tank_swf.write(open('tomato/sample/mc/tank_without_kombu.swf', 'w'))

``delete_movie_clip`` メソッドで MovieClip を画面上に表示しないようにすることができます。

引数に MovieClip の名前、もしくは MovieClip オブジェクトを指定します。

ただし、MovieClip で用いられていたベクターデータや画像データ等は残ったままです。


swf.replace_movie_clip
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   >>> red_swf = Swf(open('tomato/sample/mc/fish_red.swf').read())
   >>> red_mc = red_swf.get_movie_clip('red')
   >>> ret_mc = tank_swf.replace_movie_clip('fish1', red_mc)

``replace_movie_clip`` メソッドを用いて、MovieClip の置き換えを行います。

元々 ``red_swf`` 内にあった ``red_mc`` が ``tank_swf`` 内にコピーされ、新しい MovieClip
``ret_mc`` が返されます。この ``ret_mc`` に対してメソッドを呼ぶことで
置き換えた MovieClip の位置やサイズを変更することができます。


swf.write
^^^^^^^^^^^

.. code-block:: python

   >>> tank_swf.write()
   'FWS\x04\x83\x06\x00\x00p\x00\t`\x00\x00\xa6...

   >>> tank_swf.write(open('tomato/sample/mc/out2.swf', 'w'))

``write`` メソッドで加工した SWF バイナリを出力します。

引数に何も指定しなければそのままバイナリが出力されます。
Django 等でレスポンス返却する際に用います。

引数にファイルオブジェクトを指定すると加工した SWF が書き出されます。


MovieClip オブジェクトのメソッド
---------------------------------

MovieClip オブジェクトのメソッド一覧です。

mc.scale
^^^^^^^^^

.. code-block:: python

    >>> ret_mc.scale
    (0.5, 0.5)

MovieClip のサイズの縦と横の拡大値を取得します。1 が元の大きさになります。

指定されていなければ ``None`` が返されます。


mc.set_scale
^^^^^^^^^^^^^^^

.. code-block:: python

    >>> ret_mc.set_scale(0.5, 0.5)

MovieClip のサイズ変更を行います。縦と横の拡大値で指定します。


mc.depth
^^^^^^^^^

.. code-block:: python

    >>> ret_mc.depth
    109

MovieClip のレイヤー深度を取得します。

レイヤー深度とは MovieClip の画面への表示順で 65535 以下の正の整数で指定します。
数値を大きく設定すれば MovieClip は手前に表示され、小さく設定すれば後方に表示されます。


mc.set_depth
^^^^^^^^^^^^^

.. code-block:: python

    >>> ret_mc.set_depth(130)
    
MovieClip のレイヤー深度の変更を行います。

ただし、 MovieClip を削除する ActionScript を記述する際に
レイヤー深度によって削除する MovieClip を指定するため、レイヤー深度を
変更するのはあまり望ましくありません。


mc.translate
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> ret_mc.translate
    (158.19999999999999, 43.549999999999997)

MovieClip の位置を取得します。ピクセル単位で x 座標, y 座標が返されます。


mc.set_translate
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> ret_mc.set_translate(100, 60)
    >>> ret_mc.translate
    (100.0, 60.0)

MovieClip の位置変更を行います。ピクセル単位で指定します。



シリアライズ機能
-----------------

Tomato の処理の中で重いものの一つが SWF ファイルのパースです。

生成した Swf オブジェクトをシリアライズし利用することで、
SWF ファイルの読み込み（パース処理）時間を削減することができます。


swf.serialize / swf.dumps
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> from tomato import Swf
    >>> s = Swf(open('tomato/sample/mc/tank.swf').read())
    >>> s.serialize()
    '\x85\xb2serializer_version\xa4MCV1\xa6blocks\xdc\x007...

    >>> s.serialize(open('tomato/sample/mc/tank.p', 'w'))

SWF オブジェクトをシリアライズします。

引数を指定しなければ、バイナリ列が出力されます。
引数にファイルオブジェクトを指定すると、ファイルに書き出されます。

``swf.dumps`` メソッドでも同じ処理を行うことができます。


swf.deserialize / swf.loads
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> from tomato import Swf
    >>> s = Swf().deserialize(open('tomato/sample/mc/tank.p').read())
    >>> s
    <tomato.swf_processor.Swf object at 0x1b19f0>

シリアライズされた SWF オブジェクトをデシリアライズします。

``swf.loads`` メソッドでも同じ処理を行うことができます。

``Swf(open('tomato/sample/mc/tank.swf').read())`` で直接 SWF ファイルを読み込むよりも、
``Swf().loads(open('tomato/sample/mc/tank.p').read())`` で swf オブジェクトを
生成する方が高速に処理できます。


msgpack.Unpacker を用いた高速化
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

頻繁にデシリアライズを行う場合は、 ``msgpack-python`` の機能である
``Unpacker`` を用いることで、デシリアライズの高速化を行うことができます。

.. code-block:: python

    >>> import msgpack
    >>> from tomato import Swf
    >>> U = msgpack.Unpacker()
    >>> Swf().loads(open('tomato/sample/mc/tank.p').read(), U)
    <tomato.swf_processor.Swf object at 0x1b1a20>

``deserialize`` / ``loads`` メソッドの二つ目の引数に ``Unpacker`` オブジェクトを指定します。