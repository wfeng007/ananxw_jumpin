# -*- mode: python ; coding: utf-8 -*-
## License and Notice:
# This file is part of ananxw_jumpin.
# ananxw_jumpin is licensed under the Apache2.0(the License); you may not use 
# this file except in compliance with the License. See LICENSE file for details.
# For the full license text, see the LICENSE file in the root directory.
# 
# For more copyright, warranty disclaimer, and third - party component information,
# see the NOTICE file in the root directory.
##
#
# @Author:wfeng007 小王同学 wfeng007@163.com
# @Date:2024-12-3 
# @Last Modified by:wfeng007
#
##
# 
# pyinstaller 打包app的配置与脚本
#

import os,sys,shutil

# from os.path import join, basename, dirname, exists
# from os import walk, makedirs, sep
# from shutil import copyfile, rmtree,copytree

# from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_all


class AppBuilder:
    def __init__(self) -> None:
        # 自定义应用名
        self.appName="ananxw_jumpin"
        # 本文件绝对路径
        self.this_spec_absdir=self.thisSpecAbsDir()
        #
        self.moduleName=self.appName
        self.entrance_scripts_a_=['ananxw_jumpin_allin1f.py']
        # 打包生成exe的文件名称
        self.name_exe_=self.appName
        # 打包生成根目录名称文件名称
        self.name_coll_=self.moduleName
        
        
        # 指定包路径；默认增加1当前目录，即工程目录就是最基础1个包路径
        # 在静态分析时机，即打包前指定spec的所在目录作为导入包的目录之1。应为app本身也可能是1个模块包。
        # 比如，分析时将ananxw_jumpin 作为一个包，通过init文件扫描所得
        self.scan_pkg_dirs_a_=[self.this_spec_absdir]
        # 分析阶段，指定哪些文本文件直接打包到 name_coll_
        self.libs_datas_a_ = [
        #        ('icon.png', '.'), ('.env', '.'), ('LICENSE', '.')
        ]
        # 分析阶段，指定哪些二进制文件直接打包到 name_coll_
        self.libs_binaries_a_=[]
        self.buildLibsBinaries()

        self.hiddenimports_a_ = [
            'posthog', #chromadb 需要
            'ananxw_jumpin.builtin_plugins',
            'pydantic.deprecated.decorator'
        ] # 导入动态模块 / 添加打包程序找不到的模块
        self.excludes_a_ = ['PyQt5'] # 不需要导入的包


        self.libs_contents_dirname_exe_='_libs'
        self.icon_exe_ = [] # 图标路径
        self.console_exe_ = True # 是否显示命令行窗口
        self.private_module = [ ] #  不需要打包的文件


        # 生成发布（dist）后要直接拷贝的目录、文件内容
        #
        self.copy2workdir_files = ['icon.png','.env','LICENSE','NOTICE','requirements.txt'] # 额外所需文件
        self.copy2workdir_folders = ['memories','_libs_ext'] # 额外所需目录
        # 

        pass

    def thisSpecAbsDir(self):
        # spec 不能直接用__file__
        # 可以用参数文件获取路径：current_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        # 或 current_path = os.path.abspath('.')
        spec_file_path = sys.argv[0]
        # 使用spec当前目作为 分析导入包的基础目录之一
        #  1 根据spec与pkg的相对位置得到包目录，如 current_path=os.path.dirname(os.path.abspath(__file__))
        #  2 可以拼接出子包 os.path.join(current_path, 'sub_pkg')
        this_spec_absdir = os.path.dirname(os.path.abspath(spec_file_path))
        print(f'this_spec_absdir: {this_spec_absdir}')
        return this_spec_absdir
    
    # 额外复制 dll 应该是用来动态导入模块
    def buildLibsBinaries(self):
        # 本应用 onnx可能用处不大？
        modules = ['onnxruntime']
        for module in modules: 
            tmp_ret = collect_all(module)
            self.libs_binaries_a_ += tmp_ret[1]
        
        ...


    def copyFilesAndFoldersToWorkdir(self):
        # 拷贝文件到打包所在目录（_interal同级 coll.name下,这里使用预设的name_coll_）
        # 这里应该是从当前文件触发计算的，所以加上了dist
        dest_root = os.path.join('dist', os.path.basename(self.name_coll_))
        print(f'copyFilesAndFoldersToWorkdir, dest_root:{dest_root}')
        AppBuilder.copyFoldersTo(self.copy2workdir_folders,dest_root)
        AppBuilder.copyFilesTo(self.copy2workdir_files,dest_root)

        ###
        # chroma无法很好的静态分析后打包，这里直接整体复制到打包后的libs目录下。
        # 已处理chroma作为py库直接运行时载入，而不是静态分析打包。
        # TODO 之后考虑直接用_libs_ext作为运行时的另外1个模块、包导入扫描目录。
        # TODO 增加zip解压，工程中默认压缩后上传git工程库
        ###
        self.copyChromadb()

    def copyChromadb(self):
        #直接用复制方式复制到 libs下
        dest_root = os.path.join('dist', os.path.basename(self.name_coll_),os.path.basename(self.libs_contents_dirname_exe_))
        AppBuilder.copyFoldersTo(
            ['_libs_ext\\chromadb','_libs_ext\\chromadb-0.5.23.dist-info']
            ,dest_root
        )


    @classmethod
    def copyFoldersTo(cls, src_folders: list[str], dest_dir: str):
        for folder in src_folders:
            try:
                dest_folder = os.path.join(dest_dir, os.path.basename(folder))  # 保留文件夹名称
                print(f"准备复制文件夹{folder} 到 {dest_folder}。")
                if os.path.exists(dest_folder):
                    shutil.rmtree(dest_folder)  # 如果目标文件夹已存在，先删除
                    print(f"已删除已存在的文件夹 {dest_folder}。")
                if not os.path.exists(folder):
                    print(f"warning:源文件夹 {folder} 不存在，跳过。")
                    continue
                shutil.copytree(folder, dest_folder)  # 使用shutil.copytree进行深层拷贝
                print(f"已将源文件夹 {folder} 复制到 {dest_folder}。")
            except Exception as e:
                print(f"复制文件夹 {folder} 到 {dest_folder} 时发生错误: {e}")
    


    @classmethod
    def copyFilesTo(cls, files: list[str], dest_dir: str ):
        for file in files:
            try:
                print(f"准备复制文件{file} 到 {dest_dir}。")
                if not os.path.exists(file):
                    print(f"warning:源文件 {file} 不存在，跳过。")
                    continue
                dest_file = os.path.join(dest_dir, os.path.basename(file))
                dest_folder = os.path.dirname(dest_file)
                os.makedirs(dest_folder, exist_ok=True)
                shutil.copyfile(file, dest_file)
                print(f"已将源文件 {file} 复制到 {dest_file}。")
            except Exception as e:
                print(f"复制文件夹 {file} 到 {dest_folder} 时发生错误: {e}")
    
    ...

# 打包设定与工具
appBuilder=AppBuilder()


a = Analysis(
    appBuilder.entrance_scripts_a_,
    pathex=appBuilder.scan_pkg_dirs_a_,
    binaries=appBuilder.libs_binaries_a_,
    datas=appBuilder.libs_datas_a_,
    hiddenimports=appBuilder.hiddenimports_a_,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=appBuilder.excludes_a_,
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
    name=appBuilder.name_exe_,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=appBuilder.console_exe_,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=appBuilder.icon_exe_,
    #这个对应 --contents-directory 参数指定. 可以修改_interal目录为指定目录比如.。
    contents_directory=appBuilder.libs_contents_dirname_exe_,  
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=appBuilder.name_coll_,
)

appBuilder.copyFilesAndFoldersToWorkdir()

