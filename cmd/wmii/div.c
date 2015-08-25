/* Copyright ©2006-2010 Kris Maglione <maglione.k at Gmail>
 * See LICENSE file for license details.
 */
#include "dat.h"
#include "fns.h"

static Handlers	handlers;

static Divide*
getdiv(Divide ***dp) {
	WinAttr wa;
	Divide *d;

	if(**dp)
		d = **dp;
	else {
		d = emallocz(sizeof *d);

		wa.override_redirect = true;
		wa.cursor = cursor[CurDHArrow];
		wa.event_mask =
			  EnterWindowMask
			| ButtonPressMask
			| ButtonReleaseMask;
		d->w = createwindow(&scr.root, Rect(0, 0, 1, 1), 0, InputOnly, &wa,
			  CWOverrideRedirect
			| CWEventMask
			| CWCursor);
		d->w->aux = d;
		sethandler(d->w, &handlers);
		**dp = d;
	}
	*dp = &d->next;
	return d;
}

void
div_set(Divide *d, int x) {
	Rectangle r;
	int scrn;

	scrn = d->left ? d->left->screen : d->right->screen;

	d->x = x;
	if(x == selview->r[scrn].min.x || x == selview->r[scrn].max.x)
		return;

	r = Rect(x-1, selview->r[scrn].min.y, x+1, selview->r[scrn].max.y);

	moveresizewin(d->w, r);
	mapraisewin(d->w);
}

void
div_update_all(void) {
	Divide **dp, *d;
	Area *a, *ap;
	View *v;
	int s;

	v = selview;
	dp = &divs;
	ap = nil;

	for(d = *dp; d; d = d->next) {
		/* Force unmap */
		d->w->unmapped = 0;
		d->w->mapped = true;
		unmapwin(d->w);
    }

	foreach_column(v, s, a) {
		if(ap && ap->screen != s)
			ap = nil;

		d = getdiv(&dp);
		d->left = ap;
		d->right = a;
		div_set(d, a->r.min.x);
		ap = a;

		if(!a->next) {
			d = getdiv(&dp);
			d->left = a;
			d->right = nil;
			div_set(d, a->r.max.x);
		}
	}
}

/* Div Handlers */
static bool
bdown_event(Window *w, void *aux, XButtonEvent *e) {
	Divide *d;

	USED(e);

	d = aux;
	mouse_resizecol(d);
	return false;
}

static Handlers handlers = {
	.bdown = bdown_event,
};

