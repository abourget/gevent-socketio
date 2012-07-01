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

    <script id="chat_item_template" type="text/x-handlebars-template">
      <li>{{ chat_line }}</li>
    </script>
    <script id="chat_template" type="text/x-handlebars-template">
      <h1>Chat Log</h1>
      <ul id="chatlog">
        {{#each collection }}
          <li>{{ this.chat_line }}</li>
        {{/each}}
      </ul>
      <form id="chat_form">
        <input type="text" id="chatbox"></input>
        <button type="submit" id="submit">Send</button>
      </form>
    </script>
  </head>
  <body>
  <div id="container">
  </div>
  </body>
</html>
