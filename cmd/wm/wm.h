/*
 * (C)opyright MMIV-MMVI Anselm R. Garbe <garbeam at gmail dot com>
 * See LICENSE file for license details.
 */

#include <stdio.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

#include "ixp.h"
#include "blitz.h"

/* array indexes of EWMH window properties */
	                  /* TODO: set / react */
enum {
	NET_NUMBER_OF_DESKTOPS, /*  ✓      –  */
	NET_CURRENT_DESKTOP,    /*  ✓      ✓  */
	NET_WM_DESKTOP          /*  ✗      ✗  */
};

/* 8-bit qid.path.type */
enum {                          
    Droot,
	Ddef,
	Dtag,
	Darea,
	Dclient,
	Dkeys,
	Dbar,
    Dlabel,
	Fexpand,
    Fdata,                      /* data to display */
    Fcolors,
    Ffont,
    Fselcolors,
    Fnormcolors,
	Fkey,
	Fborder,
	Fsnap,
	Fbar,
	Fgeom,
	Fevent,
	Fctl,
	Fname,
	Fmode
};

#define NET_ATOM_COUNT         3

#define PROTO_DEL              1
#define DEF_BORDER             3
#define DEF_SNAP               20
#define DEF_PAGER_GAP          5

#define ROOT_MASK              SubstructureRedirectMask
#define CLIENT_MASK            (StructureNotifyMask | PropertyChangeMask)

typedef struct Area Area;
typedef struct Tag Tag;
typedef struct Client Client;

typedef enum { COL_EQUAL, COL_STACK, COL_MAX, COL_MODE_LAST } ColumnMode;

struct Area {
	unsigned short id;
    Client **client;
	Tag *tag;
	unsigned int clientsz;
	unsigned int sel;
	unsigned int nclient;
	ColumnMode mode;
	XRectangle rect;
};

struct Tag {
	unsigned short id;
	Area **area;
	unsigned int areasz;
	unsigned int narea;
	unsigned int sel;
	Tag *revert;
};

struct Client {
	unsigned short id;
	char name[256];
    int proto;
    unsigned int border;
    Bool destroyed;
	Area *area;
    Window win;
    Window trans;
    XRectangle rect;
    XSizeHints size;
	Client *revert;
	struct Frame {
		Window win;
    	XRectangle rect;
		XRectangle revert;
    	GC gc;
    	Cursor cursor;
	} frame;
};

typedef struct Key Key;
struct Key {
	unsigned short id;
    char name[128];
    unsigned long mod;
    KeyCode key;
    Key *next;
};

typedef struct {
	unsigned short id;
    char data[256];
	char colstr[24];
	Color color;
	XRectangle rect;
} Label;

/* default values */
typedef struct {
	char selcolor[24];
	char normcolor[24];
	char *font;
	Color sel;
	Color norm;
	unsigned int border;
	unsigned int snap;
} Default;

/* global variables */
Tag **tag;
unsigned int ntag;
unsigned int tagsz;
unsigned int sel;
Client **client;
unsigned int nclient;
unsigned int clientsz;
Key **key;
unsigned int keysz;
unsigned int nkey;
Label **label;
unsigned int nlabel;
unsigned int labelsz;
unsigned int iexpand;

Display *dpy;
IXPServer *ixps;
int screen;
Window root;
XRectangle rect;
XFontStruct *xfont;
GC gc_xor;
IXPServer srv;
Pixmap pmapbar;
Window winbar;
GC gcbar;
XRectangle brect;
Qid root_qid;

Default def;

Atom wm_state; /* TODO: Maybe replace with wm_atoms[WM_ATOM_COUNT]? */
Atom wm_change_state;
Atom wm_protocols;
Atom wm_delete;
Atom motif_wm_hints;
Atom net_atoms[NET_ATOM_COUNT];

Cursor normal_cursor;
Cursor resize_cursor;
Cursor move_cursor;
Cursor drag_cursor;
Cursor w_cursor;
Cursor e_cursor;
Cursor n_cursor;
Cursor s_cursor;
Cursor nw_cursor;
Cursor ne_cursor;
Cursor sw_cursor;
Cursor se_cursor;

unsigned int valid_mask, num_lock_mask;

/* area.c */
Area *alloc_area(Tag *t);
void destroy_area(Area *a);
int area2index(Area *a);
int aid2index(Tag *t, unsigned short id);
void update_area_geometry(Area *a);
void select_area(Area *a, char *arg);
void send_toarea(Area *to, Client *c);
void attach_toarea(Area *a, Client *c);
void detach_fromarea(Client *c);
void arrange_tag(Tag *t, Bool updategeometry);
void arrange_area(Area *a);
void resize_area(Client *c, XRectangle *r, XPoint *pt);
Area *new_area(Tag *t);
ColumnMode str2colmode(char *arg);
char *colmode2str(ColumnMode mode);

/* bar.c */
Label *new_label();
void detach_label(Label *l);
void draw_bar();
int lid2index(unsigned short id);
void update_bar_geometry();
unsigned int bar_height();

/* client.c */
Client *alloc_client(Window w, XWindowAttributes *wa);
void destroy_client(Client *c);
void configure_client(Client *c);
void handle_client_property(Client *c, XPropertyEvent *e);
void kill_client(Client *c);
void draw_client(Client *client);
void gravitate(Client *c, unsigned int tabh, unsigned int bw, int invert);
void unmap_client(Client *c);
void map_client(Client *c);
void reparent_client(Client *c, Window w, int x, int y);
void attach_client(Client *c);
void attach_totag(Tag *t, Client *c);
void detach_client(Client *c, Bool unmap);
Client *sel_client();
Client *sel_client_of_tag(Tag *t);
void focus_client(Client *c);
Client *win2clientframe(Window w);
void resize_client(Client *c, XRectangle *r, XPoint *pt, Bool ignore_xcall);
int cid2index(Area *a, unsigned short id);
int client2index(Client *c);
void select_client(Client *c, char *arg);
void sendtotag_client(Client *c, char *arg);
void sendtoarea_client(Client *c, char *arg);
void resize_all_clients();
void focus(Client *c);

/* event.c */
void init_x_event_handler();
void check_x_event(IXPConn *c);

/* fs.c */
unsigned long long mkqpath(unsigned char type, unsigned short pg,
						unsigned short area, unsigned short cl);
void write_event(char *event);
void new_ixp_conn(IXPConn *c);

/* kb.c */
void handle_key(Window w, unsigned long mod, KeyCode keycode);
void grab_key(Key *k);
void ungrab_key(Key *k);
Key * name2key(char *name);
int kid2index(unsigned short id);
Key *create_key(char *name);
void destroy_key(Key *k);
void init_lock_modifiers();

/* mouse.c */
void mouse_resize(Client *c, Align align);
void mouse_move(Client *c);
Cursor cursor_for_motion(Client *c, int x, int y);
Align cursor2align(Cursor cursor);
Align xy2align(XRectangle * rect, int x, int y);
void drop_move(Client *c, XRectangle *new, XPoint *pt);
void grab_mouse(Window w, unsigned long mod, unsigned int button);
void ungrab_mouse(Window w, unsigned long mod, unsigned int button);
char *warp_mouse(char *arg);

/* tag.c */
Tag *alloc_tag();
char *destroy_tag(Tag *t);
void focus_tag(Tag *t);
XRectangle *rectangles(unsigned int *num);
int pid2index(unsigned short id);
void select_tag(char *arg);
int tag2index(Tag *t);

/* wm.c */
void scan_wins();
Client *win2client(Window w);
int win_proto(Window w);
int win_state(Window w);
