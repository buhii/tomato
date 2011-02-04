=======================
Tomato API
=======================

Tomato API を用いることで、チュートリアルで紹介した他にも
いろいろな操作を SWF に対して行うことができるようになります。

メソッド
---------

SWF の読み込み
^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> from tomato import Swf
    >>> tank_swf = Swf(open('tomato/sample/mc/tank.swf').read())


SWF の画面サイズ
^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> tank_swf.size
    (240, 266)
    >>> tank_swf.width
    240
    >>> tank_swf.height
    266

SWF の画面サイズがピクセル単位で出力されます。


SWF オブジェクトのコピー
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> tank_swf.copy()
    <tomato.swf_processor.Swf object at 0x51e330>

SWF オブジェクトの deepcopy を作成します。

python の copy モジュールの deepcopy 関数よりも
8 倍程度高速にコピーを生成することができます。

Global 変数に置き換え元の SWF を宣言し、MovieClip
の置き換えを行う際に ``copy()`` したものを用いる事で、
SWF ファイルを読み込んでパースを行うコストを抑えることができます。


SWF 内 MovieClip 名の取得
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> tank_swf.get_movie_clip_name()
    ['kombu', 'fish1', 'fish2']


MovieClip オブジェクトの取得
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> tank_swf.get_movie_clip('kombu')
    <tomato.structure.MovieClip object at 0x5102d0>


入れ子関係を用いた MovieClip の取得
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``tomato/sample/mc/fish_red_fin.swf`` は金魚の MovieClip (``red``)
の内部にヒレの MovieClip (``fin``) があります。

このように入れ子構造の MovieClip を取得したい場合は
``get_movie_clip_from_parent`` 関数を用います。

.. raw:: html

    <embed src="swf/fish_red_hire.swf" embed src="example.swf" type="application/x-shockwave-flash" width="240" height="266" />
    <img src="img/tomato_fin.png" />

.. code-block:: python

    >>> s = Swf(open('tomato/sample/mc/fish_red_fin.swf').read())
    >>> s.get_movie_clip_from_parent('red', 'fin')
    <tomato.structure.MovieClip object at 0x1b7570>

-------------

``fin`` という名前の MovieClip が一つしかない場合は ``get_movie_clip`` 関数でも
問題なく取得することができますが、

- ``fish1`` MovieClip の中の ``fin`` MovieClip
- ``fish2`` MovieClip の中の ``fin`` MovieClip
- ``fish3`` MovieClip の中の ``fin`` MovieClip
- ...

といったような構造の場合、 ``get_movie_clip`` 関数だと SWF の中で最初に
発見された ``fin`` MovieClip を取得しようとしてうまくいきません。
このような場合に ``get_movie_clip_from_parent``
関数を用いるとうまく処理を行うことができます。


画面から MovieClip の削除
^^^^^^^^^^^^^^^^^^^^^^^^^^


MovieClip の置き換え
^^^^^^^^^^^^^^^^^^^^^

MovieClip のサイズ変更
^^^^^^^^^^^^^^^^^^^^^^^

MovieClip のレイヤー深度の変更
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


MovieClip の位置変更
^^^^^^^^^^^^^^^^^^^^^^


SWF の書き出し
^^^^^^^^^^^^^^^^


シリアライズ機能
-----------------


