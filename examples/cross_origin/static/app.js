$(document).ready(function () {

    var $sayhi = $('#sayhi');
    var $messages = $('#messages');

    function message (m) {
        $messages.append($('<li></li>').html(m));
    }

    var sock = io.connect('http://localhost:9090');
    sock.on('connect', function () {
        message('Connected');
    });

    sock.on('disconnect', function () {
        message('Goodbye!');
    });

    sock.on('greetings', function (data) {
        console.log(data);
        console.log(arguments);
        message('Greetings from ' + data.from);
    });

    $sayhi.click(function (event) {
        event.preventDefault();
        sock.emit('hello', {'from': 'the application'})
    });
});
