<?php
header('Content-Type: application/json; charset=utf-8');

// Stockage des niveaux de maîtrise du vocabulaire (vert/orange/rouge),
// partagé entre tous les appareils — un fichier JSON par livre (3A, 3B, 4A, 4B...).
// Clé : "{chapitre}_{한글}" -> "green" | "orange" | "red" | "none"

$book = preg_replace('/[^A-Za-z0-9_-]/', '', $_GET['book'] ?? ($_POST['book'] ?? ''));
if ($book === '') {
    http_response_code(400);
    echo json_encode(['error' => 'missing "book" parameter']);
    exit;
}

$dataDir = __DIR__ . '/../data/levels';
$file = "$dataDir/$book.json";

$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET') {
    if (file_exists($file)) {
        readfile($file);
    } else {
        echo '{}';
    }
    exit;
}

if ($method === 'POST') {
    $raw = file_get_contents('php://input');
    $data = json_decode($raw, true);
    if (!is_array($data)) {
        http_response_code(400);
        echo json_encode(['error' => 'invalid JSON body']);
        exit;
    }
    @mkdir($dataDir, 0755, true);
    $ok = @file_put_contents($file, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_FORCE_OBJECT));
    echo json_encode(['ok' => $ok !== false]);
    exit;
}

http_response_code(405);
echo json_encode(['error' => 'method not allowed']);
