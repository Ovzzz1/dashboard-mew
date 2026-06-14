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

$nsYt = 'http://www.youtube.com/xml/schemas/2015';
$nsMedia = 'http://search.yahoo.com/mrss/';
$ctx = stream_context_create(['http' => ['timeout' => 10, 'header' => "User-Agent: Mozilla/5.0\r\n"]]);

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

@mkdir(dirname($cacheFile), 0755, true);
$json = json_encode($result, JSON_UNESCAPED_UNICODE);
@file_put_contents($cacheFile, $json);
echo $json;
