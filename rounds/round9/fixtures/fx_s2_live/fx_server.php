<?php
// fx_s2_live fake policy server: answers SimSearch_Eval
// requests with the priors planted on argv. Protocol is the
// production one (4-byte big-endian length + JSON), read from
// code/search_s2.php's SimSearch_Eval / SimSearch_Connect.
//   php fx_server.php <sockpath> <priors-json>
$sock = $argv[1];
$priors = json_decode($argv[2], true);
@unlink($sock);
$srv = stream_socket_server("unix://" . $sock, $errno, $errstr);
if ($srv === false) { fwrite(STDERR, "fx server bind failed: $errstr\n"); exit(1); }
file_put_contents($sock . ".ready", "1");
$deadline = time() + 120;
while (time() < $deadline) {
  $r = [$srv]; $w = null; $e = null;
  if (stream_select($r, $w, $e, 2) < 1) continue;
  $c = @stream_socket_accept($srv, 2);
  if ($c === false) continue;
  stream_set_timeout($c, 10);
  // one connection may carry several sequential eval requests
  while (true) {
    $hdr = "";
    while (strlen($hdr) < 4) {
      $chunk = @fread($c, 4 - strlen($hdr));
      if ($chunk === false || $chunk === "") break;
      $hdr .= $chunk;
    }
    if (strlen($hdr) < 4) break;
    $len = unpack("N", $hdr)[1];
    $body = "";
    while (strlen($body) < $len) {
      $chunk = @fread($c, $len - strlen($body));
      if ($chunk === false || $chunk === "") break;
      $body .= $chunk;
    }
    if (strlen($body) < $len) break;
    $resp = json_encode(["priors" => $priors, "value" => 0.0]);
    fwrite($c, pack("N", strlen($resp)) . $resp);
  }
  fclose($c);
}
