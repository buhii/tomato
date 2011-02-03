===========================
ソースコードのダウンロード
===========================

github
------------------

github から最新の Tomato をダウンロードすることができます。

http://github.com/buhii/tomato

PyPI には現在登録準備中です。


必要なモジュール
------------------

画像抽出、画像置き換えには、 ``PIL`` (バージョン 1.1.7 以降) が必要です。

.. code-block:: none

    $ pip install PIL


また、MovieClip の置き換えや抽出を行う場合は ``bitarray`` (バージョン 0.3.5 以降) ,
``msgpack-python`` (バージョン 0.1.8 以降) が必要です。

.. code-block:: none

    $ pip install bitarray
    $ pip install msgpack-python==0.1.8


-------------

``※ 今後のリリースについて``

GAE では ``msgpack-python`` , ``bitarray`` 等のモジュールを用意することができないため、
今後 ``msgpack-python`` , ``bitarray`` が無くても動作するバージョンをリリースしたいと考えています
（ただしこれらのモジュールを用いない場合、数倍程度処理に時間が掛かるでしょう）。

