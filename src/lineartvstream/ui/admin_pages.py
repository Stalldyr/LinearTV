from hypermedia import *
from flask import url_for

def channels_body(channels):
    return Div(
        H1("Channels"),
        channels_table(channels),

    )

def channels_table(channels):
    return Table(
        Tr(Th("Channel ID"), Th("Name"), Th("")),
        *[
            Tr(
                Td(c.channel_id),
                Td(c.display_name),
                Td(A("Edit", href=f"/admin/channels?edit={c.channel_id}")),
            )
            for c in channels
        ]
    )

def genres_body(genres):
    return Div(
        H1("Genres"),
        Div(
            genres_table(genres),
            Hr(class_="solid"),
            Div(
                id="form_panel"
            )
        )
    )

def genres_table(genres):
    return Table(
        Tr(Th("genre ID"), Th("Genre name"), Th("")),
        *[
            Tr(
                Td(g.name),
                Td(g.display_name),
                Td(A("Edit", href=f"/admin/genres?edit={g.name}")),
            )
            for g in genres
        ]
    )



def series_body(series):
    return Div(
        H1("Series"),
        Button("New series", hx_get=f"/admin/partials/series/form", hx_target="#form_panel"),
        Div(
            series_table(series),
            Hr(class_="solid"),
            Div(
                id="form_panel"
            )
        )
    )

def series_table(all_series):
    return Table(
        Tr(Th("Title"), Th(""), Th("")),
        *[
            Tr(
                Td(s.title),
                Td(A("Edit", hx_get=f"/admin/partials/series/form?series_id={s.series_id}", hx_target="#form_panel", href="")), #   href=f"/admin/series?series_id={s.series_id}")),
                Td(A("Episodes", href=f"/admin/episodes?series_id={s.series_id}")),
                Td(A("New Episode", href=f"/admin/episodes?series_id={s.series_id}"))
            )
            for s in all_series
        ]
    )




def movies_body(movies):
    return Div(
        H1("Movies"),
        Button("New movie", hx_get=f"/admin/partials/movies/form", hx_target="#form_panel"),
        Div(
            movies_table(movies),
            Hr(class_="solid"),
            Div(
                id="form_panel"
            )
        )
    )


def movies_table(movies):
    return Table(
        Tr(Th("Title"), Th(""), Th("")),
        *[
            Tr(
                Td(m.title),
                Td(A("Edit", hx_get=f"/admin/partials/movies/form?movie_id={m.movie_id}", hx_target="#form_panel", href="")),
                Td(A("Add to schedule", href=f"/admin/schedule?movie_id={m.movie_id}")),
            )
            for m in movies
        ]
    )



def episodes_body(episodes):
    return Div(
        H1("Episodes"),
        Div(
            episodes_table(episodes),
            Hr(class_="solid"),
            Div(
                id="form_panel"
            )
        )
    )

def episodes_table(episodes):
    return Table(
        Tr(Th("Ep."), Th("Title"), Th("")),
        *[
            Tr(
                Td(e.episode_number),
                Td(e.title),
                Td(A("Edit", hx_get=f"/admin/partials/episodes/form?episode_id={e.episode_id}", hx_target="#form_panel", href="")),
                Td(A("Add to schedule", href=f"/admin/schedule?episode_id={e.episode_id}")),
            )
            for e in episodes
        ]
    )


def schedule_body(schedule):
    return Div(
        H1(f"Schedule"),
        Div(
            schedule_table(schedule),
            Hr(class_="solid"),
            Div(
                id="form_panel"
            )
        )
    )


def schedule_table(schedule):
    return Table(
        Tr(Th("Start"), Th("Title"), Th("")),
        *[
            Tr(
                Td(s.start.isoformat()),
                Td(s.title),
                Td(A("Edit", hx_get=f"/admin/partials/schedule/form?schedule_id={s.schedule_id}", hx_target="#form_panel", href="")),
            )
            for s in schedule
        ]
    )


def admin_panel():
    return ElementList(
        H1("TVStreamer Test Panel"),
        Ul(
            Li(
                A(
                    "TV Stream",
                    href=url_for('streaming.tvstream')
                )
            ),
            Li(
                A(
                    "Prepare",
                )
            )
        )
    )
