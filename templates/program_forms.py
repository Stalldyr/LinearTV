from hypermedia import H3, H4, Label, Option, Div, Form, Input, Select, P, Hr
from tvcore.tvdatabase import TVDatabase, Series, Movie, Episode
from datetime import date, datetime


try:
    from tvcore.schemas import TVConfig
    from templates.buttons import button
    from templates.forms import *
except:
    from tvstreamer.tvcore.schemas import TVConfig
    from tvstreamer.templates.buttons import button
    from tvstreamer.templates.forms import *

config = TVConfig.from_file()
tvdb = TVDatabase()

SERIES = tvdb.get_series()
MOVIES = tvdb.get_movies()
GENRES = config.genres
CHANNELS = tvdb.get_channels()

class FormBase():
    def __init__(self, entry=None):
        self.entry = entry

    def _value(self, field: str):
        if self.entry is None:
            return None
        return getattr(self.entry, field, None)

    def form_panel(cls, title: str, header, form_fields) -> Div:
        return Div(
            H3(title),
            header,
            Hr(class_="p-2"),
            form_fields,
            Div(id="form-status"),
            id = "form-panel"
        )
     
    def form_fields(self, form:Form|None = None, **kwargs) -> Div:
        return Div(
            form,
            id="form-fields",
            **kwargs
        )
    
    def form_header(self, *elements, **kwargs) -> Div:    
        return Div(
            *elements,
            id="form-header",
            class_ = "p-2",
            **kwargs
        )
    
    def program_dropdown(self, program_data: list, hx_get, hx_target="#form-fields", **kwargs) -> Div:
        return form_group(
            form_label("Choose program:"),
            form_select(
                Option("--New program--", selected=True),
                *[Option(e.title, value=e.id) for e in program_data],
                name="program_id",
                hx_get=hx_get,
                hx_target=hx_target,
                **kwargs
            )
        )
    
    def title_field(self):
        return form_group(
            form_label("Title*:"),
            form_input(type="text", name="title", value=self._value("title"))
        )
    
    def buttons_field(self, delete_post=""):
        buttons = [
            button(
                "Cancel", 
                color="grey", 
                size="form",
                _="on click add .hidden to #overlay then hide #form-panel"
            ),
            button(
                "Save",
                color="cyan2", 
                size="form",
                type="submit"
            ),
        ]

        if delete_post and self.entry:
            buttons.insert(
                1, 
                button(
                    "Delete",
                    size="form",
                    hx_post = delete_post
                )
            )

        return Div(*buttons, class_="mt-3.75 text-right")

class ProgramFormBase(FormBase):
    def tmdb_field(self, hx_get):
        return form_group(
            form_label("TMDB-id:"),
            form_input_with_button(
                form_input(type="text", name="tmdb_id", id="tmdb_id", value=self._value("tmdb_id")),
                button(
                    "Fetch",
                    color="cyan",
                    size="mini",
                    hx_get=hx_get,
                    hx_include="#tmdb_id",
                    hx_target="#programFormData"
                )
            )
        )

    def description_field(self):
        return form_group(
            form_label("Description:"),
            form_text(self._value("description"), name="description", rows="4")
        )

    def genre_field(self, genres: list[str]):
        options = [Option(g, value=g, selected=(g == self._value("genre"))) for g in genres]
        return form_group(
            form_label("Genre:"),
            form_select(*options, name="genre")
        )

    def release_field(self):
        return form_group(
            form_label("Release:"),
            form_input(type="text", name="release", value=self._value("release"))
        )

    def source_url_field(self):
        return form_group(
            form_label("URL:"),
            form_input(type="text", name="source_url", value=self._value("source_url"))
        )
    



class SeriesForm(ProgramFormBase):
    def __init__(self, program: Series | None = None):
        super().__init__(program)

    def panel(self, program_data: list):
        header = self.form_header(
            self.program_dropdown(program_data, "/admin/partials/series/fields")
        )

        form_fields = self.form_fields(
            self.form()
        )

        return self.form_panel(
            "Edit series",
            header,
            form_fields
        )
    
    def season_field(self) -> Div:
        return form_group(
            form_label("Season:"),
            form_input(type="text", name="start_season", value=self._value("start_season"))
        )

    def reverse_field(self) -> Div:
        return form_group(
            form_label("Reverse playlist:"),
            form_input(type="checkbox", name="reverse_order", checked=self._value("reverse_order"))
        )
    
    def form(self, genres: list[str]=GENRES) -> Form:
        return Form(
            form_input(type="hidden", name="program_id", value=self._value("id")),
            form_column(
                self.tmdb_field("/admin/partials/tmdb-fetch/series"),
                self.title_field(),
                self.description_field()
            ),
            form_column(
                self.release_field(),
                self.genre_field(genres),
                self.buttons_field("/admin/series/delete")
            ),
            hx_post="/admin/series/save",
            hx_target="#form-status",
            id="programFormData",
        )
    

class Duration(FormBase):
    def duration_field(self):
        return form_group(
            form_label("Duration:"),
            form_input(type="text", name="duration", value=self._value("duration"))
        )

class EpisodeBase(FormBase):
    def season_field(self) -> Div:
        return form_group(
            form_label("Season:"),
            form_input(type="text", name="season_number", value=self._value("season_number"))
        )
    
    def episode_field(self) -> Div:
        return form_group(
            form_label("Episode:"),
            form_input(type="text", name="episode_number", value=self._value("episode_number"))
        )

class MovieForm(ProgramFormBase, Duration):
    def __init__(self, program: Movie | None = None):
        super().__init__(program)

    def panel(self, program_data: list):
        header = self.form_header(
            self.program_dropdown(program_data, "/admin/partials/movie/fields")
        )

        fields = self.form_fields(
            self.form()
        )
        
        return self.form_panel(
            "Edit movies",
            header,
            fields
        )

    def form(self, genres:list[str] = GENRES) -> Form:
        return Form(
            form_input(type="hidden", name="program_id", value=self._value("id")),
            form_column(
                self.tmdb_field("/admin/partials/tmdb-fetch/movie"),
                self.title_field(),
                self.description_field()
            ),
            form_column(
                self.source_url_field(),
                self.release_field(),
                self.genre_field(genres),
                self.duration_field(),
                #schedule_field
                self.buttons_field("/admin/movie/delete")
            ),
            hx_post="/admin/movie/save",
            hx_target="#form-status",
            id="programFormData",
        )
    

class EpisodesForm(ProgramFormBase, Duration, EpisodeBase):
    def __init__(self, program: Episode | None = None):
        super().__init__(program)


    def panel(self, program_data) -> Div:
        header = self.form_header(
            self.program_dropdown(program_data,"/admin/partials/episodes/select", hx_target="#episode-select"),
            self.episode_dropdown([])
        )

        form_fields = self.form_fields(
            self.form()
        )

        return self.form_panel(
            "Edit episodes",
            header,
            form_fields
        )
    
    def episode_dropdown(self, program):
        return form_group(
            form_label("Choose episode:"),
            form_select(
                Option("--New episode--", selected=True),
                *[Option(e.title, value=e.id) for e in program],
                name = "episode_id",
                hx_get = "/admin/partials/episodes/fields",
                hx_target="#form-fields"
            ),
            id="episode-select"
        )
    

    def program_id_field(self) -> Div:
        return form_group(
            form_label("Program ID:"),
            form_input(type="text", name="program_id", value=self._value("program_id"))
        )
    
    def form(self) -> Form:
        return Form(
            form_input(type="hidden", name="series_id", value=self._value("series_id")),
            form_input(type="hidden", name="episode_id", value=self._value("id")),
            form_column(
                #self.tmdb_field("/admin/partials/tmdb-fetch/series"),
                self.title_field(),
                self.source_url_field(),
                self.description_field()
            ),
            form_column(
                self.season_field(),
                self.episode_field(),
                self.program_id_field(),
                self.duration_field(),
                self.buttons_field()
            ),
            hx_post="/admin/season/save",
            hx_target="#form-status",
            id="programFormData",
        )

class SeasonForm(ProgramFormBase, EpisodeBase):
    def __init__(self, program: Series | None = None):
        super().__init__(program)

    def panel(self, program_data: list):
        header = self.form_header(
            self.program_dropdown(program_data, "/admin/partials/season/fields")
        )

        form_fields = self.form_fields(
            self.form()
        )

        return self.form_panel(
            "Add season",
            header,
            form_fields
        )

    
    def form(self) -> Form:
        return Form(
            form_input(type="hidden", name="series_id", value=self._value("series_id")),
            form_input(type="hidden", name="episode_id", value=self._value("id")),
            form_column(
                self.source_url_field()
            ),
            form_column(
                self.season_field(),
                self.buttons_field()
            ),
            hx_post="/admin/episode/save",
            hx_target="#form-status",
            id="programFormData",
        )


class ScheduleFormElements():
    def rerun_check(self):
        return form_group(
            form_label("Re-run:"),
            form_input(type="checkbox", name="rerun", id="isRerun", checked=self._value("rerun"))
        )
    
    def channel_select(self, *channels):
        return form_group(
            form_label("Channel:"),
            form_select(
                *channels,
                name="channel"
            )
        )

    def datetime_select(self, **kwargs):
        return form_group(
            form_label("Date"),
            form_input(
                type="datetime-local",
                value=datetime.now().isoformat(timespec="minutes"),
                name="datetime",
                id="date-select",
                **kwargs
            )
        )
    
    def date_select(self, **kwargs):
        return form_group(
            form_label("Date"),
            form_input(
                type="date",
                value=date.today(),
                name="date",
                id="date-select",
                **kwargs
            )
        )

class ScheduleForm(FormBase, ScheduleFormElements):
    def panel(self) -> Div:
        channels = [Option(e, value=e) for e in CHANNELS]

        header = self.form_header(
            Form(
                self.channel_select(*channels),
                self.date_select(),
                hx_get = "/admin/partials/schedule/programs",
                hx_trigger = "change",
                hx_target = "#program-select"
            ),
            self.program_select([])
        )

        form_fields = self.form_fields(
            self.form()
        )

        return self.form_panel(
            "Edit schedule",
            header,
            form_fields
        )
        
    def program_select(self, data: list):
        return form_group(
            Form(
                form_label("Program:"),
                form_select(
                    *[Option(
                        e.start.time().isoformat() + " " + e.title, 
                        value=e.id
                    ) for e in data],
                    name="schedule_id",
                    hx_get="/admin/partials/schedule/fields",
                    hx_target="#form-fields",
                )
            ),
            id = "program-select"
        )
        
    def start_group(self):
        return form_group(
            form_label("Start time:"),
            form_input(type="time", name="time", value=self._value("start") and self._value("start").time().isoformat())
        )
    
    def duration_group(self):
        return form_group(
            form_label("Duration:"),
            #TODO: text container
        )
    
    def form(self):
        return Form(
            Input(type="hidden", name="schedule_id", value=self._value("id")),
            self.title_field(),
            self.channel_select(*[Option(e, value=e) for e in CHANNELS]),
            self.start_group(),
            self.rerun_check(),
            self.buttons_field(),
            hx_post="/admin/schedule/update",
            hx_include="#date-select",
            hx_target="#form-status",
            id="schedule-fields-container"
        )
    
class NewScheduleForm(FormBase, ScheduleFormElements):
    #def __init__(self, program_type):
    #    self.program_type = program_type

    def panel(self) -> Div:
        channels = [Option(e, value=e) for e in CHANNELS]

        header = self.form_header(
            Form(
                self.channel_select(*channels),
                self.datetime_select(),
                self.program_type_select(),
                hx_get="/admin/partials/schedule/conflict-check",
                hx_target="#schedule-conflict",
                hx_trigger="change"
            ),
            Div(
                id="schedule-conflict"
            )
        )

        form_fields = self.form_fields(
            Div("")
            #self.form()
        )

        return self.form_panel(
            "Add to schedule",
            header,
            form_fields
        )
    
    def program_type_select(self):
        return form_group(
            form_label("Type:"),
            Input(
                type="radio",
                name="programType",
                value="series",
                checked=True,
            ),
            Label("Serie"),
            Input(
                type="radio",
                name="programType",
                value="movie"
            ),
            Label("Film")
        )
    
    def program_select(self, data: list):
        return form_group(
            form_label("Program:"),
            form_select(
                *[Option(e.title, value=e.id) for e in data],
                name="program_id",
                hx_get="/admin/partials/schedule/new-fields",
                hx_target="#form-fields"
            )
        )
    
    def program_selector(self):
        return Form(
            form_group(

            ),
            Div(
                self._programs([]),
                id="schedule-programs"
            ),
            id="schedule-program-form"
        )

    def _programs(self, program_data) -> Div:
        return form_group(
            form_label("Program:"),
            form_select(
                Option("--Velg program--", value="", selected=True),
                *[Option(p.title, value=p.id) for p in program_data],
                name="program_id",
                hx_get="/admin/partials/schedule/episodes",
                hx_target="#form-fields",
                hx_trigger="change"
            )
        )
    
    def _episodes(self, program_data):
        return form_group(
            form_select(
                Option("--Velg program--", value="", selected=True),
                *[Option(p.title, value=p.id) for p in program_data],
                name="program_id",
                hx_get="/admin/partials/schedule/new-forms",
                hx_target="#schedule-episode-selector",
                hx_trigger="change"
            )
        )        
    
    def form(self):
        return Form(
            Input(type="hidden", name="schedule_id", value=self._value("id")),
            self.title_field(),
            self.rerun_check(),
            self.buttons_field(),
            hx_post="/admin/schedule/update",
            hx_include="#date-select",
            hx_target="#form-status",
            id="schedule-fields-container"
        )