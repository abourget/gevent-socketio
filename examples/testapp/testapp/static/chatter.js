appendMessage = function(message) {
  $('#chatlog').append(message);
}

$(document).ready(function() {
  // connect to the websocket
  socket = io.connect();
  chat = io.connect('/chat');

  // Listen for the event "chat" and add the content to the log
  socket.on("chat", function(e) {
    console.log("Chat message event", arguments);
    appendMessage(e + "<br />");
  });
  socket.on("got_some_json", function(e) {
    console.log("We got back some json", e);
  });
  socket.on("message", function(e) {
    console.log("Message", e);
  });
  socket.on("nettest_configured", function(e) {
    console.log("Ok, configured", e);
  });
  socket.on("connect", function(e) {
    console.log("Connected", arguments);
  });
  socket.on("disconnect", function(e) {
    console.log("Disconnected", arguments);
  });


  /* Chat events */
  chat.on("rtc_invite", function(nickname, sdp) {
    console.log("Got an RTC_INVITE packet", nickname, sdp);
    var div = $("<div>You've been invited.  <a href='#' onclick='onJoinRemoteStream(this);'>Click here</a> to join</div>");
    div.data('sdp', sdp);
    appendMessage(div);
  });
  chat.on("disconnect", function(e) {
    console.log("Disconnected from chat", arguments);
  });
  chat.on("pack", function(e) {
    console.log("got pack message", e);
  });
  chat.on("bob", function(e) {
    console.log("Received the bob event on /chat", e);
  });
  chat.on("callmeback", function(param1, param2, ack) {
    console.log("Got the 'callmeback' call", param1, param2, ack);
    if (ack) {
      console.log("  sending an ack");
      ack("ackprm1", "ackprm2");
    } else {
      console.log("  no ack to send, probably already sent");
    }
  });
  chat.on("error", function(e) {
    console.log("Error", arguments);        
  });


  // Execute whenever the form is submitted
  $("#chat_form").submit(function(e) {
    // don't allow the form to submit
    e.preventDefault();

    var val = $("#chatbox").val();

    // send out the "chat" event with the textbox as the only argument
    socket.emit("chat", val);

    appendMessage(val + "<br />");

    $("#chatbox").val("");
  });

  $('#b1').click(function(){
    console.log("b1, emit bob, thank you")
    socket.emit("bob", {"thank": "you"});
  });
  $('#b2').click(function(){
    console.log("b2, send simple json message")
    socket.json.send({blah: "a simple message"});
  });
  $('#b3').click(function(){
    console.log("b3, json.emit(bob, {thank:you})")
    socket.emit("bob", {"thank": "you"});
    socket.send("a simple message");
  });
  $('#b4').click(function(){
    console.log("b4, send /chat elements")
    chat.emit('mymessage', 'bob');
    chat.send("hey");
    chat.json.send({asdfblah: "asd " + String.fromCharCode(13) + "fé\n\\'blah"});
  });
  $('#b5').click(function(){
    console.log("b5, ack stuff and callbacks")
    chat.emit("my_callback", {'this': 'is sweet'}, function() {
      console.log("OKAY! Executed callback!!!!!", arguments);
      chat.emit("mymessage", "bob");
    });
  });
  $('#b6').click(function(){
    console.log("b6, triggering server callback")
    chat.emit("trigger_server_callback", 'superbob as param');
    chat.send("a little message", function() {
      console.log("GOT BACK THE SIMPLE CALLBACK!");
    });
  });
  $('#b7').click(function(){
    console.log("b7, disconnet me please")
    //chat.emit("disconnect_me", 'superbob as param');
    chat.disconnect();
  });
  $('#button_nettest_config').click(function() {
    var options = {test_name: 'A2',
                   num_packets: 50,
                   packet_size: 100,
                   delay_between_packets: 0,
                   spread_delay: 0,
                  }
    console.log("Calling nettest_config_next", options);
    socket.emit("nettest_config_next", options);
  });
  $('#button_nettest_launch').click(function() {
    console.log("Calling nettest_launch");
    socket.emit("nettest_launch", {});
  });
  $('#rtc_button').click(function() {
    console.log("Sending WebRTC invitation to the channel.")
    getUserMedia();
    var video_el = $('#rtc_video');
  });


});


/** Web RTC stuff, inspired by http://code.google.com/p/webrtc-samples/source/browse/trunk/apprtc/index.html and the code from someone at PyCon, snippettized at https://gist.github.com/2026984 */


var pc = null;
var localStream = null;

getUserMedia = function() {
  try {
    navigator.webkitGetUserMedia("video,audio", onUserMediaSuccess,
                                 onUserMediaError);
    console.log("Requested access to local media.");
  } catch (e) {
    alert("webkitGetUserMedia() failed. Does your browser support WebRTC?");
    console.log("webkitGetUserMedia failed with exception: " + e.message);
  }
}
onUserMediaSuccess = function(stream) {
  console.log("User has granted access to local media.");
  var url = webkitURL.createObjectURL(stream);
  var video_el = $('#rtc_video')[0];
  video_el.style.opacity = 1;
  video_el.autoplay = true;
  console.log("Got an ObjectURL for the stream:", url);
  video_el.src = url;

  // Create my own peerConnection stuff..
  createPeerConnection();
}
onUserMediaError = function(error) {
  console.log("Failed to get access to local media. Error code was " + error.code);
  alert("Failed to get access to local media. Error code was " + error.code + ".");
}


onProcessSignalMessage = function() {
  var sdp = $(this).data('sdp');
  processSignalMessage(sdp);
  appendMessage("<p>Attempting to connect to remote, using SDP "+ sdp + ".</p>");
}
processSignalMessage = function(data) {
  pc.processSignalingMessage(data);
}

onJoinRemoteStream = function(el) {
  console.log("Trying to do stuff");
  console.log(el);
  var sdp = $(el).parent().data('sdp');
  console.log("Trying to do stuff again", sdp);
  createPeerConnection(sdp)
}
createPeerConnection = function(sdp) {
  if (pc != null) { return; }

  var pc_config = 'STUN stun.xten.com';
  try {
    pc = new webkitDeprecatedPeerConnection(pc_config,
                                            onSignalingMessage);
    console.log("Created webkitDeprecatedPeerConnnection with config \"" + pc_config + "\".");
  } catch (e) {
    console.log("Failed to create webkitDeprecatedPeerConnection, exception: " + e.message);
    try {
      pc = new webkitPeerConnection(pc_config,
                                    onSignalingMessage);
      console.log("Created webkitPeerConnnection with config \"" + pc_config + "\".");
    } catch (e) {
      console.log("Failed to create webkitPeerConnection, exception: " + e.message);
      alert("Cannot create PeerConnection object; tried webkitPeerConnection and webkitDeprecatedPeerConnection");
      return;
    }
  }
  pc.onconnecting = onSessionConnecting;
  pc.onopen = onSessionOpened;
  pc.onaddstream = onRemoteStreamAdded;
  pc.onremovestream = onRemoteStreamRemoved;
}
onSignalingMessage = function(message) {
  console.log("PC: Got a signaling message", message);
  chat.emit("rtc_invite", message);
}
onSessionConnecting = function(message) {
  console.log("PC: Session connecting.");
}
onSessionOpened = function(message) {
  console.log("PC: Session opened.");
}
onRemoteStreamAdded = function(event) {
  console.log("PC: Remote stream added.");
  var url = webkitURL.createObjectURL(event.stream);
  var remote_video = $('#rtc_remote_video')[0];
  remote_video.style.opacity = 1;
  remote_video.src = url;
  appendMessage("<input type=\"button\" id=\"hangup\" value=\"Hang up\" onclick=\"onHangup()\" />");
}
onRemoteStreamRemoved = function(event) {
  console.log("PC: Remote stream removed.");
}
onHangup = function() {
  console.log("PC: Hanging up.");
  $('#rtc_video')[0].style.opacity = 0;
  $('#rtc_remote_video')[0].style.opacity = 0;
  pc.close();
  // will trigger BYE from server
  chat.emit("rtc_hangup");
  pc = null;
  appendMessage("<p>You have left the call.</p>");
}