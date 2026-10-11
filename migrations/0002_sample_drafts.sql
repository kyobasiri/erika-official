-- 試作で使ったサンプル5件を「下書き」として入れる（不要なら管理ページから削除）
-- 適用: npx wrangler d1 migrations apply erika-words --remote
INSERT OR IGNORE INTO words (id, status, quote, speaker, source_title, source_author, source_kind, source_detail, source_url, image_url, image_key, image_alt, template, options, comment, tags, spoiler, sort_order, created_at, updated_at, published_at)
VALUES ('fugaku-tsukimiso', 'draft', '富士には、
月見草が
よく似合う。', NULL, '富嶽百景', '太宰治', 'book', NULL, NULL, '/assets/images/words/erika-sunflower.webp', NULL, '夕暮れの海辺で、眼鏡のエリカが一輪の向日葵を差し出している', 'bubble', '{"accent": "#f4b63f", "focus": {"x": 50, "y": 30}, "bubble": {"x": 6, "y": 6, "width": 40, "shape": "round", "tail": "bottom-right"}}', '大きくて立派なものの隣に、小さな花がちゃんと似合っている。主役じゃなくても、そこにいていい理由があるって言われた気がするんです。だから私は向日葵を持ってきました。月見草じゃないのは、ご愛嬌ということで。', '["静か", "肯定"]', 0, 5, strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), NULL);
INSERT OR IGNORE INTO words (id, status, quote, speaker, source_title, source_author, source_kind, source_detail, source_url, image_url, image_key, image_alt, template, options, comment, tags, spoiler, sort_order, created_at, updated_at, published_at)
VALUES ('melos-shinjirarete', 'draft', '信じられて
いるから
走るのだ。', 'メロス', '走れメロス', '太宰治', 'book', NULL, NULL, '/assets/images/words/erika-moonlight.webp', NULL, '月明かりの桟橋で、エリカが金色に光る水を両手ですくっている', 'manga', '{"accent": "#111111", "vertical": true, "focus": {"x": 55, "y": 40}, "bubble": {"x": 8, "y": 8, "height": 44, "shape": "shout"}}', '間に合うかどうかじゃない。信じてくれた人がいる、それだけで足が前に出る。理屈じゃないところで人が動く瞬間って、どうしてこんなに熱いんでしょうね。', '["熱い", "決意"]', 0, 4, strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), NULL);
INSERT OR IGNORE INTO words (id, status, quote, speaker, source_title, source_author, source_kind, source_detail, source_url, image_url, image_key, image_alt, template, options, comment, tags, spoiler, sort_order, created_at, updated_at, published_at)
VALUES ('kusamakura', 'draft', '智に働けば角が立つ。
情に棹させば流される。
意地を通せば窮屈だ。', NULL, '草枕', '夏目漱石', 'book', NULL, NULL, '/assets/images/words/erika-sunflower.webp', NULL, '夕暮れの海辺で、眼鏡のエリカが一輪の向日葵を差し出している', 'game', '{"accent": "#7dd3fc", "focus": {"x": 50, "y": 22}, "speakerName": "エリカ"}', 'どれを選んでも、どこかが窮屈。それでも生きていく、という開き直りの一文目だと思っています。迷ったときに読むと、少しだけ肩の力が抜けるんです。', '["人生", "ユーモア"]', 0, 3, strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), NULL);
INSERT OR IGNORE INTO words (id, status, quote, speaker, source_title, source_author, source_kind, source_detail, source_url, image_url, image_key, image_alt, template, options, comment, tags, spoiler, sort_order, created_at, updated_at, published_at)
VALUES ('furusato', 'draft', '志を果たして
いつの日にか帰らん
山は青き故郷
水は清き故郷', NULL, '故郷', '作詞 高野辰之', 'song', '文部省唱歌（1914年）', NULL, '/assets/images/words/erika-moonlight.webp', NULL, '月明かりの桟橋で、エリカが金色に光る水を両手ですくっている', 'lyric', '{"accent": "#c2410c", "focus": {"x": 62, "y": 45}, "songTitle": "故郷"}', '遠くへ行くことと、帰る場所があることは、ちゃんと両立する。いつか胸を張って帰れるように、今日もやれることをやろうと思える歌です。', '["歌", "郷愁"]', 0, 2, strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), NULL);
INSERT OR IGNORE INTO words (id, status, quote, speaker, source_title, source_author, source_kind, source_detail, source_url, image_url, image_key, image_alt, template, options, comment, tags, spoiler, sort_order, created_at, updated_at, published_at)
VALUES ('ginga-saiwai', 'draft', 'けれども
ほんとうのさいわいは
一体何だろう。', 'ジョバンニ', '銀河鉄道の夜', '宮沢賢治', 'book', NULL, NULL, '/assets/images/words/erika-moonlight.webp', NULL, '月明かりの桟橋で、エリカが金色に光る水を両手ですくっている', 'letter', '{"accent": "#9f1239", "vertical": true, "focus": {"x": 58, "y": 50}}', '答えをくれない問いなのに、手のひらに残る。すくった水がこぼれていくみたいに、大事なものほど形にできないのかもしれません。それでも問い続けることが、たぶん答えの代わりなんだと思います。', '["問い", "夜"]', 0, 1, strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), NULL);
