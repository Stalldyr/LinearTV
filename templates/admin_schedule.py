from hypermedia import *

try:
    from tvcore.tvdatabase import TVDatabase
    from templates.buttons import button
except:
    from tvstreamer.tvcore.tvdatabase import TVDatabase
    from tvstreamer.templates.buttons import button
    
tv_db = TVDatabase()

def admin_schedule_body():
    return ElementList(
        H1("Admin"),
        Div(
            main_button(
                "Series",
                "/admin/partials/series/form-open"
            ),
            main_button(
                "Seasons",
                "/admin/partials/season/form-open"
            ),
            main_button(
                "Episodes",
                "/admin/partials/episodes/form-open"
            ),
            main_button(
                "Movies",
                "/admin/partials/movie/form-open"
            ),
            main_button(
                "Schedule",
                "/admin/partials/schedule/form-open",
            ),
            main_button(
                "Add series to schedule",
                "/admin/partials/schedule/new-form-open",
            ),
            main_button(
                "Add movie to schedule",
                "/admin/partials/schedule/new-form-open",
            ),
            main_button(
                "Channels",
                "/admin/partials/channel/form-open",
            ),
            class_="flex flex-col gap-2 p-2"
        ),

        Div(
            id="overlay",
            class_="fixed top-0 left-0 w-full h-full bg-[#00000080] z-999 hidden",
            _="on click add .hidden to me then hide #form-panel"
        ),

        Div(
            id="form-panel",
            class_="fixed top-2 left-50 translate-x-50 bg-alice-blue p-10 rounded-lg z-1000 overflow-auto box-border min-w-125 max-w-9/10"    
        )
    )

def main_button(name, hx_get, **kwargs) -> Button:
    return button(
        name,
        hx_get = hx_get,
        hx_target="#form-panel",
        hx_swap="innerHTML",
        _="on click remove .hidden from #overlay then show #form-panel",
        **kwargs
    )

def form_status(message) -> P:
    return P(
        message,
        class_= "p-2"
    )