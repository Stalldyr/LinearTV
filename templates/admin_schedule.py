from hypermedia import *
from flask import url_for
from tvcore.schemas import SeriesOutput, MovieOutput
from tvcore.tvdatabase import TVDatabase, Series, Movie
try:
    from tvcore.schemas import TVConfig
except:
    from tvstreamer.tvcore.schemas import TVConfig

tvdb = TVDatabase()
config = TVConfig.from_file()

all_series = tvdb.get_series()
all_movies = tvdb.get_movies()
GENRES = config.genres

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
        ),
        Script("""
        function validateTmdbField() {
            if (!document.getElementById('programTmdbId').value) {
                alert('Please enter a TMDB ID');
                return false;
            }
        }
    """)
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
    Button(
        "Edit schedule",
        class_="program-button",
        id="scheduleBtn",
        hx_get="/admin/partials/schedule-form-open",
        hx_target="#schedule-form-container",
	    hx_swap="innerHTML",
    ),

    Table(class_="schedule-calendar"),

    Div(class_="overlay", id="overlay"),

    Div(id="program-form-container")
  )

def program_form_panel(visible=False) -> Element:
    """
    Full program form panel. Rendered once; toggled via JS.
    Left column: identity fields. Right column: metadata fields.
    """

    style = {"display":"block"} if visible else  {"display":"none"}

    return Div(
        H3("Edit program"),

        # media type radio (not using radio_inline helper since structure differs slightly)
        Div(
            Input(
                type="radio",
                name="programType",
                id="programOption0",
                value="series",
                hx_get="/admin/partials/program-type-select",
                hx_target="#programSelectContainer",
                hx_swap="innerHTML",
                checked = True
            ),
            Label("Series", for_="programOption0"),
            Input(
                type="radio",
                name="programType",
                id="programOption1",
                value="movie",
                hx_get="/admin/partials/program-type-select",
                hx_target="#programSelectContainer",
                hx_swap="innerHTML",
            ),
            Label("Film", for_="programOption1"),
            class_="media-select",
        ),

        Div(
            program_select(all_series),
            SeriesForm().render(GENRES),
            id="programSelectContainer"
        ),

        id="programForm",
        class_="program-form",
        style=style
    )

def generate_program_form(formtype: type, program_list: list):
    return ElementList(
        program_select(program_list),
        formtype().render(GENRES)
    )

def program_title_options(program_data: list[SeriesOutput]) -> Element:
    return Select(
        Option("--New series--", disabled=True, selected=True),
        *[Option(e.title, value=e.id, id=str(e.id)) for e in program_data],
        id="programTitleSelect",
        hx_get = "/admin/partials/program-select",
        hx_target = "#programFormData",
        hx_include="#programOption0, #programOption1",
        name="program_id"
    )

def program_select(program_data):
  return Div(
      Label("Choose series:", id="programTitleSelectLabel"),
      program_title_options(program_data),
      class_="form-group",
    )

class ProgramForm:
    def __init__(self, program: Series | None = None):
        super().__init__(program)

    def __init__(self, program=None):
        self.program = program

    def _value(self, field: str):
        if self.program is None:
            return None
        
        return getattr(self.program, field, None)
    
    def _create_form_group(self, *args):
        return Div(*args, class_="form-group")

    def tmdb_field(self):
        return self._create_form_group(
            Label("TMDB-id:"),
            Input(type="text", name="tmdb_id", id="tmdb_id", value=self._value("tmdb_id")),
            Button("Fetch", 
                type="button",
                class_="mini-button",
                id="fetchMetaDataButton",
                hx_get="/admin/partials/tmdb-fetch",
                hx_target="#programFormData",
                hx_include="#programOption0, #programOption1, #tmdb_id"
            )
        )

    def title_field(self):
        return self._create_form_group(
            Label("Title*:"),
            Input(type="text", name="title", value=self._value("title"))
        )

    def description_field(self):
        return self._create_form_group(
            Label("Description:"),
            TextArea(self._value("description"), name="description", rows="4")
        )

    def genre_field(self, genres: list[str]):
        return self._create_form_group(
            Label("Genre:"),
            Select(*[Option(g, value=g, selected=(g == self._value("genre"))) for g in genres], name="genre")
        )

    def release_field(self):
        return self._create_form_group(
            Label("Release:"),
            Input(type="text", name="release", value=self._value("release"))
        )

    def source_url_field(self):
        return self._create_form_group(
            Label("URL:"),
            Input(type="text", name="source_url", value=self._value("source_url"))
        )
    
    def buttons_field(self):
        return Div(
            Button("Cancel", type="button", class_="cancel-btn", 
                hx_get="/admin/partials/program-form-close", 
                hx_target="#program-form-container"),
            Button(
                "Delete",
                hx_post="delete/program"
            ),
            Button("Save", type="submit", class_="save-btn"),
            class_="form-buttons",
        )
    

class SeriesForm(ProgramForm):
    def __init__(self, program: Series | None = None):
        super().__init__(program)

    def season_field(self) -> Div:
        return self._create_form_group(
            Label("Season*:"),
            Input(type="text", name="start_season", value=self._value("start_season"))
        )

    def episode_field(self) -> Div:
        return self._create_form_group(
            Label("Episode*:"),
            Input(type="text", name="start_episode", value=self._value("start_episode"))
        )

    def reverse_field(self) -> Div:
        return self._create_form_group(
            Label("Reverse playlist:"),
            Input(type="checkbox", name="reverse_order", checked=self._value("reverse_order"))
        )

    def render(self, genres: list[str]=None) -> Element:
        if genres is None:
            genres = GENRES

        return Form(
            Input(type="hidden", name="program_id", value=self._value("id")),
            Div(
                self.tmdb_field(),
                self.title_field(),
                self.season_field(),
                self.episode_field(),
                self.source_url_field(),
                class_="column"
            ),
            Div(
                self.description_field(),
                self.release_field(),
                self.genre_field(genres),
                self.reverse_field(),
                class_="column"
            ),
            self.buttons_field(),
            hx_post="/admin/save/series",
            id="programFormData",
        )

class MovieForm(ProgramForm):
    def __init__(self, program: Movie | None = None):
        super().__init__(program)

    def duration_field(self):
        return self._create_form_group(
            Label("Duration*:"),
            Input(type="text", name="duration", value=self._value("duration"))
        )

    def render(self, genres: list[str]) -> Element:
        return Form(
            Input(type="hidden", name="program_id", value=self._value("id")),
            Div(
                self.tmdb_field(),
                self.title_field(),
                self.source_url_field(),
                class_="column"
            ),
            Div(
                self.description_field(),
                self.release_field(),
                self.genre_field(genres),
                self.duration_field(),
                class_="column"
            ),
            self.buttons_field(),
            hx_post="/admin/save/movie",
            id="programFormData",
        )