import os
import sys
import traceback
from threading import Thread

import pygmi
from pygmi import *
from pygmi import event

# Note: This file loads ~/.wmii/wmiirc_local.py if it exists.
# Configuration should be placed in that file, and this file
# left unmodified, if possible. wmiirc_local should import
# wmiirc or any other modules it needs.
#
# Do *not* copy this file to wmiirc_local.py lest you want it
# executed twice.

# Tell that we are starting up (older wmiirc session will terminate)
client.awrite('/event', 'Start wmiirc')

# Cleanup from previous session
for name in wmii.rbuttons:
    Button('right', name).remove()


# Keys definitions
keys.defs = dict(
    mod='Mod1',
    left='h',
    down='j',
    up='k',
    right='l')


# Theme
background = '#333333'
floatbackground='#222222'

wmii['font'] = '-*-fixed-*-*-*-*-12-*-*-*-*-*-*-*'
wmii['normcolors'] = '#bbbbbb', '#222222', '#474747'
wmii['focuscolors'] = '#eeeeee', '#506070', '#708090'
wmii.cache['urgentcolors'] = '#eeeeee', '#bb6050', '#dd8070'
wmii['border'] = 1


# Behavior / rules
wmii['grabmod'] = keys.defs['mod']
wmii['colmode'] = 'default'

if Tag('sel').id == '1':
    # If fresh session, change the current colmode to default as well
    Tag('sel')['colmode'] = 'sel default'

terminal = 'wmiir', 'setsid', '@TERMINAL@'
pygmi.shell = os.environ.get('SHELL', 'sh')

wmii.colrules = (
    (ur'.*', '62+38'), # Golden Ratio
)

wmii.rules = (
    # Apps with system tray icons like to their main windows
    # Give them permission.
    (ur'^Pidgin:',       dict(allow='+activate')),

    # MPlayer and VLC don't float by default, but should.
    (ur'MPlayer|VLC',   dict(floating=True)),

    # ROX puts all of its windows in the same group, so they open
    # with the same tags.  Disable grouping for ROX Filer.
    (ur'^ROX-Filer:',   dict(group=0)),
)


# Misc functions
def setbackground(color='black'):
    bg_file = '%s/.wmii/background' % os.getenv('HOME')
    if os.path.isfile(bg_file):
        call('feh', '--bg-fill', bg_file)
    else:
        call('xsetroot', '-solid', color)

def unresponsive_client(client):
    msg = 'The following client is not responding. What would you like to do?'
    resp = call('wihack', '-transient', str(client.id),
                'xmessage', '-nearmouse', '-buttons', 'Kill,Wait', '-print',
                '%s\n  %s' % (msg, client.label))
    if resp == 'Kill':
        client.slay()

def clickmenu(choices, args):
    ClickMenu(choices=(k for k, v in choices),
            action=lambda choice: dict(choices).get(choice, lambda k: k)(*args)
             ).call()

def temp_tag():
    tag = Tag('sel').id
    client = Client.name_write(Client('sel').id)
    if tag == client:
        Client(client).tags = '-%s' % client
        tags.select(tags.LAST)
    else:
        Client(client).tags = '+%s' % client
        tags.select(client)


# Initialize tags
tags = Tags()


# Events
events.bind({
    ('Quit', Match('Start', 'wmiirc')): lambda *a: sys.exit(),
    'CreateTag':    tags.add,
    'DestroyTag':   tags.delete,
    'FocusTag':     tags.focus,
    'UnfocusTag':   tags.unfocus,
    'UrgentTag':    lambda args: tags.set_urgent(args.split()[1], True),
    'NotUrgentTag': lambda args: tags.set_urgent(args.split()[1], False),

    'AreaFocus':    lambda args: (args == '~' and
                                  (setbackground(floatbackground), True) or
                                  setbackground(background)),

    'Unresponsive': lambda args: Thread(target=unresponsive_client,
                                        args=(Client(args),)).start(),

    'ScreenChange': lambda args: wmii.ctl('wipescreens'),

    Match(('LeftBarClick', 'LeftBarDND'), 1): lambda e, b, tag: tags.select(tag),
    Match('LeftBarClick', 4): lambda *a: tags.select(tags.next(True)),
    Match('LeftBarClick', 5): lambda *a: tags.select(tags.next()),

    Match('LeftBarMouseDown', 3):   lambda e, n, tag: clickmenu((
            ('Delete',     lambda t: Tag(t).delete()),
        ), (tag,)),
    Match('ClientMouseDown', _, 3): lambda e, client, n: clickmenu((
            ('Delete',     lambda c: Client(c).kill()),
            ('Kill',       lambda c: Client(c).slay()),
            ('Fullscreen', lambda c: Client(c).set('Fullscreen', 'on')),
        ), (client,)),

    Match('ClientClick', _, 4): lambda e, c, n: Tag('sel').select('up'),
    Match('ClientClick', _, 5): lambda e, c, n: Tag('sel').select('down'),
})


# Actions
class Actions(event.Actions):
    def reload(self, args=''):
        call(sys.argv[0], background=True)
    def rehash(self, args=''):
        program_menu.choices = program_list(os.environ['PATH'].split(':'))
    def showkeys(self, args=''):
        message(keys.help)
    def quit(self, args=''):
        events.alive = False
        self.exit()
        wmii.ctl('quit')
    def eval_(self, args=''):
        exec args
    def exec_(self, args=''):
        wmii['exec'] = args
    def exit(self, args=''):
        client.awrite('/event', 'Quit')
    def sticky(self, args=''):
        Client('sel').tags = '/./'
actions = Actions()


# Menus
program_menu = Menu(histfile='%s/history.progs' % confpath[0], nhist=5000,
                    action=curry(call, 'wmiir', 'setsid',
                                 pygmi.shell, '-c', background=True))
action_menu = Menu(histfile='%s/history.actions' % confpath[0], nhist=500,
                   choices=lambda: actions._choices,
                   action=lambda args: actions._call(args))
tag_menu = Menu(histfile='%s/history.tags' % confpath[0], nhist=100,
                choices=lambda: sorted(tags.tags.keys()))


# Key bindings
keys.bind('main', (
    "Moving around",
    ('%(mod)s-%(left)s',  "Select the client to the left",
        lambda k: Tag('sel').select('left')),
    ('%(mod)s-%(right)s', "Select the client to the right",
        lambda k: Tag('sel').select('right')),
    ('%(mod)s-%(up)s',    "Select the client above",
        lambda k: Tag('sel').select('up')),
    ('%(mod)s-%(down)s',  "Select the client below",
        lambda k: Tag('sel').select('down')),

    ('%(mod)s-space',     "Toggle between floating and managed layers",
        lambda k: Tag('sel').select('toggle')),

    "Moving through stacks",
    ('%(mod)s-Control-%(up)s',   "Select the stack above",
        lambda k: Tag('sel').select('up', stack=True)),
    ('%(mod)s-Control-%(down)s', "Select the stack below",
        lambda k: Tag('sel').select('down', stack=True)),

    "Moving clients around",
    ('%(mod)s-Shift-%(left)s',  "Move selected client to the left",
        lambda k: Tag('sel').send(Client('sel'), 'left')),
    ('%(mod)s-Shift-%(right)s', "Move selected client to the right",
        lambda k: Tag('sel').send(Client('sel'), 'right')),
    ('%(mod)s-Shift-%(up)s',    "Move selected client up",
        lambda k: Tag('sel').send(Client('sel'), 'up')),
    ('%(mod)s-Shift-%(down)s',  "Move selected client down",
        lambda k: Tag('sel').send(Client('sel'), 'down')),

    ('%(mod)s-Shift-space',     "Toggle selected client between floating and managed layers",
        lambda k: Tag('sel').send(Client('sel'), 'toggle')),

    "Client actions",
    ('%(mod)s-f',       "Toggle selected client's fullsceen state",
        lambda k: Client('sel').set('Fullscreen', 'toggle')),
    ('%(mod)s-Shift-c', "Close client",
        lambda k: Client('sel').kill()),

    "Changing column modes",
    ('%(mod)s-d', "Set column to default mode",
        lambda k: setattr(Tag('sel').selcol, 'mode', 'default-max')),
    ('%(mod)s-s', "Set column to stack mode",
        lambda k: setattr(Tag('sel').selcol, 'mode', 'stack-max')),
    ('%(mod)s-m', "Set column to max mode",
        lambda k: setattr(Tag('sel').selcol, 'mode', 'stack+max')),

    "Running programs",
    ('%(mod)s-a',      "Open wmii actions menu",
        lambda k: action_menu()),
    ('%(mod)s-p',      "Open program menu",
        lambda k: program_menu()),

    ('%(mod)s-Return', "Launch a terminal",
        lambda k: call(*terminal, background=True)),

    "Tag actions",
    ('%(mod)s-t',       "Change to another tag",
        lambda k: tags.select(tag_menu())),
    ('%(mod)s-Shift-t', "Retag the selected client",
        lambda k: setattr(Client('sel'), 'tags', tag_menu())),
    ('%(mod)s-y', "Create a temporary tag for selected client",
        lambda k: temp_tag()),
    ('%(mod)s-u', "Select urgent tag",
        lambda k: tags.select_urgent()),

    ('%(mod)s-b', "Move to the view to the left",
        lambda k: tags.select(tags.next(True))),
    ('%(mod)s-n', "Move to the view to the right",
        lambda k: tags.select(tags.next())),
    ('%(mod)s-Shift-b', "Move to the view to the left, take along current client",
        lambda k: tags.select(tags.next(True), take_client=Client('sel'))),
    ('%(mod)s-Shift-n', "Move to the view to the right, take along current client",
        lambda k: tags.select(tags.next(), take_client=Client('sel'))),

    ('%(mod)s-i', "Move to the newer tag in the tag stack",
        lambda k: tags.select(tags.NEXT)),
    ('%(mod)s-o', "Move to the older tag in the tag stack",
        lambda k: tags.select(tags.PREV)),
    ('%(mod)s-Shift-i', "Move to the newer tag in the tag stack, take along current client",
        lambda k: tags.select(tags.NEXT, take_client=Client('sel'))),
    ('%(mod)s-Shift-o', "Move to the older tag in the tag stack, take along current client",
        lambda k: tags.select(tags.PREV, take_client=Client('sel'))),

))
def bind_num(i):
    keys.bind('main', (
        "Tag actions",
        ('%%(mod)s-%d' % i,       "Move to view '%d'" % i,
            lambda k: tags.select(str(i))),
        ('%%(mod)s-Shift-%d' % i, "Retag selected client with tag '%d'" % i,
            lambda k: setattr(Client('sel'), 'tags', i)),
    ))
map(bind_num, range(0, 10))

keys.bind('main', (
    "Changing modes",
    ('%(mod)s-Control-r', "Enter resize mode",
        lambda k: setattr(keys, 'mode', 'resize')),
    ('%(mod)s-Control-t', "Enter passthrough mode",
        lambda k: setattr(keys, 'mode', 'passthrough')),
));
keys.bind('passthrough', (
    "Changing modes",
    ('%(mod)s-Control-t', "Leave passthrough mode",
        lambda k: setattr(keys, 'mode', 'main')),
));

keys.bind('resize', (
    ('Escape', "Leave resize mode",
        lambda k: setattr(keys, 'mode', 'main')),
), import_={'main': ('%(mod)s-%(left)s', '%(mod)s-%(right)s',
                     '%(mod)s-%(up)s', '%(mod)s-%(down)s',
                     '%(mod)s-Space')})

def addresize(mod, desc, cmd, *args):
    keys.bind('resize', (
        (mod + '%(left)s',  "%s selected client to the left" % desc,
            lambda k: Tag('sel').ctl(cmd, 'sel sel', 'left',
                                     *args)),
        (mod + '%(right)s', "%s selected client to the right" % desc,
            lambda k: Tag('sel').ctl(cmd, 'sel sel', 'right',
                                     *args)),
        (mod + '%(up)s',    "%s selected client up" % desc,
            lambda k: Tag('sel').ctl(cmd, 'sel sel', 'up',
                                     *args)),
        (mod + '%(down)s',  "%s selected client down" % desc,
            lambda k: Tag('sel').ctl(cmd, 'sel sel', 'down',
                                     *args)),
    ));
addresize('',         'Grow', 'grow')
addresize('Control-', 'Shrink', 'grow', '-1')
addresize('Shift-',   'Nudge', 'nudge')


# Rehash path to programs
actions.rehash()


# Load local adaptations if any
wmiirc_local_exist = any(
    (os.path.isfile(os.path.join(f, 'wmiirc_local.py')) for f in confpath))

if wmiirc_local_exist:
    try:
        import wmiirc_local
    except Exception, e:
        traceback.print_exc(sys.stdout)


# Set background
setbackground(background)

# vim:se sts=4 sw=4 et:
