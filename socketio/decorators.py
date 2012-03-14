import gevent

def require_connection(fn):
    # TODO: hey, will we need that somewhere ?  that'd be safer, huh ?
    def wrapped(ctx, *args, **kwargs):
        io = ctx.io

        if not io.session.connected:
            ctx.kill()
            ctx.debug("not connected on %s: exiting greenlet", fn.__name__)
            raise gevent.GreenletExit()

        return fn(ctx, *args, **kwargs)

    return wrapped
