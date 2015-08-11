/* Copyright ©2007-2010 Kris Maglione <maglione.k at Gmail>
 * See LICENSE file for license details.
 */
#include "../x11.h"

void
moveresizewin(Window *w, Rectangle r) {
	assert(w->type == WWindow);
	XMoveResizeWindow(display, w->xid, r.min.x, r.min.y, Dx(r), Dy(r));
	w->r = r;
}
