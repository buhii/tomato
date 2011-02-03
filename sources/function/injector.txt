=======================
SWF へ変数の埋め込み
=======================

変数の埋め込み
----------------

Tomato では SWF へ変数を注入することができます。

``※パラメータ注入を行う場合、SWF パブリッシュ設定の「XMPメタデータを含める」
オプションは無効にして下さい。``

ここでは、 ``tomato/sample/params/params.swf`` に変数を注入してみます。


create_swf 関数
----------------

.. raw:: html

    <embed src="../swf/params.swf" embed src="example.swf" type="application/x-shockwave-flash" width="240" height="266" />

``params.swf`` は ``a`` , ``b`` , ``c`` という変数の内容を画面上に表示します。
直接表示した場合、 ``a`` , ``b`` , ``c`` という変数が SWF 内に存在しないので
何も表示されません。

Tomato で変数を埋め込むコードは以下になります。

.. code-block:: python

   >>> from tomato import create_swf
   >>> params = {
   ... 	   'a': 'hoge',
   ...     'b': u'ふが',
   ...     'c': u'ぴよち'}
   >>> s = create_swf(open('sample/params/params.swf').read(), params)
   >>> open('sample/params/out.swf', 'w').write(s)

埋め込みたい変数の名前と内容を辞書形式にした ``params`` を用意し
``create_swf`` 関数を呼び出すことで埋め込みが行われます。

出力された ``out.swf`` は次のようになります。

.. raw:: html

    <embed src="../swf/params_out.swf" embed src="example.swf" type="application/x-shockwave-flash" width="240" height="266" />

    
