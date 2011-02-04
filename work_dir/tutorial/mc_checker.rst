==========================
MovieClip 入れ子数の調査
==========================

swf_checker.py
------------------

``tomato/swf_checker.py`` によって、SWF 内の MovieClip の入れ子数を調べることができます。

.. code-block:: sh

    $ cd tomato
    $ python swf_checker.py
    usage: python swf_checker.py [input.swf] [limit_depth]

**[input.swf]**
    MovieClip 入れ子数を調査したい SWF を指定します。

**[limit_depth]**
    MovieClip の入れ子数の上限を指定します。limit_depth 以上の入れ子数を
    検出するとエラーを出力します。
    指定しない場合、デフォルト値 3 が使用されます。


実行結果
----------

``tomato/sample/mc/tank.swf`` の MovieClip 階層を調べてみましょう。

.. code-block:: sh

    $ python swf_checker.py sample/mc/tank.swf 1
    Error: MovieClip : ID: 2 - "kombu"                 depth 1
    Error: MovieClip : ID: 4 - "fish1"                 depth 1
    Error: MovieClip : ID: 6 - "fish2"                 depth 1

