from hypermedia import Button

SIZE = {
    "default": "px-[24px] py-[12px] text-[16px] max-w-36",
    "mini":    "px-[12px]  py-[6px] text-[8px]",
    "form":    "px-[15px]  py-[8px] text-[12px] ml-[2px]",
}

COLOR = {
    "cyan":  "bg-cyan-dark  text-cyan-pale",
    "cyan2": "bg-cyan-dark-2 text-white",
    "grey":  "bg-gray-200   text-black",
}

BASE = "cursor-pointer rounded-xl"

def button(name, color="cyan", size="default", type="button", **kwargs):
    cls = f"{BASE} {SIZE[size]} {COLOR[color]}"
    return Button(name, type=type, class_=cls, **kwargs)