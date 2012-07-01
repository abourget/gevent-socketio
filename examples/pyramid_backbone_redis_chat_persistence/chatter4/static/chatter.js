$(document).ready(function() {
    // connect to the websocket
    var socket = io.connect();
    socket.emit('subscribe')

    var ChatModel = Backbone.Model.extend({
    });

    var ChatItem = Backbone.View.extend({
        render: function(){
            var template = Handlebars.compile($("#chat_item_template").html());
            this.$el.html(template(this.model));

            return this;
        },
    });

    // a collection that will hit a RESTful webservice and pull back all
    // results serialized as backbone models
    var ChatCollection = Backbone.Collection.extend({
        url: "/get_log"
    });


    var ChatView = Backbone.View.extend({
        events: {
            "submit #chat_form": "send"
        },

        send: function(evt) {
            evt.preventDefault();
            var val = $("#chatbox").val();

            socket.emit("chat", val);
            $("#chatbox").val("");
        },

        initialize: function() {
            var me = this;

            socket.on("chat", function(e) {
                me.$("#chatlog").append(new ChatItem({
                    model: e
                }).render().el);
            });

            // re-render the view if the collection fires a reset event
            this.collection.on("reset", function() {
                me.render();
            });
        },

        render: function(){
            var template = Handlebars.compile($("#chat_template").html());

            $(this.el).html(template({
                collection: this.collection.toJSON()
            }));
        },

    });

    var Router = Backbone.Router.extend({

        routes: {
            "": "index"
        },

        index: function() {
            var collection = new ChatCollection();

            var view = new ChatView({
                collection: collection,
                el: $("#container")
            });

            // pull the data from the server
            collection.fetch();

            view.render();
        }

    });

    var router = new Router();
    Backbone.history.start({ pushState: true });

});
