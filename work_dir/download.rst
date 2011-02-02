===========================
ソースコードのダウンロード
===========================

github
------------------

github から最新の Tomato をダウンロードすることができます。

http://github.com/buhii/tomato

PyPI にはまだ登録準備中です。もうしばらくお待ち下さい。


必要なモジュール
------------------

画像抽出、画像置き換えには、PIL 1.1.7 が必要です。

.. code-block:: none

    $ pip install PIL


また、MovieClip の置き換えや抽出を行う場合は bitarray, msgpack-python が必要です。

.. code-block:: none

    $ pip install bitarray
    $ pip install msgpack-python==0.1.8


-------------

``※ 今後のリリースについて``

GAE では msgpack, bitarray 等のモジュールを用意することができないため、
今後 msgpack, bitarray が無くても動作するバージョンをリリースしたいと考えています
（ただしこれらのモジュールを用いるよりも数倍程度処理が遅くなるでしょう）。

