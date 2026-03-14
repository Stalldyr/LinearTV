from hypermedia import *
from flask import url_for

def base_schedule() -> ElementList:
  return Html(
    Head(
        Link(
            rel="stylesheet",
            href=url_for('streaming.static', filename='styles/schedule.css')
        ),
        Link(
            rel="stylesheet",
            href=url_for('streaming.static', filename='styles/form.css')
        ),
        Title("Admin"),
        Meta(
          charset="UTF-8"
        ),
        Meta(
          name="description",
          content="Administrative panel for managing broadcasting schedule"
        )
    ),
    Body(
      schedule_panel()
    ),
    Footer(
      Script(
        src="https://unpkg.com/htmx.org@2.0.0",
        integrity="sha384-wS5l5IKJBvK6sPTKa2WZ1js3d947pvWXbPJ1OmWfEuxLgeHcEbjUUA5i9V5ZkpCw",
        crossorigin="anonymous"
      )
    )
  )

def schedule_panel():
  return ElementList(
    H1("Schedule Admin"),
    Button(
      "Add or update program",
      class_="program-button",
      id="programBtn",
      hx_get="/admin/partials/program-form-open",
      hx_target="#program-form-container",
	    hx_swap="innerHTML",
    ),

    Table(class_="schedule-calendar"),

    Div(class_="overlay", id="overlay"),

    Div(id="program-form-container")
  )


def program_title_options(series_data: list) -> Element:
    return Select(
        Option("--New series--", disabled=True, selected=True),
        *[Option(e["title"], id=str(e["id"])) for e in series_data],
        id="programTitleSelect",
        onchange="updateProgramForm()",
        name="program_id"
    )


def genre_options(genres: list[str]) -> Element:
    return Select(
        *[Option(g, label=g) for g in genres],
        id="programGenre",
        name="genre"
    )

def program_select(program_data):
  return Div(
      Label("Choose series:", id="programTitleSelectLabel"),
      program_title_options(program_data),
      class_="form-group",
    )
   

def series_form(series_data: list, genres: list[str]) -> Element:
    left_column = Div(
        # Series/film selector
        Div(
            Label("Choose series:", id="programTitleSelectLabel"),
            program_title_options(series_data),
            class_="form-group",
        ),

        # TMDB id + fetch
        Div(
            Label("TMDB-id:"),
            Input(type="text", id="programTmdbId", name="tmdb_id"),
            class_="form-group",
        ),
        Button(
          "Fetch",
          type="button",
          class_="mini-button",
          id="fetchMetaDataButton",
          onclick="fetchMetaData()"
        ),

        # Title
        Div(
            Label("Title*:"),
            Input(type="text", id="programTitle", name="title"),
            class_="form-group",
        ),

        # Season
        Div(
            Label("Season*:", id="programSeasonLabel"),
            Input(type="text", id="programSeason", name="start_season", required=True),
            class_="form-group",
        ),

        # Episode
        Div(
            Label("Episode*:", id="programEpisodeLabel"),
            Input(type="text", id="programEpisode", name="start_episode", required=True),
            class_="form-group",
        ),

        # URL
        Div(
            Label("URL:"),
            Input(type="text", id="programUrl", name="source_url"),
            class_="form-group",
        ),

        class_="column",
    )

    right_column = Div(
        # Description
        Div(
            Label("Description:"),
            TextArea(
                name="description",
                placeholder="Beskrivelse av programmet",
                rows="4",
                id="programDescription",
            ),
            class_="form-group",
        ),

        # Release
        Div(
            Label("Release:"),
            Input(type="text", id="programRelease", name="release"),
            class_="form-group",
        ),

        # Genre
        Div(
            Label("Genre:"),
            genre_options(genres),
            class_="form-group",
        ),

        # Reverse playlist
        Div(
            Label("Reverse playlist:", id="programIsReverseLabel"),
            Input(type="checkbox", id="programIsReverse", name="is_reverse"),
            class_="form-group",
        ),

        Div(
            Button("Cancel", type="button", class_="cancel-btn", hx_get="/admin/partials/program-form-close", hx_target="#program-form-container",  hx_swap="innerHTML"),
            #Button("Delete", type="button", class_="delete-btn", onclick=delete_onclick),
            Button("Save", type="submit", class_="save-btn"),
            class_="form-buttons",
        ),

        class_="column",
    )

    return Form(
      Input(type="hidden", name="program_id", id="programId", value=""),
      left_column,
      right_column,
      id="programFormData",
      hx_post="/admin/save/series",
      #hx_target="#program-form-container",
      #hx_swap="innerHTML"
    )

def movie_form(movie_data: list, genres: list[str]) -> Element:
    left_column = Div(
        # Series/film selector
        Div(
            Label("Choose movie:", id="programTitleSelectLabel"),
            program_title_options(movie_data),
            class_="form-group",
        ),

        # TMDB id + fetch
        Div(
            Label("TMDB-id:"),
            Input(type="text", id="programTmdbId", name="tmdb_id"),
            class_="form-group",
        ),
        Button(
          "Fetch",
          type="button",
          class_="mini-button",
          id="fetchMetaDataButton",
          onclick="fetchMetaData()"
        ),

        # Title
        Div(
            Label("Title*:"),
            Input(type="text", id="programTitle", name="title"),
            class_="form-group",
        ),

        # URL
        Div(
            Label("URL:"),
            Input(type="text", id="programUrl", name="source_url"),
            class_="form-group",
        ),

        class_="column",
    )

    right_column = Div(
        # Description
        Div(
            Label("Description:"),
            TextArea(
                name="description",
                placeholder="Beskrivelse av programmet",
                rows="4",
                id="programDescription",
            ),
            class_="form-group",
        ),

        # Release
        Div(
            Label("Release:"),
            Input(type="text", id="programRelease", name="release"),
            class_="form-group",
        ),

        # Genre
        Div(
            Label("Genre:"),
            genre_options(genres),
            class_="form-group",
        ),

        # Duration
        Div(
            Label("Duration*:"),
            Input(type="text", id="programDuration", name="duration", required=True),
            class_="form-group",
        ),

        Div(
            Button("Cancel", type="button", class_="cancel-btn", hx_get="/admin/partials/program-form-close", hx_target="#program-form-container",  hx_swap="innerHTML"),
            Button("Delete", type="button", class_="delete-btn", hx_post="/admin/delete_program"),
            Button("Save", type="submit", class_="save-btn"),
            class_="form-buttons",
        ),

        class_="column",
    )

    return Form(
      Input(type="hidden", name="program_id", id="programId", value=""),
      left_column,
      right_column,
      id="programFormData",
      hx_post="/admin/save/movie",
      #hx_target="#program-form-container",
      #hx_swap="innerHTML"
    )

def program_form(visible=False) -> Element:
    """
    Full program form panel. Rendered once; toggled via JS.
    Left column: identity fields. Right column: metadata fields.
    """

    style = {"display":"block"} if visible else  {"display":"none"}

    return Div(
        H3("Legg til nytt program"),

        # media type radio (not using radio_inline helper since structure differs slightly)
        Div(
            Input(
              type="radio", 
              name="programType",
              id="programOption0",
              value="series",
              hx_get="/admin/partials/program-select",
              hx_target="#programSelectContainer",
              hx_swap="innerHTML",
              checked=True
            ),
            Label("Series", for_="programOption0"),
            Input(
              type="radio",
              name="programType",
              id="programOption1",
              value="movie",
              hx_get="/admin/partials/program-select",
              hx_target="#programSelectContainer",
              hx_swap="innerHTML",
            ),
            Label("Film", for_="programOption1"),
            class_="media-select",
        ),
        
        Div(id="programSelectContainer"),         

        id="programForm",
        class_="program-form",
        style=style
    )
