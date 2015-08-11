/* Copyright ©2007-2010 Kris Maglione <maglione.k at Gmail>
 * See LICENSE file for license details.
 */
#include "../x11.h"

int
mapraisewin(Window *w) {
	assert(w->type == WWindow);
	XMapRaised(display, w->xid);
	w->mapped = 1;
	return 1;
}
