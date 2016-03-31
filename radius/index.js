
'use strict';

var dgram = require('dgram');

var command = process.argv[0],
    script = process.argv[1],
    host = process.argv[2],
    secret = process.argv[3],
    sends = parseInt(process.argv[4] || 0, 10);

if (!(host && secret && sends)) process.exit(1);

var radius = require('radius');
var access_request, total = sends, sent = 0;

try {
  access_request = radius.encode({
    code: 'Access-Request',
    secret: secret,
    attributes: [
      ['User-Name', '11:11:11:11:11:11'],
      ['Framed-IP-Address', '10.0.0.100'],
      ['Acct-Session-Id', 'abc123'],
      ['Calling-Station-Id', '11:11:11:11:11:11']
    ]
  });
} catch (ex) {
  throw ex;
}

var radius_client = (
  dgram.createSocket('udp4').on('error', function(err) {
    console.error('socket error', err);
  }).on('close', function() {
    console.log('done!');
  })
);

radius_client.bind(9000, '0.0.0.0', function() {
  console.log('about to send', sends, 'bogus access-requests');
  while (sends) {
    sends -= 1;
    radius_client.send(access_request, 0, access_request.length, 1812, host, function() {
      sent += 1;
      if (sent === total) {
        radius_client.close();
      }
    });
  }
});
