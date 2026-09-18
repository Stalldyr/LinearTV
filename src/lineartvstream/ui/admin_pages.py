from hypermedia import *
from flask import url_for

def channels_body(channels):
    return Div(
        H1("Channels"),
        Button("New channel", hx_get=f"/admin/partials/channel/form", hx_target="#form_panel"),
        Div(
            channels_table(channels),
            Hr(class_="solid"),
            Div(
                id="form_panel"
            )
        )
    )

def channels_table(channels):
    return Table(
        Tr(Th("Channel ID"), Th("Name"), Th("")),
        *[
            Tr(
                Td(c.channel_id),
                Td(c.display_name),
                Td(A("Edit", hx_get=f"/admin/partials/channel/form?channel_id={c.id}", hx_target="#form_panel", href="")),
            )   
            for c in channels
        ]
    )

def genres_body(genres):
    return Div(
        H1("Genres"),
        Button("New genre", hx_get=f"/admin/partials/genres/form", hx_target="#form_panel"),
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
                Td(A("Edit", hx_get=f"/admin/partials/genres/form?genre_id={g.id}", hx_target="#form_panel", href="")),
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
                Td(A("Edit", hx_get=f"/admin/partials/series/form?series_id={s.series_id}", hx_target="#form_panel", href="")),
                Td(A("Episodes", href=f"/admin/episodes?series_id={s.series_id}")),
                Td(A("New Episode", hx_get=f"/admin/partials/episodes/form?series_id={s.series_id}", hx_target="#form_panel", href="")),
                Td(A("Add season", hx_get=f"/admin/partials/season/form?series_id={s.series_id}", hx_target="#form_panel", href="")),
                Td(A("Add season to schedule", hx_get=f"/admin/partials/season-schedule/form?series_id={s.series_id}", hx_target="#form_panel", href=""))
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

def form_status(message):
    return Div(P(message), id="form-status")


def season_schedule_results(results: list[dict]):
    return Div(
        H3("Results"),
        Table(
            Tr(Th("Episode"), Th("Tidspunkt"), Th("Status")),
            *[
                Tr(
                    Td(r["title"]),
                    Td(r["start"].strftime("%d.%m.%Y %H:%M")),
                    Td("Lagt til" if r["status"] == "scheduled" else "Konflikt")
                )
                for r in results
            ]
        ),
        id="form-status"
    )