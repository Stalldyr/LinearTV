from hypermedia import *
from flask import url_for

from lineartvstream.tvcore.tvdatabase import TVDatabase

tv_db = TVDatabase()


def stream_html() -> ElementList:
    return ElementList(
        stream_head(),
        stream_main()
    )

def stream_head():
    return ElementList(
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/video.js@8.23.4/dist/video-js.min.css"),
        Script(src="https://cdn.jsdelivr.net/npm/video.js@8.23.4/dist/video.min.js"),

        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/videojs-logo@latest/dist/videojs-logo.css"),
        Script(src="https://cdn.jsdelivr.net/npm/videojs-logo@latest/dist/videojs-logo.min.js"),

        Script("""
            window.SILVERMINE_VIDEOJS_CHROMECAST_CONFIG = {
                preloadWebComponents: true,
            };
        """),
        Script(src=url_for('static', filename='scripts/stream.js')),
        Script(
            src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.js",
            integrity="sha384-Q+Dky3iHVJOr6wUjQ4ulh6uQ76an/t+ak1+PjMVaxRjbZamFLAG+u9InkfjbsEQf",
            crossorigin="anonymous"
        ),
        Script(
            src="https://cdn.jsdelivr.net/npm/htmx-ext-sse@2.2.4", 
            integrity="sha384-A986SAtodyH8eg8x8irJnYUk7i9inVQqYigD6qZ9evobksGNIXfeFvDwLSHcp31N", 
            crossorigin="anonymous"
        )
    )

def stream_main():
    channels = tv_db.get_channels()
    if not channels:
        return Div("There's no channels in database")

    return Div(
        Video(
            content="",#no_javascript().dump(),
            id="tvPlayer",
            class_="video-js",
            preload="auto",
            controls=True,
        ),

        channel_selector(channels),
        stream_channel_panel(channels[0].channel_id)
    )


def no_javascript():
    return P(
        "To view this video please enable JavaScript, and consider upgrading to a web browser that ",
        A("supports HTML5 video",  href="https://videojs.com/html5-video-support/", target="_blank"),
        class_="vjs-no-js"
    )

def stream_channel_panel(channel):
    return Div(
        id="stream-channel-panel",
        sse_swap="program-update",
        hx_swap="innerHTML",
        hx_on__after_swap="onProgramChanged(this.firstElementChild)",
        hx_ext="sse",
        sse_connect=f"/stream/{channel}/events"
    )

def channel_selector(channels:list):
    return Div(
        *[Button(
            c.display_name, 
            id=c.channel_id, 
            hx_get=url_for("streaming.htmx.stream_panel", channel=c.channel_id),
            hx_target="#stream-channel-panel",
            hx_swap="outerHTML",
        ) for c in channels],
        class_="channelSelector"
    )

