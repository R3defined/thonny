# -*- coding: utf-8 -*-
 
"""
Classes used both by front-end and back-end
"""
import os.path
from typing import Optional, List

class Record:
    def __init__(self, **kw):
        self.__dict__.update(kw)
    
    def update(self, e, **kw):
        self.__dict__.update(e, **kw)
    
    def setdefault(self, **kw):
        "updates those fields that are not yet present (similar to dict.setdefault)"
        for key in kw:
            if not hasattr(self, key):
                setattr(self, key, kw[key])
    
    def get(self, key, default=None):
        return self.__dict__.get(key, default)
    
    def __getitem__(self, key):
        return self.__dict__[key]
    
    def __delitem__(self, key):
        self.__dict__.__delitem__(key)
    
    def __setitem__(self, key, value):
        self.__dict__[key] = value
    
    def __contains__(self, key):
        return key in self.__dict__
    
    def __repr__(self):
        keys = self.__dict__.keys()
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(self.__class__.__name__, ", ".join(items))
    
    def __str__(self):
        keys = sorted(self.__dict__.keys())
        items = ("{}={!r}".format(k, str(self.__dict__[k])) for k in keys)
        return "{}({})".format(self.__class__.__name__, ", ".join(items))
    
    def __eq__(self, other):
        if type(self) != type(other):
            return False
        
        if len(self.__dict__) != len(other.__dict__):
            return False 
        
        for key in self.__dict__:
            if not hasattr(other, key):
                return False
            self_value = getattr(self, key)
            other_value = getattr(other, key)
            
            if type(self_value) != type(other_value) or self_value != other_value:
                return False
        
        return True

    def __ne__(self, other):
        return not self.__eq__(other)
        
    def __hash__(self):
        return hash(repr(self))


class TextRange(Record):
    def __init__(self, lineno: int, col_offset: int, end_lineno: int, end_col_offset: int) -> None:
        self.lineno = lineno
        self.col_offset = col_offset
        self.end_lineno = end_lineno
        self.end_col_offset = end_col_offset
    
    def contains_smaller(self, other: "TextRange") -> bool:
        this_start = (self.lineno, self.col_offset)
        this_end = (self.end_lineno, self.end_col_offset)
        other_start = (other.lineno, other.col_offset)
        other_end = (other.end_lineno, other.end_col_offset)
        
        return (this_start < other_start and this_end > other_end
                or this_start == other_start and this_end > other_end
                or this_start < other_start and this_end == other_end)
    
    def contains_smaller_eq(self, other: "TextRange") -> bool:
        return self.contains_smaller(other) or self == other
    
    def not_smaller_in(self, other: "TextRange") -> bool:
        return not other.contains_smaller(self)

    def is_smaller_in(self, other: "TextRange") -> bool:
        return other.contains_smaller(self)
    
    def not_smaller_eq_in(self, other: "TextRange") -> bool:
        return not other.contains_smaller_eq(self)

    def is_smaller_eq_in(self, other: "TextRange") -> bool:
        return other.contains_smaller_eq(self)
    
    def get_start_index(self) -> str:
        return str(self.lineno) + "." + str(self.col_offset)
    
    def get_end_index(self) -> str:
        return str(self.end_lineno) + "." + str(self.end_col_offset)
    
    def __str__(self) -> str:
        return "TR(" + str(self.lineno) + "." + str(self.col_offset) + ", " \
                     + str(self.end_lineno) + "." + str(self.end_col_offset) + ")"
    
    
                 
class FrameInfo(Record):
    def __init__(self, 
                 id: int,  # @ReservedAssignment
                 code_name: str,
                 filename: str, 
                 focus:Optional[TextRange]=None, **kw) -> None:
        super().__init__(**kw)
        self.id = id
        self.code_name = code_name
        self.filename = filename
        self.focus = focus
    
    def get_description(self) -> str:
        return (
            "[" + str(self.id) + "] "
            + self.code_name + " in " + self.filename
            + ", focus=" + str(self.focus)
        )

class InputSubmission(Record):
    """For sending data to backend's stdin"""
    def __init__(self, data: str, **kw) -> None:
        super().__init__(**kw)
        self.data = data

class CommandToBackend(Record):
    """Command meant for the back-end"""
    
    def __init__(self, name: str, **kw) -> None:
        super().__init__(**kw)
        self.name = name

class ToplevelCommand(CommandToBackend):
    def __init__(self, name: str, argv: List[str]=[], **kw)->None:
        super().__init__(name, **kw)

class DebuggerCommand(CommandToBackend):
    pass

class InlineCommand(CommandToBackend):
    """
    Can be used both during debugging and in waiting_toplevel_command state
    (eg. for sending variable and heap info requests)
    """
    pass


class MessageFromBackend(Record):
    def __init__(self, **kw) -> None:
        self.event_type = type(self).__name__ # allow event_type to be overridden by kw
        super().__init__(**kw)

class ToplevelResponse(MessageFromBackend):
    pass

class DebuggerResponse(MessageFromBackend):
    pass

class BackendEvent(MessageFromBackend):
    def __init__(self, event_type: str, **kw) -> None:
        super().__init__(**kw)
        self.event_type = event_type

class InlineResponse(MessageFromBackend):
    def __init__(self, command_name: str, **kw) -> None:
        super().__init__(**kw)
        self.command_name = command_name
        self.event_type = self.command_name + "_response"
        
def serialize_message(msg: Record) -> str:
    # I want to transfer only ASCII chars because encodings are not reliable 
    # (eg. can't find a way to specify PYTHONIOENCODING for cx_freeze'd program) 
    return repr(msg).encode("UTF-7").decode("ASCII") 

def parse_message(msg_string: str) -> Record:
    # DataFrames may have nan 
    nan = float("nan")  # @UnusedVariable
    return eval(msg_string.encode("ASCII").decode("UTF-7"))

def actual_path(name: str) -> str:
    """In Windows return the path with the case it is stored in the filesystem"""
    assert os.path.isabs(name)
    
    if os.name == "nt":
        name = os.path.realpath(name)
        
        from ctypes import create_unicode_buffer, windll

        buf = create_unicode_buffer(512)
        windll.kernel32.GetShortPathNameW(name, buf, 512)  # @UndefinedVariable
        windll.kernel32.GetLongPathNameW(buf.value, buf, 512)  # @UndefinedVariable
        assert len(buf.value) >= 2
        
        result = buf.value
        assert isinstance(result, str) 
        
        if result[1] == ":":
            # ensure drive letter is capital
            return result[0].upper() + result[1:]
        else:
            return result
    else:
        return os.path.realpath(name)

def is_same_path(name1: str, name2: str) -> bool:
    return os.path.realpath(os.path.normcase(name1)) == os.path.realpath(os.path.normcase(name2))

def path_startswith(child_name: str, dir_name: str) -> bool:
    normchild = os.path.realpath(os.path.normcase(child_name))
    normdir = os.path.realpath(os.path.normcase(dir_name))
    return normdir == normchild or normchild.startswith(normdir.rstrip(os.path.sep) + os.path.sep)
    

class UserError(RuntimeError):
    """Errors of this class are meant to be presented without stacktrace"""
    pass

if __name__ == "__main__":
    print(repr(actual_path("c:\\users/aivar/DesKTOp")))
