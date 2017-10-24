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
	r = Rect(x-1, selview->r[scrn].min.y, x+1, selview->r[scrn].max.y);

	moveresizewin(d->w, r);
	mapraisewin(d->w);
}

void div_map(bool map) {
	Divide *d;
	int (*mapfunc)(Window*);

	if (map)
		mapfunc = &mapwin;
	else
		mapfunc = &unmapwin;

	for(d = divs; d != divend; d = d->next) {
		/* Force map/unmap by letting it think it has the opposite state */
		d->w->unmapped = map;
		d->w->mapped = !map;
		(*mapfunc)(d->w);
	}
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

	div_map(false);

	foreach_column(v, s, a) {
		if(ap && ap->screen != s)
			ap = nil;

		if(!a->next || a->next->screen != s)
			continue;

		d = getdiv(&dp);
		d->left = a;
		d->right = a->next;
		div_set(d, a->r.max.x);
		ap = a;
	}

	divend = *dp;
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

