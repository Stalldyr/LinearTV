from hypermedia import Html, Head, Link, Script, Meta, Title, Body

def base(title, description) -> Html:
  return Html(
    Head(
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