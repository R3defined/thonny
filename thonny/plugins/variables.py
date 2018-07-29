# -*- coding: utf-8 -*-

from tkinter import ttk

from thonny.memory import VariablesFrame
from thonny import get_workbench, get_runner
from thonny.common import InlineCommand
from thonny.ui_utils import create_string_var

class GlobalsView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        
        get_workbench().set_default("view.globals_module_selector", False)
        
        self._module_name_variable = create_string_var("__main__",
            modification_listener=self._request_globals)
        self.module_name_combo = ttk.Combobox(self,
                                        exportselection=False,
                                        textvariable=self._module_name_variable,
                                        state='readonly',
                                        height=20,
                                        values=[])
        
        if (get_workbench().get_option("view.globals_module_selector")
            and get_workbench().get_mode() != "simple"
            or self._module_name_variable.get() != "__main__"):
            self.module_name_combo.grid(row=0, column=0, sticky="nsew")
        
        self.variables_frame = VariablesFrame(self)
        self.variables_frame.grid(row=1, column=0, sticky="nsew")
        
        self.error_label = ttk.Label(self, text="Error", anchor="center", wraplength="5cm")
        
        ttk.Style().configure("Centered.TButton", justify="center")
        self.home_button = ttk.Button(self.variables_frame.tree, style="Centered.TButton", 
                                      text="Back to\ncurrent frame",
                                      width=15)
        self.home_button.place(relx=1, x=-5, y=5, anchor="ne")
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        get_workbench().bind("get_globals_response", self._handle_globals_event, True)
        get_workbench().bind("get_frame_info_response", self._handle_frame_info_event, True)
        get_workbench().bind("BackendRestart", self._backend_restart, True)
        get_workbench().bind("DebuggerResponse", self._handle_progress, True)
        get_workbench().bind("ToplevelResponse", self._handle_progress, True)
        get_workbench().bind("InputRequest", self._handle_progress, True)
    
    def before_show(self):
        self._request_globals()
    
    def _backend_restart(self, event):
        self.variables_frame._clear_tree()

    def _handle_frame_info_event(self, frame_info):
        #print("FRAI", event)
        if frame_info.get("error"):
            self.variables_frame.update_variables(None)
            # TODO: show error
        else:
            self.variables_frame.update_variables([
                ("LOCALS", frame_info["locals"]),
                ("GLOBALS", frame_info["globals"])
            ])
        
        name = frame_info.get("name", "") 
        if name and name != "<module>":
            view_caption = "Variables (%s)" % name
        else:
            view_caption = "Variables"
            
        self.home_widget.master.tab(self.home_widget, text=view_caption)
        
    def _handle_globals_event(self, event):
        # TODO: handle other modules as well
        error = getattr(event, "error", None)
        if error:
            self.error_label.configure(text=error)
            if self.variables_frame.winfo_ismapped():
                self.variables_frame.grid_remove()
            if not self.error_label.winfo_ismapped():
                self.error_label.grid(row=1, column=0, sticky="nsew")
        else:
            self._update_modules_list(event)
            self.variables_frame.update_variables(event.globals)
            if self.error_label.winfo_ismapped():
                self.error_label.grid_remove()
            if not self.variables_frame.winfo_ismapped():
                self.variables_frame.grid(row=1, column=0, sticky="nsew")
    
    def _handle_progress(self, event=None):
        self._update_modules_list(event)
        self._request_globals()
    
    def _request_globals(self, event=None):
        if get_runner() is None:
            return
        
        get_runner().send_command(InlineCommand("get_globals", 
                                                module_name=self._module_name_variable.get()))
    
    def _update_modules_list(self, event):
        if not hasattr(event, "loaded_modules"):
            return
        else:
            self.module_name_combo.configure(values=sorted(event.loaded_modules))
    

def load_plugin() -> None:
    get_workbench().add_view(GlobalsView, "Variables", "e", default_position_key="AAA")