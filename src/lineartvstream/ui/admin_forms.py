from hypermedia import H3, Div, Form, Input, Option, Hr
from flask import url_for

from lineartvstream.tvcore.tvdatabase import Series, Movie, Episode, TVDatabase
from lineartvstream.ui.forms_style import (
    form_group, form_label, form_select, form_input,
    form_input_with_button, form_text, form_column
)
from lineartvstream.ui.buttons_style import button


tv_db = TVDatabase()


def form_panel(title: str, header, form_fields) -> Div:
    return Div(
        H3(title),
        header,
        Hr(class_="p-2"),
        form_fields,
        Div(id="form-status"),
        id="form-panel"
    )

def fields_container(form: Form | None = None, **kwargs) -> Div:
    return Div(form, id="form-fields", **kwargs)

def form_header(*elements, **kwargs) -> Div:
    return Div(*elements, id="form-header", class_="p-2", **kwargs)



class FormBase():
    def __init__(self, entry=None):
        self.entry = entry

    def _value(self, field: str):
        if self.entry is None:
            return None
        return getattr(self.entry, field, None)
     
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



    
    def title_field(self):
        return form_group(
            form_label("Title*:"),
            form_input(type="text", name="title", value=self._value("title"))
        )

    def program_id_field(self) -> Div:
        return form_group(
            form_label("Program-ID:"),
            form_input(type="text", name="program_id", value=self._value("program_id"))
        )

    def description_field(self):
        return form_group(
            form_label("Description:"),
            form_text(self._value("description"), name="description", rows="4")
        )

    def genre_select(self):
        genres = tv_db.get_genres()
        return form_group(
            form_label("Genre:"),
            form_select(
                *[Option(g.display_name, value=g.name) for g in genres],
                name="genre"
            )
        )

    def tmdb_field(self, endpoint):
        return form_group(
            form_label("TMDB-id:"),
            form_input_with_button(
                form_input(type="text", name="tmdb_id", id="tmdb_id", value=self._value("tmdb_id")),
                button(
                    "Fetch",
                    color="cyan",
                    size="mini",
                    hx_get=url_for(endpoint),
                    hx_include="#formData",
                    hx_target="#formData"
                )
            )
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

    def ytdlp_url_field(self, endpoint):
        return form_group(
            form_label("URL:"),
            form_input_with_button(
                form_input(type="text", name="source_url", id="source_url", value=self._value("source_url")),
                button(
                    "Fetch",
                    color="cyan",
                    size="mini",
                    hx_get=url_for(endpoint),
                    hx_include="#formData",
                    hx_target="#formData",
                    hx_swap="outerHTML"
                )
            )
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

    def channel_id_field(self) -> Div:
        return form_group(
            form_label("Channel-ID:"),
            form_input(type="text", name="channel_id", value=self._value("channel_id"))
        )

    def channel_name_field(self) -> Div:
        return form_group(
            form_label("Channel name:"),
            form_input(type="text", name="display_name", value=self._value("display_name"))
        )

    def genre_id_field(self) -> Div:
        return form_group(
            form_label("Genre-ID:"),
            form_input(type="text", name="name", value=self._value("name"))
        )

    def genre_name_field(self) -> Div:
        return form_group(
            form_label("Genre name:"),
            form_input(type="text", name="display_name", value=self._value("display_name"))
        )
    
    def duration_field(self):
        return form_group(
            form_label("Duration:"),
            form_input(type="text", name="duration", value=self._value("duration"))
        )

    def season_number_field(self) -> Div:
        return form_group(
            form_label("Season:"),
            form_input(type="text", name="season_number", value=self._value("season_number"))
        )
    
    def episode_number_field(self) -> Div:
        return form_group(
            form_label("Episode:"),
            form_input(type="text", name="episode_number", value=self._value("episode_number"))
        )


    def rerun_check(self):
        return form_group(
            form_label("Re-run:", for_="rerun"),
            form_input(type="checkbox", name="rerun", id="rerun", checked=self._value("rerun"))
        )

    def channel_select(self):
        channels = tv_db.get_channels()
        return form_group(
            form_label("Channel:"),
            form_select(
                *[Option(c.display_name, value=c.channel_id) for c in channels],
                name="channel"
            )
        )

    def datetime_select(self, **kwargs):
        return form_group(
            form_label("Date"),
            form_input(
                type="datetime-local",
                value=self._value("start"),#datetime.now().isoformat(timespec="minutes"),
                name="start",
                id="date-select",
                **kwargs
            )
        )

    def end_time(self):
        return Input(type="hidden", name="end", value=self._value("end"))

    
    def series_id_key(self):
        return Input(type="hidden", name="series_id", value=self._value("series_id"))

    def movie_id_key(self):
        return Input(type="hidden", name="movie_id", value=self._value("movie_id"))

    def episode_id_key(self):
        return Input(type="hidden", name="episode_id", value=self._value("episode_id"))

    def schedule_id_key(self):
        return Input(type="hidden", name="schedule_id", value=self._value("schedule_id"))

    def channel_key(self) -> Div:
        return Input(type="hidden", name="id", value=self._value("id"))

    def genre_id_key(self) -> Div:
        return Input(type="hidden", name="id", value=self._value("id"))


    
    
    def buttons_field(self):
        buttons = [
            button(
                "Save",
                color="cyan2", 
                size="form",
                type="submit"
            ),
        ]

        if self.entry:
            buttons.insert(
                1, 
                button(
                    "Delete",
                    size="form",
                    type="submit",
                    value="true"
                )
            )

        return Div(*buttons, class_="mt-3.75 text-right")

    def render_form(
        self,
        fields: list,
        post_endpoint: str,
        target: str = "#form-status",
        **kwargs
    ) -> Form:
        return Form(
            *fields,
            self.buttons_field(),
            Div(id="form-status"),
            id = "formData",
            hx_post = url_for(post_endpoint),
            hx_target = target,
            hx_swap = "innerHTML",
            **kwargs
        )



# ============ CHANNEL ============

class ChannelForm(FormBase):
    def __init__(self, entry=None):
        self.entry = entry

    def form(self) -> Form:
        print(self.entry)

        fields = [  
            self.channel_id_field(),
            self.channel_name_field()
        ]

        if self.entry:
            fields.append(self.channel_key())

        return self.render_form(fields, post_endpoint="streaming.admin_crud.channel_page")



# ============ GENRES ============

class GenreForm(FormBase):
    def __init__(self, entry=None):
        self.entry = entry

    def form(self) -> Form:
        fields = [  
            self.genre_id_field(),
            self.genre_name_field()
        ]

        if self.entry:
            fields.append(self.genre_id_key())

        return self.render_form(fields, post_endpoint="streaming.admin_crud.genre_page")

# ============ SERIES ============

class SeriesForm(FormBase):
    def __init__(self, entry: Series | None = None):
        self.entry = entry

    def form(self) -> Form:
        fields = [
            self.tmdb_field("streaming.htmx.tmdb_fetch_series"),
            self.title_field(),
            self.description_field(),
            self.release_field(),
            self.genre_select()
        ]

        if self.entry:
            fields.append(self.series_id_key())

        return self.render_form(fields, post_endpoint="streaming.admin_crud.series_page")

# ============ EPISODES ============

class EpisodesForm(FormBase):
    def __init__(self, entry: Episode | None = None, series_id: int | None = None, episode_id: int | None = None):
        self.entry = entry
        self.series_id = series_id
        self.episode_id = episode_id

    def series_id_key(self):
        series_id = self.series_id or self._value("series_id")
        return Input(type="hidden", name="series_id", value=series_id)

    def episode_id_key(self):
        episode_id = self.episode_id or self._value("episode_id")
        return Input(type="hidden", name="episode_id", value=episode_id)

    def form(self) -> Form:
        fields = [
            self.episode_id_key(),
            self.series_id_key(),
            self.tmdb_field("streaming.htmx.tmdb_fetch_episode"),
            self.ytdlp_url_field("streaming.htmx.ytdlp_fetch_episode"),
            self.title_field(),
            self.program_id_field(),
            self.description_field(),
            self.season_number_field(),
            self.episode_number_field(),
            self.duration_field(),
        ]

        return self.render_form(fields, post_endpoint="streaming.admin_crud.episodes_page")


# ============ MOVIE ============

class MovieForm(FormBase):
    def __init__(self, entry: Movie | None = None, movie_id: int | None = None):
        self.entry = entry
        self.movie_id = movie_id

    def movie_id_key(self):
        movie_id = self.movie_id or self._value("movie_id")
        return Input(type="hidden", name="movie_id", value=movie_id)

    def form(self) -> Form:
        return self.render_form(
            [
                self.movie_id_key(),
                self.tmdb_field("streaming.htmx.tmdb_fetch_movie"),
                self.ytdlp_url_field("streaming.htmx.ytdlp_fetch_movie"),
                self.title_field(),
                self.description_field(),
                self.release_field(),
                self.genre_select(),
                self.duration_field(),
            ],
            post_endpoint="streaming.admin_crud.movies_page"
        )

# ============ SCHEDULE ============

class ScheduleForm(FormBase):
    def __init__(self, entry=None, episode=None, movie=None):
        self.entry = entry
        self.episode = episode
        self.movie = movie

    def title_field(self):
        title = self._value("title")
        if not title:
            program = self.episode or self.movie
            title = program.title if program else ""

        return form_group(
            form_label("Title*:"),
            form_input(type="text", name="title", value=title)
        )

    def episode_id_key(self):
        episode_id = self._value("episode_id")
        if episode_id is None and self.episode:
            episode_id = self.episode.episode_id

        return Input(type="hidden", name="episode_id", value=episode_id if episode_id is not None else "")

    def movie_id_key(self):
        movie_id = self._value("movie_id")
        if movie_id is None and self.movie:
            movie_id = self.movie.movie_id

        return Input(type="hidden", name="movie_id", value=movie_id if movie_id is not None else "")

    def form(self) -> Form:
        fields = [
            self.title_field(),
            self.channel_select(),
            self.datetime_select(),
            self.end_time(),
            self.rerun_check(),
            self.episode_id_key(),
            self.movie_id_key(),
            self.schedule_id_key()
        ]

        return self.render_form(fields, post_endpoint="streaming.admin_crud.schedule_page")

# ============ SEASON ============

class SeasonForm(FormBase):
    def __init__(self, series_id: int | None = None):
        self.series_id = series_id
        self.entry = None

    def series_id_key(self):
        return Input(type="hidden", name="series_id", value=self.series_id)

    def form(self) -> Form:
        fields = [
            self.series_id_key(),
            self.source_url_field(),
            self.season_number_field(),
        ]

        return self.render_form(fields, post_endpoint="streaming.admin_crud.save_season")

class SeasonScheduleForm(FormBase):
    def __init__(self, series_id: int, entry=None):
        self.entry = entry
        self.series_id = series_id

    def series_id_key(self):
        return Input(type="hidden", name="series_id", value=self.series_id)

    def season_select(self):
        seasons = tv_db.get_seasons(self.series_id)
        return form_group(
            form_label("Sesong:"),
            form_select(
                *[Option(f"Sesong {s}", value=s) for s in seasons],
                name="season_number"
            )
        )

    def form(self) -> Form:
        fields = [
            self.series_id_key(),
            self.season_select(),
            self.channel_select(),
            self.datetime_select(),
            self.rerun_check(),
        ]

        return self.render_form(fields, post_endpoint="streaming.admin_crud.schedule_season_page")