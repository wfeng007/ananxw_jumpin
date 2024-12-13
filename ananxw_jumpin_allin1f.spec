# -*- mode: python ; coding: utf-8 -*-

import os,sys
from os.path import join, basename, dirname, exists
from os import walk, makedirs, sep
from shutil import copyfile, rmtree,copytree

# from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_all


copy2workdir_files = ['icon.png','.env','LICENSE','NOTICE'] # 额外所需文件
copy2workdir_folders = ['memories'] # 复制文件夹中所有文件
# TODO 需要处理一下 chroma 作为py库运行时载入，而不是静态分析打包。
libs_contents_dirname_exe_='_libs'
libs_datas_a_ = [
#        ('icon.png', '.'), ('.env', '.'), ('LICENSE', '.')
]
hiddenimports_a_ = [
    'ananxw_jumpin.builtin_plugins',
    'pydantic.deprecated.decorator'
] # 导入动态模块 / 添加打包程序找不到的模块
excludes_a_ = ['PyQt5'] # 不需要导入的包
icon_exe_ = [] # 图标路径
console_exe_ = True # 是否显示命令行窗口
private_module = [ ] # TODO 不需要打包的文件

# 额外二进制库
binaries=[]

# 额外复制 dll 应该是用来动态导入模块
modules = ['onnxruntime']
for module in modules: 
    tmp_ret = collect_all(module)
    binaries += tmp_ret[1]


# spec 不能直接用__file__
# 可以用参数文件获取路径：current_path = os.path.dirname(os.path.abspath(sys.argv[0]))
# 或 current_path = os.path.abspath('.')
spec_file_path = sys.argv[0]

# 使用spec当前目作为 分析导入包的基础目录之一
#  1 根据spec与pkg的相对位置得到包目录，如 current_path=os.path.dirname(os.path.abspath(__file__))
#  2 可以拼接出子包 os.path.join(current_path, 'sub_pkg')
current_path = os.path.dirname(os.path.abspath(spec_file_path))
print(f'current_path: {current_path}')
# 指定包路径，这里当前目录，即工程目录就是最基础1个包路径
pkg_dirs=[current_path]

a = Analysis(
    ['ananxw_jumpin_allin1f.py'],
    pathex=pkg_dirs,
    binaries=binaries,
    datas=lib_datas_a_,
    hiddenimports=hiddenimports_a_,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes_a_,
    noarchive=False,
    optimize=0,
    # init_hook='import ananxw_jumpin.__init__',
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ananxw_jumpin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=console_exe_,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_exe_,
    #这个对应 --contents-directory 参数指定. 可以修改_interal目录为指定目录比如.。
    contents_directory=libs_contents_dirname_exe_,  
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ananxw_jumpin',
)


# 拷贝文件到打包所在目录（_interal同级 coll.name）
dest_root = join('dist', basename(coll.name))
for folder in copy2workdir_folders:
    for dirpath, dirnames, filenames in walk(folder):
        for filename in filenames:
            copy2workdir_files.append(join(dirpath, filename))

for file in copy2workdir_files:
    if not exists(file):
        continue
    dest_file = join(dest_root, file)
    dest_folder = dirname(dest_file)
    makedirs(dest_folder, exist_ok=True)
    copyfile(file, dest_file)

# TODO 改为整体目录复制
# # 源目录路径
# src_dir = "source_directory"
# # 目标目录路径
# dst_dir = "destination_directory"
# try:
#     shutil.copytree(src_dir, dst_dir)
#     print("目录复制成功。")
# except FileExistsError:
#     print("目标目录已存在。")
# except Exception as e:
#     print(f"复制目录时出错: {e}")