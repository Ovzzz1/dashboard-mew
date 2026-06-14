<?php
header('Content-Type: application/json; charset=utf-8');

// Chaînes coréennes suivies : handle -> [id, nom affiché]
$channels = [
    ['id' => 'UCOjBM0pBpUshHSB3qxYEo-w', 'name' => 'Rana 한국어 Podcast'],
    ['id' => 'UCWQTljD_t5DATk_EhbI76bw', 'name' => 'Korean with Sol'],
    ['id' => 'UCAlCEzL0QxyufwrjTOa7p4g', 'name' => '토토의 Korean Podcast'],
    ['id' => 'UCiS8Wx_7_1Hgi39YrFPiiIg', "name" => "Lina's Korean Podcast"],
    ['id' => 'UCYBToQk7WhzdlxGTNK2e8Zw', 'name' => 'Korean with Mina'],
];

$cacheFile = __DIR__ . '/../cache/youtube_feed.json';
$cacheTTL = 3600; // 1h

if (file_exists($cacheFile) && (time() - filemtime($cacheFile) < $cacheTTL)) {
    readfile($cacheFile);
    exit;
}

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';
$nsYt = 'http://www.youtube.com/xml/schemas/2015';
$nsMedia = 'http://search.yahoo.com/mrss/';
$ctx = stream_context_create(['http' => ['timeout' => 10, 'header' => "User-Agent: " . UA . "\r\n"]]);

$result = [];
foreach ($channels as $ch) {
    $videos = [];
    $xml = @file_get_contents("https://www.youtube.com/feeds/videos.xml?channel_id={$ch['id']}", false, $ctx);
    if ($xml !== false) {
        $feed = @simplexml_load_string($xml);
        if ($feed !== false) {
            foreach ($feed->entry as $entry) {
                $yt = $entry->children($nsYt);
                $media = $entry->children($nsMedia);
                $videos[] = [
                    'videoId' => (string)$yt->videoId,
                    'title' => (string)$entry->title,
                    'published' => (string)$entry->published,
                    'thumbnail' => (string)$media->group->thumbnail->attributes()->url,
                ];
            }
        }
    }
    $result[] = [
        'channelId' => $ch['id'],
        'channelName' => $ch['name'],
        'videos' => $videos,
    ];
}

// Filtre les YouTube Shorts : /shorts/{id} renvoie 200 si c'est un short,
// 303 -> /watch?v=... sinon. Requêtes HEAD en parallèle (curl_multi).
$allIds = [];
foreach ($result as $ch) {
    foreach ($ch['videos'] as $v) $allIds[] = $v['videoId'];
}

$isShort = [];
if ($allIds) {
    $mh = curl_multi_init();
    $handles = [];
    foreach ($allIds as $id) {
        $c = curl_init("https://www.youtube.com/shorts/$id");
        curl_setopt_array($c, [
            CURLOPT_NOBODY => true,
            CURLOPT_FOLLOWLOCATION => false,
            CURLOPT_USERAGENT => UA,
            CURLOPT_COOKIE => 'CONSENT=YES+1; SOCS=CAI',
            CURLOPT_TIMEOUT => 8,
            CURLOPT_RETURNTRANSFER => true,
        ]);
        curl_multi_add_handle($mh, $c);
        $handles[$id] = $c;
    }
    $running = null;
    do {
        curl_multi_exec($mh, $running);
        curl_multi_select($mh);
    } while ($running > 0);
    foreach ($handles as $id => $c) {
        $isShort[$id] = curl_getinfo($c, CURLINFO_HTTP_CODE) === 200;
        curl_multi_remove_handle($mh, $c);
    }
    curl_multi_close($mh);
}

foreach ($result as &$ch) {
    $ch['videos'] = array_values(array_filter(
        $ch['videos'],
        fn($v) => empty($isShort[$v['videoId']])
    ));
}
unset($ch);

@mkdir(dirname($cacheFile), 0755, true);
$json = json_encode($result, JSON_UNESCAPED_UNICODE);
@file_put_contents($cacheFile, $json);
echo $json;
