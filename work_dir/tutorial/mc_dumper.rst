==========================
SWF から MovieClip の抽出
==========================

swf_mc_dumper.py
------------------

``tomato/swf_mc_dumper.py`` によって、SWF 内の MovieClip を抽出し
それぞれ SWF に変換することができます。

.. code-block:: sh

    $ cd tomato
    $ python swf_mc_dumper.py
    usage: python swf_mc_dumper.py [input.swf] [output directory] [limit_depth]


**[input.swf]**
    MovieClip を抽出したい SWF を指定します。

**[output directory]**
    抽出し変換した SWF を出力したいディレクトリを指定します。

**[limit_depth]**
    MovieClip の入れ子数の上限を指定します。limit_depth 以上の入れ子数を
    検出するとエラーを出力します。
    指定しない場合、デフォルト値 3 が使用されます。


実行結果
----------

``tomato/sample/mc/tank.swf`` の MovieClip を抽出してみましょう。

.. code-block:: sh

    $ python swf_mc_dumper.py sample/mc/tank.swf sample/mc
    parsing sample/mc/tank.swf ...
    writing sample/mc/kombu.swf ...
    writing sample/mc/fish1.swf ...
    writing sample/mc/fish2.swf ...

処理が完了すると sample/mc ディレクトリに ``kombu.swf`` , 
``fish1.swf`` , ``fish2.swf`` が出力されます。

limit_depth に 1 を指定すると、入れ子数 1 以上の MovieClip について
エラーが出力されます。

.. code-block:: sh

    $ python swf_mc_dumper.py sample/mc/tank.swf sample/mc 1
    parsing sample/mc/tank.swf ...
    writing sample/mc/kombu.swf ...
    Error: MovieClip : ID: 10000 - "kombu"             depth 1
    Error: MovieClip : ID: 9999                        depth 1
    writing sample/mc/fish1.swf ...
    Error: MovieClip : ID: 10000 - "fish1"             depth 1
    Error: MovieClip : ID: 9999                        depth 1
    writing sample/mc/fish2.swf ...
    Error: MovieClip : ID: 10000 - "fish2"             depth 1
    Error: MovieClip : ID: 9999                        depth 1


``※SWF のサイズの問題について``

出力された SWF は MovieClip の大きさにちょうど収まるよう
サイズを調整できていません。これは次回リリースで対応できればと考えています。
