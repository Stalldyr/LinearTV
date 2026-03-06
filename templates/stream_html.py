from hypermedia import *
from flask import url_for

def stream_html() -> ElementList:
    return ElementList(
        stream_head(),
        Body(
            stream_main()
        )
    )

def stream_head():
    return ElementList(
        Link(rel="stylesheet", href=url_for('static', filename='node_modules/video.js/dist/video-js.min.css')),
        Script(src=url_for('static', filename='node_modules/video.js/dist/video.min.js')),

        Script(src=url_for('static', filename='node_modules/videojs-offset/dist/videojs-offset.min.js')),
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/videojs-logo@latest/dist/videojs-logo.css"),
        Script(src="https://cdn.jsdelivr.net/npm/videojs-logo@latest/dist/videojs-logo.min.js"),

        Script("""
            window.SILVERMINE_VIDEOJS_CHROMECAST_CONFIG = {
                preloadWebComponents: true,
            };
        """),
        Link(rel="stylesheet", href=url_for('static', filename='node_modules/@silvermine/videojs-chromecast/dist/silvermine-videojs-chromecast.css')),
        Script(src=url_for('static', filename='node_modules/@silvermine/videojs-chromecast/dist/silvermine-videojs-chromecast.min.js')),
        Script(type="text/javascript", src="https://www.gstatic.com/cv/js/sender/v1/cast_sender.js?loadCastFramework=1"),
        Script(src=url_for('static', filename='scripts/stream.js'))
        
    )

def stream_main():
    return Div(
        Video(
            content="""
            <p class="vjs-no-js">
                To view this video please enable JavaScript, and consider upgrading to a
                web browser that
                <a href="https://videojs.com/html5-video-support/" target="_blank">
                    supports HTML5 video
                </a>
            </p>
            """,
            #src=url_for('streaming.static', filename='PM5544.mp4'),
            id="tvPlayer",
            class_="video-js",
            preload="auto",
            controls=True,
        ),

        Div(
            H2(id="programTitle"),
            P(id="programTime"),
            P(id="programDescription"),
            P(id="nextProgram"),
            id="streaminfo",
            slot="streaminfo"
        ),
       
    )

def update_program(program):
    if program.status == "available": #Change status to global variable
        if program.offset > program.duration:
            source = url_for("streaming.static", filename="PM5544.mp4" )
        else:
            source = program.filepath


