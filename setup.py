from distutils.core import setup, Extension
from distutils.command.build_py import build_py as build_py_orig
import re, sys, os

# custom build_py command which runs build_ext first
# this is necessary because build_py needs the fitz.py which is only generated
# by SWIG in the build_ext step
class build_ext_first(build_py_orig):
    def run(self):
        self.run_command("build_ext")
        return super().run()


DEFAULT = [
    "mupdf",
    "mupdf-third",
]

ALPINE = DEFAULT + [
    "jbig2dec",
    "jpeg",
    "openjp2",
    "harfbuzz",
]
ARCH_LINUX = DEFAULT + [
    "jbig2dec",
    "openjp2",
    "jpeg",
    "freetype",
    "gumbo",
]
OPENSUSE = ARCH_LINUX + [
    "harfbuzz",
    "png16",
]
FEDORA = ARCH_LINUX + [
    "harfbuzz",
]
NIX = ARCH_LINUX + [
    "harfbuzz"
]
LIBRARIES = {
    "default": DEFAULT,
    "ubuntu": DEFAULT,
    "arch": ARCH_LINUX,
    "manjaro": ARCH_LINUX,
    "artix": ARCH_LINUX,
    "opensuse": OPENSUSE,
    "fedora": FEDORA,
    "alpine": ALPINE,
    "nix": NIX
}


def load_libraries():
    if os.getenv("NIX_STORE"):
        return LIBRARIES["nix"]

    try:
        import distro

        os_id = distro.id()
    except:
        os_id = ""
    if os_id in list(LIBRARIES.keys()) + ["manjaro", "artix"]:
        return LIBRARIES[os_id]

    filepath = "/etc/os-release"
    if not os.path.exists(filepath):
        return LIBRARIES["default"]
    regex = re.compile("^([\\w]+)=(?:'|\")?(.*?)(?:'|\")?$")
    with open(filepath) as os_release:
        info = {
            regex.match(line.strip()).group(1): re.sub(
                r'\\([$"\'\\`])', r"\1", regex.match(line.strip()).group(2)
            )
            for line in os_release
            if regex.match(line.strip())
        }

    os_id = info["ID"]
    if os_id.startswith("opensuse"):
        os_id = "opensuse"
    if os_id not in LIBRARIES.keys():
        return LIBRARIES["default"]
    return LIBRARIES[os_id]


# check the platform
if sys.platform.startswith("linux") or "gnu" in sys.platform:
    module = Extension(
        "fitz._fitz",  # name of the module
        ["fitz/fitz.i"],
        include_dirs=[  # we need the path of the MuPDF headers
            "/usr/include/mupdf",
            "/usr/local/include/mupdf",
            "mupdf/thirdparty/freetype/include",
            "/usr/include/freetype2",
        ],
        libraries=load_libraries(),
    )
elif sys.platform.startswith(("darwin", "freebsd", "openbsd")):
    module = Extension(
        "fitz._fitz",  # name of the module
        ["fitz/fitz.i"],
        # directories containing mupdf's header files
        include_dirs=[
            "/usr/local/include/mupdf",
            "/usr/local/include",
            "/usr/include/freetype2",
            "/usr/local/include/freetype2",
            "/usr/X11R6/include/freetype2",
            "/opt/homebrew/include",
            "/opt/homebrew/include/mupdf",
            "/opt/homebrew/include/freetype2",
        ],
        # libraries should already be linked here by brew
        library_dirs=["/usr/local/lib", "/opt/homebrew/lib"],
        # library_dirs=['/usr/local/Cellar/mupdf-tools/1.8/lib/',
        #'/usr/local/Cellar/openssl/1.0.2g/lib/',
        #'/usr/local/Cellar/jpeg/8d/lib/',
        #'/usr/local/Cellar/freetype/2.6.3/lib/',
        #'/usr/local/Cellar/jbig2dec/0.12/lib/'
        # ],
        libraries=["mupdf", "mupdf-third"],
    )

else:
    # ===============================================================================
    # Build / set up PyMuPDF under Windows
    # ===============================================================================
    module = Extension(
        "fitz._fitz",
        ["fitz/fitz.i"],
        include_dirs=[  # we need the path of the MuPDF's headers
            "./mupdf/include",
            "./mupdf/include/mupdf",
            "./mupdf/thirdparty/freetype/include",
        ],
        libraries=[  # these are needed in Windows
            "libmupdf",
            "libresources",
            "libthirdparty",
        ],
        extra_link_args=["/NODEFAULTLIB:MSVCRT"],
        # x86 dir of libmupdf.lib etc.
        library_dirs=["./mupdf/platform/win32/Release"],
        # x64 dir of libmupdf.lib etc.
        # library_dirs=['./mupdf/platform/win32/x64/Release'],
    )

pkg_tab = open("PKG-INFO", "rb").read().splitlines()
long_dtab = []  # long description lines
classifier = []  # classifier lines
for line in pkg_tab:
    line = line.decode()
    if line.startswith("Classifier: "):
        classifier.append(line[12:])
        continue
    if line.startswith(" ") or line == "":
        long_dtab.append(line.strip())
long_desc = "\n".join(long_dtab)

setup(
    name="PyMuPDF",
    version="1.18.16",
    description="Python bindings for the PDF toolkit and renderer MuPDF",
    long_description=long_desc,
    classifiers=classifier,
    url="https://github.com/pymupdf/PyMuPDF",
    author="Jorj McKie",
    author_email="jorj.x.mckie@outlook.de",
    cmdclass={"build_py": build_ext_first},
    ext_modules=[module],
    py_modules=["fitz.fitz", "fitz.utils", "fitz.__main__"],
    license="GNU AFFERO GPL 3.0",
    data_files=["README.md"],
)
