<html>
  <head>
    <title>Chatter!</title>
    <script src="/static/jquery.js" type="text/javascript"></script>
    <script src="/static/socket.io.js" type="text/javascript"></script>
    <script src="/static/handlebars.js" type="text/javascript"></script>
    <script src="/static/underscore.js" type="text/javascript"></script>
    <script src="/static/backbone.js" type="text/javascript"></script>
    <script src="/static/chatter.js" type="text/javascript"></script>
    <link rel="stylesheet" type="text/css" href="/static/styles.css" />
  </head>
  <body>
  <div id="container">
    <h1>Chat Log</h1>
    <div id="chatlog"></div><br />
    <form id="chat_form">
      <input type="text" id="chatbox"></input>
      <button type="submit" id="submit">Send</button>
    </form>
    <button id="b1">Test 1</button>
    <button id="b2">Test 2</button>
    <button id="b3">Test 3</button>
    <button id="b4">Test 4</button>
    <button id="b5">Test 5</button>
    <button id="b6">Test 6</button>
    <button id="b7">Test 7</button>
    <button id="rtc_button">Send WebRTC invitation</button>
    <video id="rtc_video"></video>
    <video id="rtc_remote_video"></video>
  </div>
  </body>
</html>
