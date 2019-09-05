AC_INIT([enigma2-2boom-plugins],[1.0])
AM_INIT_AUTOMAKE([dist-bzip2 foreign no-define tar-pax])
AC_CONFIG_HEADERS([enigma2-plugins-config.h])

# Silent rules are available since 1.11, but older versions
# are still in use. So don't use them unconditionally.
m4_ifdef([AM_SILENT_RULES], [AM_SILENT_RULES([yes])])

AC_USE_SYSTEM_EXTENSIONS
AC_SYS_LARGEFILE

AC_PROG_CC
AC_PROG_CXX
m4_ifdef([LT_INIT], [LT_INIT], [AC_PROG_LIBTOOL])
AC_CONFIG_MACRO_DIR([m4])

AC_CHECK_HEADERS([dbox/fp.h dbox/lcd-ks0713.h])

AC_PATH_PROG(MSGFMT, msgfmt, AC_MSG_ERROR(Could not find msgfmt))
AC_PATH_PROG(MSGINIT, msginit, AC_MSG_ERROR(Could not find msginit))
AC_PATH_PROG(MSGMERGE, msgmerge, AC_MSG_ERROR(Could not find msgmerge))
AC_PATH_PROG(MSGUNIQ, msguniq, AC_MSG_ERROR(Could not find msguniq))
AC_PATH_PROG(XGETTEXT, xgettext, AC_MSG_ERROR(Could not find xgettext))

AM_PATH_PYTHON
AX_PYTHON_DEVEL
AX_PTHREAD

AC_ARG_WITH(arch,
	[  --with-arch=NAME box arch [[none,ah4,mipsel...]]],
	[ARCH="$withval"],[ARCH="mipsel"])
AC_SUBST(ARCH)
AC_DEFINE_UNQUOTED(ARCH,"$ARCH",[box arch])

AM_CONDITIONAL(SH4, test `echo "$ARCH" | cut -b 1-3` == "sh4")
AM_CONDITIONAL(MIPSEL, test `echo "$ARCH" | cut -b 1-6` == "mipsel")
AM_CONDITIONAL(ARM, test `echo "$ARCH" | cut -b 1-3` == "arm")

AC_ARG_WITH(boxtype,
	[  --with-boxtype=NAME box type [[none,dm800...]]],
	[BOXTYPE="$withval"],[BOXTYPE="dm800"])
AC_SUBST(BOXTYPE)
AC_DEFINE_UNQUOTED(BOXTYPE,"$BOXTYPE",[box type])

AC_ARG_WITH(boxbrand,
	[  --with-boxbrand=NAME box brand [[none,dreambox...]]],
	[BOXBRAND="$withval"],[BOXBRAND="dreambox"])
AC_SUBST(BOXBRAND)
AC_DEFINE_UNQUOTED(BOXBRAND,"$BOXBRAND",[box brand])

AC_CONFIG_FILES([
Makefile

ARbouquet/Makefile
ARbouquet/po/Makefile
ARbouquet/src/Makefile
ARbouquet/src/images/Makefile

ECCcam/Makefile
ECCcam/po/Makefile
ECCcam/src/Makefile
ECCcam/src/images/Makefile

epanel/Makefile
epanel/po/Makefile
epanel/script/Makefile
epanel/src/Makefile
epanel/src/images/Makefile

epgdd/Makefile
epgdd/po/Makefile
epgdd/src/Makefile
epgdd/src/images/Makefile

ipktools/Makefile
ipktools/po/Makefile
ipktools/src/Makefile
ipktools/src/images/Makefile

LTV/Makefile
LTV/po/Makefile
LTV/src/Makefile

m2b/Makefile
m2b/po/Makefile
m2b/src/Makefile
m2b/src/images/Makefile

QCIfH/Makefile
QCIfH/po/Makefile
QCIfH/src/Makefile
QCIfH/src/images/Makefile

QEIfH/Makefile
QEIfH/po/Makefile
QEIfH/src/Makefile

QERfH/Makefile
QERfH/po/Makefile
QERfH/src/Makefile

QuickEcmInfo/Makefile
QuickEcmInfo/e2/Makefile
QuickEcmInfo/po/Makefile
QuickEcmInfo/src/Makefile
QuickEcmInfo/src/images/Makefile

QuickEmuRestart/Makefile
QuickEmuRestart/po/Makefile
QuickEmuRestart/src/Makefile
QuickEmuRestart/src/images/Makefile

ReloadSL/Makefile
ReloadSL/po/Makefile
ReloadSL/src/Makefile

ReMountNetShare/Makefile
ReMountNetShare/po/Makefile
ReMountNetShare/src/Makefile
ReMountNetShare/src/images/Makefile

RPUlite/Makefile
RPUlite/po/Makefile
RPUlite/src/Makefile
RPUlite/src/images/Makefile

TPUlite/Makefile
TPUlite/po/Makefile
TPUlite/src/Makefile
TPUlite/src/images/Makefile

UpdatePreview/Makefile
UpdatePreview/e2/Makefile
UpdatePreview/po/Makefile
UpdatePreview/src/Makefile
UpdatePreview/src/images/Makefile

YWeather/Makefile
YWeather/po/Makefile
YWeather/src/Makefile
YWeather/src/images/Makefile
YWeather/src/istyle/Makefile
YWeather/src/istyle/istyle1/Makefile

YWfH/Makefile
YWfH/po/Makefile
YWfH/src/Makefile
YWfH/src/images/Makefile
YWfH/src/istyle/Makefile
YWfH/src/istyle/istyle1/Makefile

])
AC_OUTPUT
