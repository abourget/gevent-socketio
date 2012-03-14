$(document).ready(function() {
    // connect to the websocket
    var socket = io.connect();

    // Listen for the event "chat" and add the content to the log
    socket.on("chat", function(e) {
        $("#chatlog").append(e + "<br />");
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
