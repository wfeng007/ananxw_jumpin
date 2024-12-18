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
import zipfile

# from os.path import join, basename, dirname, exists
# from os import walk, makedirs, sep
# from shutil import copyfile, rmtree,copytree

# from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_all


class AppBuilder:
    def __init__(self) -> None:

        ## 基本定义
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
        
        ## 分析时：
        # 指定包路径；默认增加工程目录就是最基础1个包路径
        # 在静态分析时机，即打包前指定spec的所在目录作为导入包的目录之1。应为app本身也可能是1个模块包。
        # 比如，分析时将ananxw_jumpin 作为一个包，通过init文件扫描所得
        self.scan_pkg_dirs_a_=[self.this_spec_absdir]
        # 分析阶段，指定哪些文本文件直接打包到 name_coll_
        self.libs_datas_a_ = [ 
        #        ('icon.png', '.'), ('.env', '.'), ('LICENSE', '.')
        ]
        #分析阶段，指定哪些二进制文件直接打包到 name_coll_
        self.libs_binaries_a_=[] 
        self.buildLibsBinaries()
        # 导入动态模块 / 添加打包程序找不到的模块
        # 隐含导入，用了try块静态分析并不一定执行；
        self.hiddenimports_a_ = [ 
            'ananxw_jumpin.builtin_plugins',  # 似乎加不加无关。 只要pathex 有设定就行。
            'pydantic.deprecated.decorator'
        ] 
        self.addChromadbDependences() #专门处理chroma的隐含导入
        self.excludes_a_ = ['PyQt5'] # 不需要导入的包

        ## 分析后打包前:
        self.filter_after_analysis = [ #  需要分析引用，但不需要打包的文件
            'chromadb' # chromadb之后会直接整体拷贝到libs目录中，使用原始py状态的库
        ] 

        ## 打包时:
        self.libs_contents_dirname_exe_='_libs'
        self.icon_exe_ = [] # 图标路径
        self.console_exe_ = True # 是否显示命令行窗口
        
        ## 打包发布后：
        #
        # 生成发布（dist）后要直接拷贝的目录、文件内容
        #
        self.copy2workdir_files = [ # 额外所需复制的文件
            'icon.png','.env','LICENSE','NOTICE','requirements.txt'
        ] 
        self.copy2workdir_folders = [ # 额外所需复制的目录
            'memories','_libs_ext'
        ] 
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

        # 先解压Chroma()
        self.unzipChromadb()

        # 拷贝文件到打包所在目录（_interal同级 coll.name下,这里使用预设的name_coll_）
        # 这里应该是从当前文件触发计算的，所以加上了dist
        dest_root = os.path.join('dist', os.path.basename(self.name_coll_))
        print(f'copyFilesAndFoldersToWorkdir, dest_root:{dest_root}')
        AppBuilder.copyFolders(self.copy2workdir_folders,dest_root)
        AppBuilder.copyFiles(self.copy2workdir_files,dest_root)

        ###
        # chroma无法很好的静态分析后打包，这里直接整体复制到打包后的libs目录下。
        # 已处理chroma作为py库直接运行时载入，而不是静态分析打包。
        # TODO 之后考虑直接用_libs_ext作为运行时的另外1个模块、包导入扫描目录。
        # TODO 增加zip解压，工程中默认压缩后上传git工程库
        ###
        self.copyChromadb()


    def unzipChromadb(self):
         AppBuilder.unzipFiles(['_libs_ext\\chromadb_0.5.23.zip'],'_libs_ext\\')

    # chromadb处理
    def copyChromadb(self):
        #直接用复制方式复制到 libs下
        dest_root = os.path.join('dist', os.path.basename(self.name_coll_),os.path.basename(self.libs_contents_dirname_exe_))
        AppBuilder.copyFolders(
            ['_libs_ext\\chromadb','_libs_ext\\chromadb-0.5.23.dist-info']
            ,dest_root
        )

    def addChromadbDependences(self):
         # langchain,  embedding模型需要 尤其用ada2,进行文档灌库时
        self.hiddenimports_a_.append("tiktoken.registry") 
        self.hiddenimports_a_.append("tiktoken_ext.openai_public") # embedding模型需要 尤其用ada2
        self.hiddenimports_a_.append("tiktoken_ext") # embedding模型需要 尤其用ada2

        self.hiddenimports_a_.append("chromadb.telemetry.product.posthog")
        self.hiddenimports_a_.append("chromadb.api.segment")
        self.hiddenimports_a_.append("chromadb.db.impl")
        self.hiddenimports_a_.append("chromadb.db.impl.sqlite")
        self.hiddenimports_a_.append("chromadb.segment.impl.manager.local")
        self.hiddenimports_a_.append("chromadb.execution.executor.local")
        self.hiddenimports_a_.append("chromadb.quota.simple_quota_enforcer")
        self.hiddenimports_a_.append("chromadb.rate_limit.simple_rate_limit")
        self.hiddenimports_a_.append("chromadb.segment.impl.metadata")
       
 


    def filterAnalysis(self,a:'Analysis'):
        pure = a.pure.copy()
        a.pure.clear()
        for name, src, type in pure:
            condition = [name == m or name.startswith(m + '.') for m in self.filter_after_analysis]
            if condition and any(condition):
                print(f"打包前，已过滤模块/包: {name} ")
                ...
            else:
                a.pure.append((name, src, type))    # 把需要保留打包的 py 文件重新添加回 a.pure

    @classmethod
    def unzipFiles(cls, src_files: list[str], dest_dir: str):
        
        for zip_file in src_files:
            try:
                print(f"准备解压文件 {zip_file} 到 {dest_dir}。")
                if not os.path.exists(zip_file):
                    print(f"warning:源文件 {zip_file} 不存在，跳过。")
                    continue
                
                # 创建目标目录（如果不存在）
                os.makedirs(dest_dir, exist_ok=True)
                
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:

                    # 仅遍历 ZIP 文件中的第一层文件和目录目标位置已有则删除。
                    for member in zip_ref.namelist():
                        # print(f"遍历zip中...存在内容: {member}。")
                        # 只处理第一层目录与文件；
                        if member.count('/') == 0 or (member.count('/') == 1 and member.endswith('/')):  
                            member_path = os.path.join(dest_dir, member)
                            
                            # 如果目标文件已存在，先删除
                            if os.path.exists(member_path):
                                if os.path.isdir(member_path):
                                    shutil.rmtree(member_path)  # 删除目录
                                else:
                                    os.remove(member_path)  # 删除文件
                                print(f"已删除已存在的文件或目录 {member_path}。")
                            
                    # 解压文件到目标目录
                    zip_ref.extractall(dest_dir)
                    print(f"已将文件 {zip_file} 解压到 {dest_dir}。")
            except Exception as e:
                print(f"解压文件 {zip_file} 到 {dest_dir} 时发生错误: {e}")

    @classmethod
    def copyFolders(cls, src_folders: list[str], dest_dir: str):
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
    def copyFiles(cls, files: list[str], dest_dir: str ):
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

# 过滤分析结果
appBuilder.filterAnalysis(a)

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

