from enum import Enum
import pyautogui as pag
from time import sleep
from string import ascii_uppercase
pag_keyboard=['\t', '\n', '\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(',
')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7',
'8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`',
'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~',
'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace',
'browserback', 'browserfavorites', 'browserforward', 'browserhome',
'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear',
'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete',
'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10',
'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20',
'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja',
'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail',
'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack',
'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6',
'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn',
'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn',
'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator',
'shift', 'shiftleft', 'shiftright', 'sleep', 'space', 'stop', 'subtract', 'tab',
'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen',
'command', 'option', 'optionleft', 'optionright']
DEBUG=False
class NFA_Enum(Enum):
    START=0
    TERMINAL=1
    EPSILON=2
    FAILURE=3
    INTERNAL=4
    INTERNAL_NO_CAPTURE=5
    TERMINAL_NO_CAPTURE=6
class NFA:
    START=NFA_Enum.START
    TERMINAL=NFA_Enum.TERMINAL
    EPSILON=NFA_Enum.EPSILON
    FAILURE=NFA_Enum.FAILURE
    INTERNAL=NFA_Enum.INTERNAL
    def __init__(self,start):
        self.cur=start
        self.start=start
    def __call__(self,unit):
        self.cur=self.cur(unit)
        t=self.cur.state
        if t==NFA.TERMINAL:
            self.reset()
        return t
    def reset(self):
        self.cur=self.start
    @classmethod
    def from_expr(cls,expr):
        return cls(NFA_Node.from_expr(expr))
class NFA_funcs(NFA):
    @classmethod
    def from_expr(cls,expr):
        return cls(NFA_funcs_Node.from_expr(expr))
class NFA_Node:
    def __init__(self,state=NFA.START,transitions=None,metadata={'capture':True}):
        self.transitions=transitions if transitions is not None else {}
        self.state=state
        self.metadata=metadata
    def __call__(self,transition=None):
        if transition in self.transitions:
            if NFA.EPSILON in self.transitions[transition].transitions:
                return self.transitions[transition](NFA.EPSILON)
            return self.transitions[transition]
        if self.state==NFA.TERMINAL:
            return self
        if NFA.EPSILON in self.transitions:
            return self.transitions[NFA.EPSILON](transition)
        return NFA_Node(NFA.FAILURE)
    def add_edge(self,transition,node=None):
        if transition in self.transitions:
                raise ValueError(f"Transition {transition}->{node} already exists")
        if node is None:
            node=NFA_Node(NFA.TERMINAL)
        self.transitions[transition]=node
        if node.state == NFA.TERMINAL:
            node.state=NFA.INTERNAL
        return self
    def add_edges(self,other: 'NFA'):
        for transition,node in other.transitions.items():
            self.add_edge(transition,node)
    def add_self_loop(self, transition):
        self.transitions[transition] = self
        return self
    def __repr__(self) -> str:
        return f"{self.state=},{self.transitions=},{self.metadata=}"
    @classmethod
    def from_expr(cls,expr,convert_unit=lambda x:x):
        if DEBUG:
            print('from_expr',cls,expr,convert_unit)
        return cls.parse_expr(expr,convert_unit)[0]
        
    @classmethod
    def parse_expr(cls,expr,convert_unit):#converts expr to a nfa returns the start and end nodes

        #| for OR
        #? for optional
        #() for grouping
        # for concatenation
        #equal precedence for OR and concatenation
        #words for units - regex [a-zA-Z]+
        #DOES NOT WORK for expressions like (x y)|(x? z) instead do (x y|z)|z
        #set convert_unit when working with NFA_funcs and convert names to functions
        escape=False
        stack=[cls(NFA.START)]
        operator = ' '
        i=0
        az="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        last_optional=False
        while i<len(expr):
            sub_start,sub_end=None,None
            match expr[i],escape:    
                case '\\',False:
                    escape=True
                case '(',False:#could optimize by saving location of internal pairs
                    open_paren=1
                    sub_expr_len=0
                    while open_paren>0:
                        i+=1
                        sub_expr_len+=1
                        match expr[i],escape:
                            case '(',False:
                                open_paren+=1
                            case ')',False:
                                open_paren-=1
                            case '\\',False:
                                escape=True
                            case _:
                                escape=False#escape is consumed regardless of the character following
                    sub_start,sub_end=cls.parse_expr(expr[i-sub_expr_len+1:i],convert_unit)         
                case s,False if s in " |":
                    operator=s
                case '?',False:
                    last_optional=True
                case ';',False:#don't capture
                    raise NotImplementedError
                    
                case _:
                    unit=""
                    while i<len(expr):
                        match expr[i],escape:
                            case '\\',False:
                                escape=True
                            case s,False if s in r"()| ?":
                                break
                            case _:
                                unit+=expr[i]
                                escape=False
                        i+=1
                    sub_end=cls(NFA.INTERNAL)
                    sub_start=cls(NFA.INTERNAL,transitions={convert_unit(unit):sub_end})
                    i-=1
                    escape=False

            if sub_start is not None:
                if operator == ' ':
                    stack[-1].add_edges(sub_start)#instead of an epsilon transition
                    stack.append(sub_end)
                    if last_optional:
                        stack[-3].add_edges(sub_start)
                        last_optional=False
                elif operator == '|':
                    stack[-2].add_edges(sub_start)
                    sub_end.add_edge(NFA.EPSILON,stack[-1])
                    #treat x?|y as (x|y)?
            i+=1
        stack[-1].state=NFA.TERMINAL
        if last_optional:
            stack[-2].state=NFA.TERMINAL
        return stack[0],stack[-1]
class NFA_funcs_Node(NFA_Node):
    #the more general the case the later it should be in the list
    #NFA_funcs.from_expr(r"lambda\ x:x>5")
    EPSILON_FUNCTION=lambda unit:NFA.EPSILON#equivalent to using NFA.EPSILON when using __call__
    def __call__(self,unit):
        for transition,node in self.transitions.items():
            if transition(unit):
                if NFA.EPSILON in node.transitions:
                    return self.transitions[NFA.EPSILON]
                return node
        if self.state==NFA.TERMINAL:
            return self
        if NFA.EPSILON in self.transitions:
            return self.transitions[NFA.EPSILON](transition)
        return NFA_funcs_Node(NFA.FAILURE)
    @classmethod
    def from_expr(cls,expr,convert_unit=eval):#by default will try to evaluate names as functions
        return super().parse_expr(expr,convert_unit)[0]
    #NFA_funcs(NFA.START,{bool: NFA_funcs(NFA.INTERNAL,{lambda x:x>5:NFA(NFA.TERMINAL)})})(True)(6)
class NFA_funcs_converters:
    @staticmethod
    def type_check(t:str):
        return lambda x: isinstance(x,eval(t))
    @staticmethod
    def in_check(collection):
        return lambda x: x in collection#or just use collection.__contains__ if the .__contains__ method is defined and does not change
    @staticmethod
    def equal_check(val):
        return lambda x: x==val   

"""shift quote comma shift quote period J O I N shift nine left bracket F shift
quote shift backslash shift left bracket I shift plus shift right bracket shift backslash shift quote"""
function_numbers = {
    'one':'1',
    'two':'2',
    'three':'3',
    'four':'4',
    'five':'5',
    'six':'6',
    'seven':'7',
    'eight':'8',
    'nine':'9',
    'ten':'10',
    'eleven':'11',
    'twelve':'12',
}
# Define patterns for each character
patterns = {
  '`': 'backtick|(grave accent)',
 '[': 'opening (square)? bracket',
 ']': 'closing (square)? bracket',
 '\\': 'backslash',
 ';': 'semicolon',
 "'": '(single? quote)|apostrophe',
 ',': 'comma',
 ' ': 'space',
 '.': 'period|dot',
 '/': 'forward slash',
 '=': 'equals|equal sign',
 '-': 'dash|minus|hyphen',
 }|{
   '~':'tilde',
    '!':'exclamation mark',
    '@':'at sign',
    '#':'hashtag|pound sign',
    '$':'dollar sign',
    '%':'percent sign',
    '^':'caret',
    '&':'ampersand',
    '*':'asterisk',
    '(':'opening parenthesis',
    ')':'closing parenthesis',
    '_':'underscore',
    '+':'plus',
    '{':'opening (curly bracket)|brace',
    '}':'closing (curly bracket)|brace',
    '|':'pipe|(vertical bar)',
    ':':'colon',
    '"': 'double quote',
     '<': 'opening angle bracket',
   '>': 'closing angle bracket',
     '<': 'opening angle bracket',
 '>': 'closing angle bracket',
 }|{
   'shift':'shift',
    'ctrl':'control',
    'alt':'alt',
 }
pattern_nfas = {
    key:NFA.from_expr(pattern) for key,pattern in patterns.items()
}

state_commands = ['hold','release','function','repeat']
holds = ['shift','ctrl','alt' ]
uppers=list(ascii_uppercase)
pag_string = ['enter','escape','backspace','delete','del','up','down','left','right']
class Converter:
    def __init__(self,nfas=pattern_nfas,additional_allowed_units=None):
        self.nfas=nfas
        if additional_allowed_units is None:
            additional_allowed_units = []
        self.additional_allowed_units = additional_allowed_units
        self.reset()
    def reset(self):
        for nfa in self.nfas.values():
            nfa.reset()
    def __call__(self, unit):
        flag=True
        for key, nfa in self.nfas.items():
           match nfa(unit):
               case NFA.TERMINAL:
                   return key
               case NFA.INTERNAL:
                   flag=False
        if flag:
            self.reset()
            if unit in uppers + state_commands + pag_string + self.additional_allowed_units:
                return unit.lower()
            if unit in function_numbers:
                return function_numbers[unit]
            if unit[0]=='f' and unit[1:].isdigit():
                return unit
        return None
from typing import Any
from functools import partial
def apply_to_dict_keys(f,d,modify_key=True):
    if modify_key:
        return {f(k):v for k,v in d.items()}
    for k in d:
        f(k)
class Commmand:
    def __init__(self,function,nfa,ignore_None=False):#functions should never return NFA.FAILURE
        self.nfa=nfa
        self.function=function
        self.ignore_None=ignore_None
        self.reset()
    @classmethod
    def _constructed_call(cls,function,nfa,ignore_None):
        return cls(function,nfa,ignore_None).__call__
    @classmethod
    def dec(cls,nfa,ignore_None=False):
        return partial(cls._constructed_call,nfa=nfa,ignore_None=ignore_None)
    def reset(self):
        self.args=[]
        self.nfa.reset()
class PrefixCommand(Commmand):
    def __call__(self, unit):
        if unit is None and self.ignore_None:
            return self
        self.args.append(unit)
        match self.nfa(unit):
            case NFA.TERMINAL:
                t=self.function(*self.args)
                self.reset()
                return t
            case NFA.FAILURE:
                self.reset()
                return NFA.FAILURE
        #else self.nfa.state == NFA.INTERNAL
        return self
class PostfixCommand(Commmand):
    #identical to Prefix command but with reversed args and nfa
    def __call__(self, unit):
        if unit is None and self.ignore_None:
            return self
        self.args.append(unit)
        match self.nfa(unit):
            case NFA.TERMINAL:
                t=self.function(*self.args[::-1])
                self.reset()
                return t
            case NFA.FAILURE:
                self.reset()
                return NFA.FAILURE
        #else self.nfa.state == NFA.INTERNAL
        return self# for chaining
    def call_on_stack(self,stack):
        i=-1
        args=[]
        while i>=-len(stack):
            args.append(stack[i])
            match self.nfa(stack[i]):
                case NFA.FAILURE:
                    self.reset()
                    return NFA.FAILURE
                case NFA.TERMINAL:
                    self.reset()
                    return self.function(*args)
        self.reset()
        return NFA.FAILURE          
class InfixCommand(PostfixCommand):
    def __init__(self, function, pre_nfa,post_nfa, ignore_None_pre=False,ignore_None_post=False,differentiate_args=False):
        self.function=function
        if not differentiate_args:
            self.function = lambda pre,post:function(*pre,*post)
        self.ignore_None_pre=ignore_None_pre
        self.ignore_None_post=ignore_None_post
        self.pre_nfa=pre_nfa
        self.post_nfa=post_nfa
        self.reset()
    def reset(self):
        self.pre_nfa.reset()
        self.post_nfa.reset()
        self.pre_args=[]
        self.post_args=[]
        self.mode="pre"
    def call_on_stack(self,stack):
        i=-1
        while i>=-len(stack):
            if self.mode == "pre":
                self.pre_args.append(stack[i])
            else:
                self.post_args.append(stack[i])
            match self.nfa(stack[i]),self.mode:
                case NFA.FAILURE,_:
                    self.reset()
                    return NFA.FAILURE
                case NFA.TERMINAL,"post":
                    t= self.function(*self.pre_args[::-1],*self.post_args)
                    self.reset()
                    return t
                case NFA.TERMINAL,"pre":
                    self.mode="post"
                    return self
        if self.mode == "pre":
            return NFA.FAILURE
        else:
            return self
                    
            
        return NFA.FAILURE
    def __call__(self,unit):
        if self.mode == "pre":
            if unit is None and self.ignore_None_pre:
                return self
            self.pre_args.append(unit)
            self.pre_nfa = self.pre_nfa(unit)
            if self.pre_nfa.state == NFA.TERMINAL:
                self.mode="post"
            elif self.pre_nfa.state == NFA.FAILURE:
                self.reset()
                return NFA.FAILURE
        else:
            if unit is None and self.ignore_None_post:
                return self
            self.post_args.append(unit)
            self.post_nfa = self.post_nfa(unit)
            if self.post_nfa.state == NFA.TERMINAL:
                t= self.function(self.pre_args,self.post_args)
                self.reset()
                return t
            elif self.post_nfa.state == NFA.FAILURE:
                self.reset()
                return NFA.FAILURE
        return self
state_commands = ['hold','release','function','repeat']
holds = ['shift','ctrl','alt' ]
uppers=list(ascii_uppercase)
other_string = ['enter','escape','backspace','delete','del','up','down','left','right']
#TODO
def lang_to_int(s:str):
    raise NotImplementedError
#TODO
from PIL import Image
class OutputTranscriber:
    def hold(self,  unit):
        pag.keyDown(unit)
        if DEBUG:
            print("key down",unit)  
    def release(self,unit):
        pag.keyUp(unit)
        if DEBUG: 
            print("key up",unit)
        if unit in self.queued:
                self.queued=[x for x in self.queued if x!=unit]
    def repeat(self,amount):#repeats last unit NOT last action
        amount=lang_to_int(amount)#need to convert natural language to int
        unit=self.unit_stack[-1]
        for _ in len(range(amount)):
            self(unit)
    def fn(self,unit):
        self(f'f{unit}')
    def click(self):#Don't need to indicate as command since it takesa no args
        pag.click()
    def right_click(self):
        pag.rightClick()
    def move_to_img(self,img_name):
        #need some handling for getting image name
        raise NotImplementedError
        #zoom factor is part of the vscode state and needs to be inputted before
        image=Image(img_name)
        image = image.resize((int(image.width  * zoom_factor), int(image.height * zoom_factor)))
        # Locate the image on the screen
        try:
            image_location = pag.locateOnScreen(image,confidence=.75,grayscale=True)
            #so that icons that have numbers appear over them show up
            x, y = pag.center(image_location)
            pag.moveTo(x, y)
        except pag.ImageNotFoundException:
            print("Image not found")      
    def unqueue_last(self,unit):
        self.queued=[x for x in self.queued if x!=unit]
        print("unqueue",unit)
    def quit(self):
        raise SystemExit
    def __init__(self):
        self.convert=Converter(additional_allowed_units=["unqueue","last"])
        self.hold = PrefixCommand(self.hold,NFA.from_expr(r"shift|ctrl|alt"))#could support others 
        self.release = PrefixCommand(self.release,NFA.from_expr(r"shift|ctrl|alt"))
        self.fn = PrefixCommand(self.fn,NFA.from_expr(r"|".join(str(i) for i in range(1,13))))
        self.unqueue_last = PostfixCommand(self.unqueue_last,NFA.from_expr(r"shift|ctrl|alt"))
        self.special_commands = apply_to_dict_keys(NFA.from_expr,{'quit':r"quit"})
        self.nullary_commands = apply_to_dict_keys(NFA.from_expr,{'click':self.click,
                        'shift':lambda:self.queued.append('shift'),
                        'ctrl':lambda:self.queued.append('ctrl'),
                        'alt':lambda:self.queued.append('alt')})
        self.prefix_commands = apply_to_dict_keys(NFA.from_expr,{'hold':self.hold,
                        'release':self.release,
                        'function':self.fn})
        self.postfix_commands = apply_to_dict_keys(NFA.from_expr,{"unqueue last":self.unqueue_last})
        self.infix_commands = apply_to_dict_keys(NFA.from_expr,{})
        self.reset()
    def reset(self):
        self.active_command=None
        self.unit_stack = []
        self.queued=[]  
        for nfa in self.special_commands:
            nfa.reset()
        for nfa in self.nullary_commands:
            nfa.reset()
        for nfa in self.prefix_commands:
            nfa.reset()
        for nfa in self.postfix_commands:
            nfa.reset()
        for nfa in self.infix_commands:
            nfa.reset()   
    def __call__(self,raw_unit):
        if DEBUG:
            print('output_transcription_unit',raw_unit)
        unit=self.convert(raw_unit)
        flag=False
        if unit is None:
            return None
        if self.active_command is not None:#must be a prefix or infix command
            match self.active_command(unit):
                case NFA.FAILURE:
                    self.reset()
                    return None
                case self.active_command:
                    flag=True
                case y:
                    return y
        for nfa, cmd in self.special_commands.items():
            match nfa(unit):
                case NFA.TERMINAL:
                    self.reset()
                    return cmd()        
                case NFA.INTERNAL:
                    flag=True
        for nfa, cmd in self.nullary_commands.items():
            match nfa(unit):
                case NFA.TERMINAL:
                    self.reset()
                    return cmd()      
        for nfa, cmd in self.prefix_commands.items():
            match nfa(unit):
                case NFA.TERMINAL:
                    self.active_command = cmd
                    return None
                case NFA.INTERNAL:
                    flag=True
        for nfa, cmd in self.postfix_commands.items():
            match nfa(unit):
                case NFA.TERMINAL:
                    return cmd.call_on_stack(self.unit_stack)
                case NFA.INTERNAL:
                    flag=True   
        for nfa, cmd in self.infix_commands.items():
            match nfa(unit):
                case NFA.TERMINAL:
                    if cmd.call_on_stack(self.unit_stack) == cmd: 
                        self.active_command = cmd
                    return None
                case NFA.INTERNAL:
                    flag=True
            self.reset()
        if not flag:
            self.unit_stack.append(unit)#functions consume units
            self.reset()
            if unit in pag_keyboard:
                pag.hotkey(*self.queued,unit)
                queued=[]
                print(*self.queued,unit)