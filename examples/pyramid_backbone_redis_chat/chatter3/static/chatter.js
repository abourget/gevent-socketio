$(document).ready(function() {
    WEB_SOCKET_SWF_LOCATION = "/static/WebSocketMain.swf";
    WEB_SOCKET_DEBUG = true;

    // connect to the websocket
    var socket = io.connect();
    socket.emit('subscribe')

    // Backbone.js model that will represent our chat log coming in
    var ChatModel = Backbone.Model.extend({
    });

    // The view that reprsents an individual chat line
    var ChatItem = Backbone.View.extend({
        render: function(){
            // grab the handlebars.js template we defined for this view
            var template = Handlebars.compile($("#chat_item_template").html());

            // render the template out with the model as a context
            this.$el.html(template(this.model.toJSON()));

            // always return this for easy chaining
            return this;
        },
    });

    // The view that represents our chat form
    var ChatView = Backbone.View.extend({

        // handle the form submit event and fire the method "send"
        events: {
            "submit #chat_form": "send"
        },

        send: function(evt) {
            evt.preventDefault();

            var val = $("#chatbox").val();

            socket.emit("chat", val);

            $("#chatbox").val("");
        },

        // constructor of the view
        initialize: function() {
            var me = this;

            // when a new chat event is emitted, add the view item to the DOM
            socket.on("chat", function(e) {

                // create the view and pass it the new model for context
                var chat_item = new ChatItem({
                    model: new ChatModel({
                        chat_line: e
                    })
                });

                // render it to the DOM
                me.$("#chatlog").append(chat_item.render().el);
            });
        },

        render: function(){
            var template = Handlebars.compile($("#chat_template").html());
            $(this.el).html(template());
        },

    });

    // Backbone.js router
    var Router = Backbone.Router.extend({
        // Match urls with methods
        routes: {
            "": "index"
        },

        index: function() {
            var view = new ChatView({
                el: $("#container"),
            });

            view.render();
        }

    });

    // start backbone routing
    var router = new Router();
    Backbone.history.start({ pushState: true });
});
