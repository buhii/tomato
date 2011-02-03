============
SWF の加工
============

replace_movie_clip 関数
-------------------------

Tomato では ``Swf`` オブジェクト及び ``MovieClip`` オブジェクトを
用いて MovieClip の置き換えを行うことができます。

``tank.swf`` の MovieClip である ``fish1`` を
``tomato/sample/mc/fish_red.swf`` 内の MovieClip である ``red`` に
置き換えてみましょう。

.. raw:: html

    <embed src="../swf/fish_red.swf" embed src="example.swf" type="application/x-shockwave-flash" width="240" height="266" />
    <img src="../img/fish_red_name.png" />


まずは、 ``fish_red.swf`` を読み込み、Swf オブジェクト及び MovieClip オブジェクト
を生成します。

.. code-block:: python

   >>> red_swf = Swf(open('tomato/sample/mc/fish_red.swf').read())
   >>> red_swf
   <tomato.swf_processor.Swf object at 0x49a570>
   >>> red_swf.get_movie_clip_name()
   ['red']
   >>> mc_red = red_swf.get_movie_clip('red') 
   >>> mc_red
   <tomato.structure.MovieClip object at 0x498250>


``replace_movie_clip`` 関数を用いて ``tank.swf`` の MovieClip を 
``mc_red`` に置き換え、``write`` 関数を用いて出力します。

.. code-block:: python

   >>> tank_swf.replace_movie_clip('fish1', mc_red)
   <tomato.structure.MovieClip object at 0x498630>
   >>> tank_swf.write(open('tomato/sample/mc/out.swf', 'w'))

出力された ``tomato/sample/mc/out.swf`` は次のようになります。

.. raw:: html

    <embed src="../swf/tank_out1.swf" embed src="example.swf" type="application/x-shockwave-flash" width="240" height="266" />


``fish2`` も ``tomato/sample/mc/fish_white.swf`` (MovieClip名: ``white``) で
置き換えると、次のような出力結果になります。

.. code-block:: python

   >>> white_swf = Swf(open('tomato/sample/mc/fish_white.swf').read())
   >>> mc_white = white_swf.get_movie_clip('white')

   >>> tank_swf.replace_movie_clip('fish2', mc_white)
   <tomato.structure.MovieClip object at 0x498670>

   >>> tank_swf.write(open('tomato/sample/mc/out2.swf', 'w'))


.. raw:: html

    <embed src="../swf/tank_out2.swf" embed src="example.swf" type="application/x-shockwave-flash" width="240" height="266" />


