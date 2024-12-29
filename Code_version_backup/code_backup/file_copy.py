import os
import shutil
from datetime import datetime
import json
import hashlib
import sys
import pkg_resources
import platform
import zipfile
from pathlib import Path
import logging
from tqdm import tqdm
from functools import wraps
import time

def calculate_file_hash(file_path):
    """计算文件的 SHA-256 哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # 分块读取文件以处理大文件
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_python_env_info():
    """获取Python环境信息"""
    env_info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'platform_machine': platform.machine(),
        'platform_processor': platform.processor(),
        'python_path': sys.executable,
        'environment_variables': {
            k: v for k, v in os.environ.items() 
            if k.startswith('PYTHON') or k.startswith('PATH') or k.startswith('VIRTUAL_ENV')
        }
    }
    return env_info

def get_installed_packages(env_info_name=None):
    """
    获取已安装的Python包信息
    :param env_info_name: 指定要获取的环境名称集合
    """
    packages = []
    for pkg in pkg_resources.working_set:
        # 如果指定了环境名称，则只保存指定环境的包
        if env_info_name:
            # 检查包的路径中是否包含指定的环境名称
            if any(env_name in pkg.location.lower() for env_name in env_info_name):
                packages.append({
                    'name': pkg.key,
                    'version': pkg.version,
                    'location': pkg.location,
                    'environment': next(env_name for env_name in env_info_name 
                                     if env_name in pkg.location.lower())
                })
        else:
            packages.append({
                'name': pkg.key,
                'version': pkg.version,
                'location': pkg.location
            })
    return packages

def get_total_size(source_dir, file_types, exclude_folders):
    """计算需要备份的文件总大小"""
    total_size = 0
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in exclude_folders]
        for file in files:
            if os.path.splitext(file)[1].lower() in file_types:
                total_size += os.path.getsize(os.path.join(root, file))
    return total_size

def copy_code_files(source_dir, target_dir, description="", tags=None, exclude_folders=None, env_info_name=None):
    """
    备份代码文件
    :param env_info_name: 指定要保存的环境名称集合
    """
    # 需要备份的文件类型
    CODE_FILE_TYPES = {
        '.py',    # Python文件
        '.md',    # Markdown文件
        '.txt',   # 文本文件
        '.json',  # JSON文件
        '.yml', '.yaml',  # YAML文件
        '.js',    # JavaScript文件
        '.html',  # HTML文件
        '.css',   # CSS文件
        '.sql',   # SQL文件
        '.sh',    # Shell脚本
        '.bat',   # Batch脚本
        '.ini',   # 配置文件
        '.conf',  # 配置文件
        '.xml',   # XML文件
        '.toml',  # TOML文件
    }
    
    # 转换排除文件夹列表为集合，便于快速查找
    exclude_folders = set(exclude_folders or [])
    env_info_name = {"lcychat","openmmlab"}
    # 创建以时间命名的文件夹
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(target_dir, timestamp)
    
    # 确保备份文件夹存在
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 用于记录文件信息的字典
    backup_info = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'description': description,
        'tags': tags or [],
        'files': [],
        'statistics': {ext: 0 for ext in CODE_FILE_TYPES}
    }
    
    # 保存上一次备份的哈希值（如果存在）
    last_backup_hash = {}
    last_backup_dir = None
    
    # 查找最近的一次备份
    if os.path.exists(target_dir):
        backup_dirs = [d for d in os.listdir(target_dir) 
                      if os.path.isdir(os.path.join(target_dir, d))]
        if backup_dirs:
            last_backup_dir = max(backup_dirs)  # 获取最新的备份目录
            last_backup_json = os.path.join(target_dir, last_backup_dir, "backup_info.json")
            if os.path.exists(last_backup_json):
                with open(last_backup_json, 'r', encoding='utf-8') as f:
                    last_info = json.load(f)
                    last_backup_hash = {file['path']: file['hash'] 
                                     for file in last_info['files']}

    # 计算总大小并初始化进度条
    total_size = get_total_size(source_dir, CODE_FILE_TYPES, exclude_folders)
    copied_size = 0
    with tqdm(total=total_size, unit='B', unit_scale=True, desc="备份进度") as pbar:
        # 遍历源目录
        for root, dirs, files in os.walk(source_dir):
            # 修改 dirs 列表来排除不需要的文件夹
            dirs[:] = [d for d in dirs if d not in exclude_folders]
            
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in CODE_FILE_TYPES:
                    # 获取源文件的完整路径
                    source_file = os.path.join(root, file)
                    relative_path = os.path.relpath(source_file, source_dir)
                    
                    # 计算文件哈希值
                    file_hash = calculate_file_hash(source_file)
                    
                    # 检查文件是否变化
                    is_modified = True
                    if relative_path in last_backup_hash:
                        is_modified = last_backup_hash[relative_path] != file_hash
                    
                    # 计算目标文件路径
                    target_path = os.path.join(backup_dir, os.path.relpath(root, source_dir))
                    
                    # 确保目标路径存在
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    
                    # 复制文件
                    target_file = os.path.join(target_path, file)
                    shutil.copy2(source_file, target_file)
                    copied_size += os.path.getsize(source_file)
                    pbar.update(os.path.getsize(source_file))
                    
                    # 记录文件信息
                    file_info = {
                        'path': relative_path,
                        'type': file_ext,
                        'size': os.path.getsize(source_file),
                        'hash': file_hash,
                        'modified': datetime.fromtimestamp(os.path.getmtime(source_file)).strftime('%Y-%m-%d %H:%M:%S'),
                        'changed_since_last_backup': is_modified
                    }
                    backup_info['files'].append(file_info)
                    backup_info['statistics'][file_ext] += 1
    
    # 在备份信息中添加排除的文件夹列表
    backup_info['exclude_folders'] = list(exclude_folders)
    
    # 获取环境信息
    env_info = get_python_env_info()
    packages_info = get_installed_packages(env_info_name)
    
    # 如果没有找到指定环境的包，则记录警告信息
    if env_info_name and not packages_info:
        print(f"警告：未找到指定环境 {env_info_name} 的包信息")
    
    # 将环境信息添加到备份信息中
    backup_info['environment'] = env_info
    backup_info['packages'] = packages_info
    
    # 生成变更报告
    changes = generate_change_report(backup_info)
    summary = generate_backup_summary(backup_info, changes)
    
    # 写入摘要到MD文件开头
    with open(os.path.join(backup_dir, "backup_record.md"), 'w', encoding='utf-8') as f:
        f.write(f"# 代码备份记录\n\n")
        f.write("## 备份摘要\n\n")
        f.write(f"- 备份时间: {summary['timestamp']}\n")
        f.write(f"- 总文件数: {summary['total_files']}\n")
        f.write(f"- 总大小: {summary['total_size']/1024/1024:.2f} MB\n")
        f.write(f"- 新增文件: {summary['changes']['new_files']}\n")
        f.write(f"- 修改文件: {summary['changes']['modified_files']}\n")
        f.write(f"- 未变更文件: {summary['changes']['unchanged_files']}\n\n")
        
        # 写入Python环境信息
        f.write("\n## Python环境信息\n\n")
        f.write(f"- Python版本: {env_info['python_version'].split()[0]}\n")
        f.write(f"- 平台: {env_info['platform']}\n")
        f.write(f"- Python路径: {env_info['python_path']}\n")
        
        # 写入依赖包信息
        f.write("\n## 依赖包列表\n")
        if env_info_name:
            # 按环境分组显示包信息
            env_packages = {}
            for pkg in packages_info:
                env = pkg.get('environment', 'unknown')
                if env not in env_packages:
                    env_packages[env] = []
                env_packages[env].append(pkg)
            
            for env, pkgs in env_packages.items():
                f.write(f"\n### {env} 环境\n\n")
                for pkg in sorted(pkgs, key=lambda x: x['name']):
                    f.write(f"- {pkg['name']} == {pkg['version']}\n")
        else:
            # 如果没有指定环境，则直接显示所有包
            f.write("\n")
            for pkg in sorted(packages_info, key=lambda x: x['name']):
                f.write(f"- {pkg['name']} == {pkg['version']}\n")
        
        # 写入排除的文件夹信息
        if exclude_folders:
            f.write(f"\n## 排除的文件夹:\n")
            for folder in sorted(exclude_folders):
                f.write(f"- {folder}\n")
        
        # 写入统计信息
        f.write("\n## 文件类型统计\n\n")
        for ext, count in backup_info['statistics'].items():
            if count > 0:
                f.write(f"- {ext}: {count} 个文件\n")
        
        # 写入详细文件列表
        f.write("\n## 文件列表\n\n")
        for file_info in backup_info['files']:
            f.write(f"### {file_info['path']}\n")
            f.write(f"- 类型: {file_info['type']}\n")
            f.write(f"- 大小: {file_info['size']} 字节\n")
            f.write(f"- 修改时间: {file_info['modified']}\n")
            f.write(f"- 哈希值: {file_info['hash']}\n")
            f.write(f"- 是否变更: {'是' if file_info['changed_since_last_backup'] else '否'}\n\n")
    
    # 保存requirements.txt时也按环境分组
    if packages_info:
        if env_info_name:
            # 为每个环境创建单独的requirements文件
            env_packages = {}
            for pkg in packages_info:
                env = pkg.get('environment', 'unknown')
                if env not in env_packages:
                    env_packages[env] = []
                env_packages[env].append(pkg)
            
            for env, pkgs in env_packages.items():
                req_file = os.path.join(backup_dir, f"requirements_{env}.txt")
                with open(req_file, 'w', encoding='utf-8') as f:
                    for pkg in sorted(pkgs, key=lambda x: x['name']):
                        f.write(f"{pkg['name']}=={pkg['version']}\n")
        else:
            # 如果没有指定环境，则创建单个requirements文件
            with open(os.path.join(backup_dir, "requirements.txt"), 'w', encoding='utf-8') as f:
                for pkg in sorted(packages_info, key=lambda x: x['name']):
                    f.write(f"{pkg['name']}=={pkg['version']}\n")
    
    # 单独保存详细环境信息到JSON文件
    with open(os.path.join(backup_dir, "environment_info.json"), 'w', encoding='utf-8') as f:
        env_data = {
            'python_environment': env_info,
            'installed_packages': packages_info
        }
        json.dump(env_data, f, ensure_ascii=False, indent=2)
    
    # 保存详细信息到JSON文件
    with open(os.path.join(backup_dir, "backup_info.json"), 'w', encoding='utf-8') as f:
        json.dump(backup_info, f, ensure_ascii=False, indent=2)
        
    # 返回备份目录路径
    return backup_dir

def compress_backup(backup_dir):
    """压缩备份文件夹"""
    if not backup_dir:  # 添加检查
        raise ValueError("备份目录路径不能为空")
        
    zip_path = backup_dir + '.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(backup_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, backup_dir)
                zipf.write(file_path, arcname)
    
    return zip_path

def setup_logging(backup_dir):
    """设置日志"""
    log_file = os.path.join(backup_dir, 'backup.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def cleanup_old_backups(target_dir, keep_count=5):
    """清理旧的备份，只保留最近的几个"""
    backup_dirs = []
    for item in os.listdir(target_dir):
        item_path = os.path.join(target_dir, item)
        if os.path.isdir(item_path) or (os.path.isfile(item_path) and item.endswith('.zip')):
            backup_dirs.append(item_path)
    
    # 按修改时间排序
    backup_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # 删除多余的备份
    for old_backup in backup_dirs[keep_count:]:
        if os.path.isdir(old_backup):
            shutil.rmtree(old_backup)
        else:
            os.remove(old_backup)

def restore_backup(backup_path, restore_dir):
    """从备份恢复文件"""
    if backup_path.endswith('.zip'):
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(restore_dir)
    else:
        shutil.copytree(backup_path, restore_dir)
    
    # 从requirements文件恢复环境
    for req_file in Path(restore_dir).glob('requirements_*.txt'):
        env_name = req_file.stem.split('_')[1]
        # 这里可以添加创建虚拟环境和安装依赖的代码

def copy_with_progress(files_to_copy):
    """带进度条的文件复制"""
    with tqdm(total=len(files_to_copy), desc="复制文件") as pbar:
        for source, target in files_to_copy:
            shutil.copy2(source, target)
            pbar.update(1)

def generate_change_report(backup_info):
    """生成变更报告"""
    changes = {
        'new': [],
        'modified': [],
        'unchanged': []
    }
    
    for file_info in backup_info['files']:
        if file_info['changed_since_last_backup']:
            if not file_info.get('existed_in_last_backup'):
                changes['new'].append(file_info['path'])
            else:
                changes['modified'].append(file_info['path'])
        else:
            changes['unchanged'].append(file_info['path'])
    
    return changes

def generate_backup_summary(backup_info, changes):
    """生成备份摘要报告"""
    summary = {
        'timestamp': backup_info['timestamp'],
        'total_files': len(backup_info['files']),
        'total_size': sum(file['size'] for file in backup_info['files']),
        'changes': {
            'new_files': len(changes['new']),
            'modified_files': len(changes['modified']),
            'unchanged_files': len(changes['unchanged'])
        },
        'file_types': backup_info['statistics']
    }
    return summary

def retry_on_error(max_retries=3, delay=1):
    """装饰器：在发生错误时重试操作"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        raise
                    logging.warning(f"操作失败，{delay}秒后重试 ({retries}/{max_retries}): {str(e)}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_on_error()
def safe_copy_file(source, target):
    """安全的文件复制函数"""
    shutil.copy2(source, target)

def verify_backup(source_dir, backup_dir, backup_info):
    """验证备份的完整性"""
    verification_results = {
        'success': True,
        'errors': []
    }
    
    for file_info in backup_info['files']:
        source_file = os.path.join(source_dir, file_info['path'])
        backup_file = os.path.join(backup_dir, file_info['path'])
        
        if not os.path.exists(backup_file):
            verification_results['success'] = False
            verification_results['errors'].append(f"文件丢失: {file_info['path']}")
            continue
        
        backup_hash = calculate_file_hash(backup_file)
        if backup_hash != file_info['hash']:
            verification_results['success'] = False
            verification_results['errors'].append(f"文件校验失败: {file_info['path']}")
    
    return verification_results

def validate_config(config):
    """验证配置文件的有效性"""
    required_fields = ['source_directory', 'target_directory']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"配置文件缺少必需字段: {field}")
    
    if not os.path.exists(config['source_directory']):
        raise ValueError(f"源目录不存在: {config['source_directory']}")
    
    return True

def main(config=None):
    try:
        # 如果没有传入配置，则尝试加载配置文件
        if config is None:
            with open('config.json', 'r') as f:
                config = json.load(f)
        
        # 创建备份
        backup_dir = copy_code_files(
            config['source_directory'],
            config['target_directory'],
            description=config.get('description', ''),
            tags=config.get('tags', []),
            exclude_folders=set(config.get('exclude_folders', [])),
            env_info_name=set(config.get('env_info_name', []))
        )
        
        # 压缩备份（如果配置中启用）
        if config.get('compress_backup', False):
            zip_path = compress_backup(backup_dir)
            if not config.get('keep_original', True):
                shutil.rmtree(backup_dir)
        
        # 清理旧备份
        if config.get('cleanup_enabled', False):
            cleanup_old_backups(
                config['target_directory'],
                config.get('keep_count', 5)
            )
        
        print("备份完成！")
        
    except Exception as e:
        logging.error(f"备份过程中发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    main() 