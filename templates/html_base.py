from hypermedia import Html, Head, Link, Script, Meta, Title, Body
from flask import url_for

def base(title, description) -> Html:
  return Html(
    Head(
        Link(
            rel="stylesheet",
            href=url_for('streaming.static', filename='styles/output.css')
        ),
        Script(
           src="https://cdn.jsdelivr.net/npm/hyperscript.org@0.9.91/dist/_hyperscript.min.js",
           integrity="sha384-OT9bNmUa5rM34SmxFpRftn2F6GbgM/4xnTmn0z106OE5uvsigkdtUMOpdPKOigyO",
           crossorigin="anonymous"
        ),
        Script(
            src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.js",
            integrity="sha384-Q+Dky3iHVJOr6wUjQ4ulh6uQ76an/t+ak1+PjMVaxRjbZamFLAG+u9InkfjbsEQf",
            crossorigin="anonymous"
        ),
        Meta(
          charset="UTF-8"
        ),
        Title(title),
        Meta(
          name="description",
          content=description
        ),
        slot="head"
    ),
    Body(
        slot="body"
    )
  )