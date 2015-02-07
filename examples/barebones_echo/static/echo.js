$(document).ready(function() { // this requires jquery!!  ack, surely there's another way!!!!

	var socket = io.connect('/echo');

	$(window).bind("beforeunload", function() {
		socket.disconnect();
	});

	socket.on("echo", function(rab, zab) {
		$("#rab").text(rab);
		$("#zab").text(zab);
	});

	socket.on("error", function(e) {
		console.log(e ? e : "Unknown error occurred; 'error' received on socket with no value for 'e'");
	});

    // Execute whenever the form is submitted:
	$("#foo").submit(function(e) {
		e.preventDefault(); // don't allow the form to submit

		var bar = $("#bar").val();
		var baz = $("#baz").val();
		socket.emit("foo", bar, baz);

		$("#bar").val("");
		$("#baz").val("");
	});
	
})
