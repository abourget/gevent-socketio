$(document).ready(function() {
    // connect to the websocket
    socket = io.connect();
    chat = io.connect('/chat');

    // Listen for the event "chat" and add the content to the log
    socket.on("chat", function(e) {
        console.log("Chat message event", arguments);
        $("#chatlog").append(e + "<br />");
    });
    socket.on("got_some_json", function(e) {
        console.log("We got back some json", e);
    });
    socket.on("message", function(e) {
        console.log("Message", e);
    });
    socket.on("connect", function(e) {
        console.log("Connected", arguments);
    });
    socket.on("disconnect", function(e) {
        console.log("Disconnected", arguments);
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

        $("#chatlog").append(val + "<br />");

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


});
