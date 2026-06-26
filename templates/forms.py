from hypermedia import Div, Label, Select, Input, TextArea

def form_group(*args, **kwargs):
    return Div(*args, **kwargs, class_="mx-2.5")

def form_label(name, **kwargs):
    return Label(name, **kwargs, class_="block mb-1.25 font-bold")

def form_select(*args, **kwargs):
    return Select(*args, **kwargs, class_="p-1.25 rounded-[3px] bg-white w-full")

def form_input(*args, **kwargs):
    return Input(*args, **kwargs, class_="p-1.25 rounded-[3px] bg-white flex-1 min-w-0")

def form_input_with_button(input_el, button_el):
    return Div(input_el, button_el, class_="flex items-center gap-2 w-full")

def form_text(*args, **kwargs):
    return TextArea(*args, **kwargs, class_="p-1.25 rounded-[3px] bg-white")

def form_column(*args, **kwargs) -> Div:
    return Div(*args, **kwargs, class_="float-left w-1/2 p-2.5")
    
