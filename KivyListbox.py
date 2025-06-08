from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.properties import BooleanProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior

Builder.load_string("""
<SelectableLabel>:
    # Draw a background to indicate selection
    canvas.before:
        Color:
            rgba: (0.4, 1, 1, 1) if self.selected else (1, 1, 1, 1)
        Rectangle:
            pos: self.pos
            size: self.size
<Listbox>:
    viewclass: 'SelectableLabel'
    SelectableRecycleBoxLayout:
        default_size: None, dp(28.5)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
        multiselect: False
        touch_multiselect: False
""")


class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    """" Adds selection and focus behaviour to the view. """


class SelectableLabel(RecycleDataViewBehavior, Label):
    """ Add selection support to the Label """
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    font_size = 12
    color = (0, 0, 0, 1)

    def refresh_view_attrs(self, listbox, index, data):
        """ Catch and handle the view changes """
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(
            listbox, index, data)

    def on_touch_down(self, touch):
        """ Add selection on touch down """
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, listbox, index, is_selected):
        """ Respond to the selection of items in the view. """
        self.selected = is_selected
        if is_selected:
            if listbox.mainwid.delbutton.ishidden and listbox.data[index].get("text") != " ":
                listbox.usrselection = listbox.data[index].get("text")
                listbox.mainwid.delbutton.hidden(False)
        else:
            if not listbox.mainwid.delbutton.ishidden or listbox.data[index].get("text") == " ":
                listbox.usrselection = ""
                listbox.mainwid.delbutton.hidden(True)


class Listbox(RecycleView):
    def __init__(self, mainwid, data, **kwargs):
        super(Listbox, self).__init__(**kwargs)
        self.mainwid = mainwid
        self.usrselection = ""

        dt = [0, 1, 2, 3, 4, 5, 6]
        if len(data) < 7:
            for i in dt:
                if i < len(data):
                    dt[i] = data[i]
                else:
                    dt[i] = " "
        else:
            dt = data

        self.data = [{'text': str(x)} for x in dt]
