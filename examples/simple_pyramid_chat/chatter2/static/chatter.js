$(document).ready(function() {
    // connect to the websocket
    var socket = io.connect('/chat');

    // Listen for the event "chat" and add the content to the log
    socket.on("chat", function(e) {
        $("#chatlog").append(e + "<br />");
    });

    socket.on("user_disconnect", function() {
        $("#chatlog").append("user disconnected" + "<br />");
    });

    socket.on("user_connect", function() {
        $("#chatlog").append("user connected" + "<br />");
    });

    // Execute whenever the form is submitted
    $("#chat_form").submit(function(e) {
        // don't allow the form to submit
        e.preventDefault();

        var val = $("#chatbox").val();

        // send out the "chat" event with the textbox as the only argument
        socket.emit("chat", val);

        $("#chatbox").val("");
    });
});
