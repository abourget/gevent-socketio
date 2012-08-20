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
    <button id='join'>join</button>
  </div>
  </body>
</html>
