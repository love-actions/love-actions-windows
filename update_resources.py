"""Replace LÖVE's application icon and version resources before fusing the game."""

import ctypes
from ctypes import wintypes as win
from itertools import chain
import os
from pathlib import Path
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory


RT_ICON = 3
RT_GROUP_ICON = 14
RT_VERSION = 16
RESOURCE_TYPES = (RT_ICON, RT_GROUP_ICON, RT_VERSION)


def resource_entries(path):
    # An .res record contains a DWORD-aligned header followed by its payload.
    # RC emits ordinal identifiers for the icon and VERSIONINFO resources here.
    contents = Path(path).read_bytes()
    offset = 0
    while offset < len(contents):
        size, header = struct.unpack_from('<II', contents, offset)
        start = offset + header
        end = start + size
        if header < 8 or end > len(contents):
            raise ValueError(f'Invalid resource record in {path}')
        if size and header >= 32:
            type_tag, kind, name_tag, name = struct.unpack_from('<4H', contents, offset + 8)
            if type_tag == name_tag == 0xffff and kind in RESOURCE_TYPES:
                language, = struct.unpack_from('<H', contents, offset + 22)
                yield kind, name, language, contents[start:end]
        offset = (end + 3) & ~3


def sdk_resource_compiler():
    program_files_x86 = os.environ.get('ProgramFiles(x86)')
    if not program_files_x86:
        raise FileNotFoundError('ProgramFiles(x86) is not set; Windows SDK rc.exe cannot be located')
    sdk = Path(program_files_x86) / 'Windows Kits' / '10' / 'bin'
    # Search only the installed SDK tree; never trust the current directory or PATH.
    candidates = [item for item in sdk.glob('10.*/x64/rc.exe') if item.is_file()]
    if not candidates:
        raise FileNotFoundError(f'Windows SDK rc.exe not found under {sdk}')
    return max(candidates, key=lambda item: tuple(map(int, item.parent.parent.name.split('.'))))


def compile_resources(icon, version):
    if not (icon or version):
        return []
    compiler = sdk_resource_compiler()
    entries = []
    with TemporaryDirectory(prefix='love-win-resources-') as directory:
        directory = Path(directory)
        output = directory / 'resources.res'
        if icon:
            script = directory / 'icon.rc'
            filename = str(Path(icon).resolve(strict=True)).replace('\\', '\\\\')
            script.write_text(f'1 ICON "{filename}"\n', encoding='utf-8')
            subprocess.run([compiler, '/c', '65001', f'/fo{output}', script], check=True)
            icons = [entry for entry in resource_entries(output) if entry[0] in (RT_ICON, RT_GROUP_ICON)]
            if not any(item[:2] == (RT_GROUP_ICON, 1) for item in icons):
                raise ValueError(f'RC did not produce the application icon from {icon}')
            entries.extend(icons)
        if version:
            script = Path(version).resolve(strict=True)
            subprocess.run([compiler, '/c', '65001', f'/fo{output}', script], check=True)
            versions = [entry for entry in resource_entries(output) if entry[:2] == (RT_VERSION, 1)]
            if not versions:
                raise ValueError(f'RC did not produce VERSIONINFO 1 from {version}')
            entries.extend(versions)
    return entries


def update_resources(executables, replacements):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    pointer = ctypes.c_void_p
    name_callback = ctypes.WINFUNCTYPE(win.BOOL, win.HMODULE, pointer, pointer, win.LPARAM)
    lang_callback = ctypes.WINFUNCTYPE(win.BOOL, win.HMODULE, pointer, pointer, win.WORD, win.LPARAM)
    for name, result, arguments in (
        ('LoadLibraryExW', win.HMODULE, (win.LPCWSTR, win.HANDLE, win.DWORD)),
        ('FreeLibrary', win.BOOL, (win.HMODULE,)),
        ('EnumResourceNamesW', win.BOOL, (win.HMODULE, pointer, name_callback, win.LPARAM)),
        ('EnumResourceLanguagesW', win.BOOL, (win.HMODULE, pointer, pointer, lang_callback, win.LPARAM)),
        ('BeginUpdateResourceW', win.HANDLE, (win.LPCWSTR, win.BOOL)),
        ('UpdateResourceW', win.BOOL, (win.HANDLE, pointer, pointer, win.WORD, pointer, win.DWORD)),
        ('EndUpdateResourceW', win.BOOL, (win.HANDLE, win.BOOL)),
    ):
        api = getattr(kernel, name)
        api.restype, api.argtypes = result, arguments

    def existing_resources(path):
        resources = []
        enumeration_error = 0
        # Map as a data file: do not execute the x86 or x64 target.
        module = kernel.LoadLibraryExW(path, None, 0x00000002)  # LOAD_LIBRARY_AS_DATAFILE
        if not module:
            raise ctypes.WinError(ctypes.get_last_error())

        @lang_callback
        def record_language(_module, kind, name, language, _context):
            resource_name = name if name <= 0xffff else ctypes.wstring_at(name)
            resources.append((kind, resource_name, language, None))
            return True

        @name_callback
        def enum_languages(module, kind, name, _context):
            nonlocal enumeration_error
            if kernel.EnumResourceLanguagesW(module, kind, name, record_language, 0):
                return True
            enumeration_error = ctypes.get_last_error()
            return False

        try:
            # The new group references only its compiled icon IDs. Keep raw
            # icons that are not replaced, as the original action did.
            for kind in (RT_GROUP_ICON, RT_VERSION):
                ctypes.set_last_error(0)
                if not kernel.EnumResourceNamesW(module, kind, enum_languages, 0):
                    error = enumeration_error or ctypes.get_last_error()
                    if enumeration_error or error not in (1812, 1813):  # resource data or type absent
                        raise ctypes.WinError(error)
        finally:
            kernel.FreeLibrary(module)
        return resources

    for executable in executables:
        path = str(Path(executable).resolve(strict=True))
        original = existing_resources(path)
        update = kernel.BeginUpdateResourceW(path, False)  # Preserve unrelated resources.
        if not update:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            for kind, name, language, data in chain(original, replacements):
                resource_name = name if isinstance(name, int) else ctypes.c_wchar_p(name)
                payload = None if data is None else ctypes.c_char_p(data)
                size = 0 if data is None else len(data)
                if not kernel.UpdateResourceW(update, kind, resource_name, language, payload, size):
                    raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            kernel.EndUpdateResourceW(update, True)
            raise
        if not kernel.EndUpdateResourceW(update, False):
            raise ctypes.WinError(ctypes.get_last_error())
        print(f'Updated application resources in {executable}')


if __name__ == '__main__':
    update_resources(sys.argv[1:], compile_resources(os.environ.get('LOVE_ICON_PATH'), os.environ.get('LOVE_RC_PATH')))
