# Shared by the launcher and packaged-runtime verification. APPDIR must be set.
export PYTHONHOME="$APPDIR/usr"
export PYTHONPATH="$APPDIR/usr/lib/python3/dist-packages:$APPDIR/usr/share/btd700-control"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export LD_LIBRARY_PATH="$APPDIR/usr/lib/x86_64-linux-gnu:$APPDIR/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export GDK_PIXBUF_MODULE_FILE="$APPDIR/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders.cache"
export GI_TYPELIB_PATH="$APPDIR/usr/lib/x86_64-linux-gnu/girepository-1.0"
export GSETTINGS_SCHEMA_DIR="$APPDIR/usr/share/glib-2.0/schemas"
export XDG_DATA_DIRS="$APPDIR/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
export FONTCONFIG_FILE="$APPDIR/etc/fonts/fonts.conf"
export FONTCONFIG_PATH="$APPDIR/etc/fonts"
# A control panel does not need GPU rendering or host-specific Mesa drivers.
export GSK_RENDERER=${GSK_RENDERER:-cairo}
