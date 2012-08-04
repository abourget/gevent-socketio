testTransport = function(transports)
{
  var prefix = "socketio - " + transports + ": ";
  
  connect = function(transports) 
  {
    // Force transport
    io.transports = transports;
    deepEqual(io.transports, transports, "Force transports");
    var options = { 'force new connection': true }
    return io.connect('/test', options);
  }
    
  asyncTest(prefix + "Connect", function() {
    expect(4);
    test = connect(transports);
    test.on('connect', function () {
      ok( true, "Connected with transport: " + test.socket.transport.name );
      test.disconnect();
    });
    test.on('disconnect', function (reason) {
      ok( true, "Disconnected - " + reason );
      test.socket.disconnect();
      start();
    });
    test.on('connect_failed', function () {
      ok( false, "Connection failed");
      start();
    });
  });
  
  asyncTest(prefix + "Emit with ack", function() {
    expect(3);
    test = connect(transports);
    test.emit('requestack', 1, function (val1, val2) {
        equal(val1, 1);
        equal(val2, "ack");
      	test.disconnect();
      	test.socket.disconnect();
        start();
    });
  });
}

transports = [io.transports];

// Validate individual transports
for(t in io.transports)
{
   if(io.Transport[io.transports[t]].check()) {
     transports.push([io.transports[t]]);
   }
}
for(t in transports)
{
   testTransport(transports[t])
}
