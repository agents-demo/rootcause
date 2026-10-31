# LAIX handoff (superseded)

This file recorded the earlier plan to copy `server/rootcause/laix/` into LAIX. That plan is complete
and no longer describes the code.

LAIX is now installed as a pinned dependency (`laix @ git+https://github.com/michaelatamuk/laix.git@v0.2.1#subdirectory=python/laix`).
The quality intervention policy lives in `server/rootcause/quality/` as a LAIX policy plugin, and the
local `server/rootcause/laix/` package has been removed.

See [docs/laix-module.md](docs/laix-module.md) for the architecture, adapter boundary, upgrade and
rollback instructions.
