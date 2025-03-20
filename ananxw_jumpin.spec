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
        self.entrance_scripts_a_=['main.py']  # 使用新的入口点
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
        return os.path.dirname(os.path.abspath(spec_file_path))
    
    def buildLibsBinaries(self):
        # 某种动态库，比如dll
        """
        # 分析阶段，指定哪些二进制文件直接打包到 binary_dir
        # 读取当前系统的exe路径
        sys_exe_path = os.path.dirname(sys.executable)
        # ffmpeg.exe 的绝对路径
        ffmpeg_path = os.path.join(sys_exe_path, 'ffmpeg.exe')
        self.libs_binaries_a_=[
            (ffmpeg_path, '.'),
        ]

        # 注意PyInstaller 提取的路径列表：
        # binaries 中的路径中第一个参数为绝对路径；第二个参数（，后的路径）为相对meipass的位置，也即相对exe的位置
        # datas 也是同样的规则
        """
        pass

    def addChromadbDependences(self):
        """添加chromadb的隐性依赖包"""
        # add: ['chromadb'] to hiddenimports
        self.hiddenimports_a_.extend([
            'chromadb',
            'multipart',
            'chromadb.segment',
            'chromadb.segment.impl.metadata',
            'chromadb.segment.impl.vector',
            'chromadb.segment.impl.mulitivector',
            'chromadb.segment.impl.manager',
            'chromadb.types.embeddings.batched',
            'chromadb.config'
        ])
        
# 因此已打包的app运行时无法 import 还是需要拷贝源码
def copyDirectoryContent(srcDir, dstDir):
    """
    复制文件夹及其所有内容到目标目录
    """
    if not os.path.exists(dstDir):
        os.makedirs(dstDir, exist_ok=True)
    
    for item in os.listdir(srcDir):
        spath = os.path.join(srcDir, item)
        dpath = os.path.join(dstDir, item)
        
        if os.path.isdir(spath):
            copyDirectoryContent(spath, dpath)
        else:
            if not os.path.exists(os.path.dirname(dpath)):
                os.makedirs(os.path.dirname(dpath), exist_ok=True)
            shutil.copy2(spath, dpath)
    
# 核心编译与打包机制
def analysis_to_spec(appBuilder:AppBuilder):
    """分析编译应用主要入口文件，确定依赖目录与文件，生成相应的spec设置，返回Analysis实例
    
    包括：编译、分析依赖、拷贝代码文件（binary）、数据文件、生成.spec

    Arguments:
    appBuilder -- 应用打包配置
    mainName -- 主要入口文件，带py文件扩展名
    moduleName -- 应用模块名

    Returns:
    3个值的Tuple：a-Analysis，pyz-PYZ，exe-EXE
    """
    from PyInstaller.building.api import (
            PYZ, EXE, COLLECT, BUNDLE, MERGE, Analysis)
    #导入这些内容后才能生成.spec
    
    # 应用基本定义与配置
    # entrance_scripts=appBuilder.entrance_scripts_a_
    main_path=appBuilder.entrance_scripts_a_[0]
    module_name=appBuilder.moduleName
    
    
    # 确定包与全依赖关系、分析、创建 Analysis 实例
    a = Analysis(
        appBuilder.entrance_scripts_a_, # 分析的主入口模块，一般为main.py；可多个，如test1.py test2.py
        pathex=appBuilder.scan_pkg_dirs_a_, # 导入路径列表，即在哪些路径下查找模块和包
        datas=appBuilder.libs_datas_a_, # 需要包含的额外文件或文件夹 [(src, dst)]
        binaries=appBuilder.libs_binaries_a_, # 需要包含的二进制文件 [(src, dst)]
        hiddenimports=appBuilder.hiddenimports_a_, # 隐式导入的模块列表，这些模块无法通过静态分析检测到，或者那些导入时包含在try块中的模块
        excludes=appBuilder.excludes_a_, # 排除的模块列表
        noarchive=False, # 是否不将Python字节码压缩到zipfile中
    )
    
    #过滤掉这些模块的 binary 和 data 文件，即不含打包它们的二进制文件和数据文件
    a.binaries = TOC([x for x in a.binaries if x[0].split('/')[0] not in appBuilder.filter_after_analysis])
    a.datas = TOC([x for x in a.datas if x[0].split('/')[0] not in appBuilder.filter_after_analysis])

    # 创建PYZ对象（Python Zipfile）
    pyz = PYZ(a.pure, a.zipped_data, cipher=None)
    
    # 创建EXE对象（可执行文件）
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,  # 不将二进制文件和数据文件打包到exe中
        name=appBuilder.name_exe_, #exe主文件命名
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=appBuilder.console_exe_,
        # icon=appBuilder.icon_exe_,
    )
    
    # 返回a、pyz、exe
    return a, pyz, exe


def collect_to_bundle(appBuilder:AppBuilder, a_analysis, pyz, exe):
    """收集所有构建的组件并捆绑为dist目录
    
    注意，此处设定了最终收集目标的目录名为 appName，作为App的目录名.
    注意，如果执行非exe，比如main.py，直接运行，最终目录是在 dist/main下.
    注意，使用pyinstaller命令时，最终打包出的目录名是和spec文件名一致的.
    """
    
    # 最终收集所有文件到COLLECT对象，也即dist目录
    coll = COLLECT(
        exe,
        a_analysis.binaries,
        a_analysis.zipfiles,
        a_analysis.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=appBuilder.name_coll_, # 收集目标目录名为: dist/name_coll_
    )
    return coll

# 补充操作
def post_build_clean_workdir(appBuilder:AppBuilder, distDir:str, target_lib_dirname:str or None=None):
    """打包后收尾工作 
    """
    print("Post build to workdir:"+distDir)
    # print(type(distDir))
    
    if not target_lib_dirname:
        target_lib_dirname=appBuilder.libs_contents_dirname_exe_
    
    # 拷贝文件
    for file_name in appBuilder.copy2workdir_files:
        # full_path = os.path.join(app_builder.this_spec_absdir, file_name)
        file_path_param = file_name #os.path.join(app_builder.root_dir, file_name)
        # 处理.env情况：如果不存在就生成一个
        if ".env" in file_path_param and not os.path.exists(file_path_param):
            print("No .env")
            #如果不存在，暂时不生成
        else:
            if os.path.exists(file_path_param):
                shutil.copy(file_path_param, os.path.join(distDir, os.path.basename(file_path_param)))
                print("Copy file: "+file_path_param + " to workdir.")
            else:
                print("File not found: "+ file_path_param)
    
    # 拷贝目录
    for folder_name in appBuilder.copy2workdir_folders:
        full_folder = folder_name
        if os.path.exists(full_folder) and os.path.isdir(full_folder):
            dest_folder = os.path.join(distDir, os.path.basename(folder_name))
            if os.path.exists(dest_folder):
                shutil.rmtree(dest_folder)
            shutil.copytree(full_folder, dest_folder)
            print("Copy folder: "+folder_name + " to workdir.")
        else:
            print("Folder not found or not a directory: "+ folder_name)
    
    try:
        src_site_pkgs=os.path.join(os.path.dirname(sys.executable),
                                   "Lib","site-packages","chromadb")
        dest_chromadb=os.path.join(distDir,"_libs","chromadb")
        try:
            if os.path.exists(dest_chromadb):
                shutil.rmtree(dest_chromadb)
        except Exception as e:
            print(f"Failed to delete existing chromadb folder: {e}")
        
        if os.path.exists(src_site_pkgs):
            copyDirectoryContent(src_site_pkgs, dest_chromadb)
            print(f"Copy folder: {src_site_pkgs} -> {dest_chromadb}.")
        else:
            print(f"Source folder not found: {src_site_pkgs}")
    except Exception as e:
        print(f"Failed to copy chromadb: {e}")

def zip_workdir(source_dir,target_zip_name=None):
    """打包为zip文件
    """
    if target_zip_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_zip_name = f"{os.path.basename(source_dir)}_{timestamp}.zip"

    # 创建zip文件
    with zipfile.ZipFile(target_zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历源目录下的所有文件
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # 计算相对路径，作为zip内的路径
                arcname = os.path.relpath(file_path, source_dir)
                # 添加文件到zip
                zipf.write(file_path, arcname)
    
    print(f"Created zip file: {target_zip_name}")
    return target_zip_name

# 主要构建逻辑
def build_main():
    '''
    主调用位置，执行完整的编译打包流程：
    '''
    abder = AppBuilder()
    a, pyz, exe = analysis_to_spec(abder)
    coll = collect_to_bundle(abder, a, pyz, exe)

    # 额外拷贝文件到打包目录 dist/abder.name_coll_，已在collect_to_bundle确定了目录。
    distDir = os.path.join('dist', abder.name_coll_)
    post_build_clean_workdir(abder,distDir)
    return distDir


#全局构造块
def block0():
    '''
    全局块
    '''
    from PyInstaller.building.api import COLLECT, TOC
    return Analysis, TOC

#全局构造块，固定引用以便全局变量正确初始化
Analysis, TOC = block0()

#打包命令
if __name__ == '__main__':
    # 通过pyinstaller命令行打包，得到正经的spec、并执行main块中的打包build过程。
    build_main() 