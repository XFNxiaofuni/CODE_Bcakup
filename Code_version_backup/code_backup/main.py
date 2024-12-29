import argparse
import os
import json
from backup_cli import run_backup
from restore_env import main as restore_main
from view_backup import main as view_main

# 获取当前脚本所在目录
SCRIPT_DIR = '/root/autodl-tmp/code_backup'

def parse_args():
    parser = argparse.ArgumentParser(description='代码备份工具集')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 备份命令
    backup_parser = subparsers.add_parser('backup', help='执行代码备份')
    backup_parser.add_argument('-c', '--config', 
                            default=os.path.join(SCRIPT_DIR, 'config.json'),
                            help='配置文件路径 (默认: config.json)')
    backup_parser.add_argument('-d', '--description',
                            help='备份描述 (覆盖配置文件中的描述)')
    backup_parser.add_argument('--tags', nargs='+',
                            help='备份标签 (覆盖配置文件中的标签)')
    backup_parser.add_argument('--no-compress', action='store_true',
                            help='不压缩备份文件')
    
    # 查看命令
    view_parser = subparsers.add_parser('view', help='查看备份信息')
    view_parser.add_argument('backup_dir', help='备份目录路径')
    view_parser.add_argument('--files', action='store_true', help='显示文件详情')
    
    # 恢复命令
    restore_parser = subparsers.add_parser('restore', help='恢复Python环境')
    restore_parser.add_argument('backup_dir', help='备份目录路径')
    restore_parser.add_argument('--env-name', help='要恢复的环境名称')
    
    return parser.parse_args([])  # 传入空列表，使用默认值

def main():
    args = parse_args()
    
    # 默认执行备份操作
    backup_args = {
        'config': os.path.join(SCRIPT_DIR, 'config.json'),
        'description': None,
        'tags': None,
        'no_compress': False
    }
    run_backup(backup_args)
    
    # 获取最新的备份目录
    config_path = os.path.join(SCRIPT_DIR, 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    target_dir = config['target_directory']
    
    # 获取最新的备份文件夹
    backup_dirs = [d for d in os.listdir(target_dir) 
                  if os.path.isdir(os.path.join(target_dir, d))]
    if backup_dirs:
        latest_backup = os.path.join(target_dir, max(backup_dirs))
        
        # 自动执行查看操作
        view_args = argparse.Namespace(
            backup_dir=latest_backup,
            files=True
        )
        view_main(view_args)

if __name__ == '__main__':
    main() 